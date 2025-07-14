terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
  
  backend "s3" {
    bucket         = "mas-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "mas-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "mas-system"
      ManagedBy   = "terraform"
    }
  }
}

# VPC Configuration
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr
  
  azs              = data.aws_availability_zones.available.names
  private_subnets  = var.private_subnet_cidrs
  public_subnets   = var.public_subnet_cidrs
  database_subnets = var.database_subnet_cidrs
  
  enable_nat_gateway   = true
  single_nat_gateway   = var.environment != "prod"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true
  
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = "${var.project_name}-eks"
  cluster_version = var.kubernetes_version
  
  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets
  
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true
  
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }
  
  eks_managed_node_groups = {
    general = {
      min_size     = var.node_group_min_size
      max_size     = var.node_group_max_size
      desired_size = var.node_group_desired_size
      
      instance_types = var.node_instance_types
      
      k8s_labels = {
        Environment = var.environment
        NodeGroup   = "general"
      }
    }
    
    compute = {
      min_size     = 1
      max_size     = 10
      desired_size = 2
      
      instance_types = ["c5.2xlarge", "c5.4xlarge"]
      
      k8s_labels = {
        Environment = var.environment
        NodeGroup   = "compute"
        Workload    = "cpu-intensive"
      }
      
      taints = [
        {
          key    = "compute"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]
    }
  }
  
  manage_aws_auth_configmap = true
  
  aws_auth_roles = var.aws_auth_roles
  aws_auth_users = var.aws_auth_users
}

# RDS PostgreSQL
module "rds" {
  source = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"
  
  identifier = "${var.project_name}-db"
  
  engine               = "postgres"
  engine_version       = var.postgres_version
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = var.db_instance_class
  
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_encrypted     = true
  
  db_name  = var.db_name
  username = var.db_username
  port     = 5432
  
  multi_az               = var.environment == "prod"
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [module.security_group_rds.security_group_id]
  
  backup_retention_period = var.db_backup_retention_period
  backup_window           = "03:00-06:00"
  maintenance_window      = "Mon:00:00-Mon:03:00"
  
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  monitoring_interval                   = 60
  monitoring_role_arn                   = aws_iam_role.rds_enhanced_monitoring.arn
  
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  deletion_protection = var.environment == "prod"
  
  tags = {
    Name = "${var.project_name}-db"
  }
}

# ElastiCache Redis
module "elasticache" {
  source = "terraform-aws-modules/elasticache/aws"
  version = "~> 1.0"
  
  cluster_id           = "${var.project_name}-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = var.redis_num_nodes
  parameter_group_name = "default.redis7"
  engine_version       = var.redis_version
  port                 = 6379
  
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [module.security_group_redis.security_group_id]
  
  snapshot_retention_limit = var.environment == "prod" ? 5 : 0
  snapshot_window          = "03:00-05:00"
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = {
    Name = "${var.project_name}-redis"
  }
}

# S3 Buckets
resource "aws_s3_bucket" "storage" {
  bucket = "${var.project_name}-storage-${var.environment}"
  
  tags = {
    Name = "${var.project_name}-storage"
  }
}

resource "aws_s3_bucket_versioning" "storage" {
  bucket = aws_s3_bucket.storage.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "storage" {
  bucket = aws_s3_bucket.storage.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "storage" {
  bucket = aws_s3_bucket.storage.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Application Load Balancer
module "alb" {
  source = "terraform-aws-modules/alb/aws"
  version = "~> 8.0"
  
  name = "${var.project_name}-alb"
  
  load_balancer_type = "application"
  
  vpc_id  = module.vpc.vpc_id
  subnets = module.vpc.public_subnets
  
  security_groups = [module.security_group_alb.security_group_id]
  
  access_logs = {
    bucket = aws_s3_bucket.alb_logs.id
  }
  
  target_groups = [
    {
      name_prefix      = "api-"
      backend_protocol = "HTTP"
      backend_port     = 80
      target_type      = "ip"
      
      health_check = {
        enabled             = true
        interval            = 30
        path                = "/health"
        port                = "traffic-port"
        healthy_threshold   = 2
        unhealthy_threshold = 2
        timeout             = 5
        protocol            = "HTTP"
        matcher             = "200"
      }
    }
  ]
  
  https_listeners = [
    {
      port            = 443
      protocol        = "HTTPS"
      certificate_arn = aws_acm_certificate.main.arn
      target_group_index = 0
    }
  ]
  
  http_tcp_listeners = [
    {
      port        = 80
      protocol    = "HTTP"
      action_type = "redirect"
      redirect = {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  ]
}

# Security Groups
module "security_group_alb" {
  source = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"
  
  name        = "${var.project_name}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = module.vpc.vpc_id
  
  ingress_rules = ["https-443-tcp", "http-80-tcp"]
  ingress_cidr_blocks = ["0.0.0.0/0"]
  
  egress_rules = ["all-all"]
}

module "security_group_rds" {
  source = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"
  
  name        = "${var.project_name}-rds-sg"
  description = "Security group for RDS"
  vpc_id      = module.vpc.vpc_id
  
  ingress_with_source_security_group_id = [
    {
      from_port                = 5432
      to_port                  = 5432
      protocol                 = "tcp"
      source_security_group_id = module.eks.node_security_group_id
    }
  ]
  
  egress_rules = ["all-all"]
}

module "security_group_redis" {
  source = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"
  
  name        = "${var.project_name}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = module.vpc.vpc_id
  
  ingress_with_source_security_group_id = [
    {
      from_port                = 6379
      to_port                  = 6379
      protocol                 = "tcp"
      source_security_group_id = module.eks.node_security_group_id
    }
  ]
  
  egress_rules = ["all-all"]
}

# IAM Roles
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name = "${var.project_name}-rds-monitoring-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
  
  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"]
}

# Outputs
output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  value = module.rds.db_instance_endpoint
}

output "redis_endpoint" {
  value = module.elasticache.cluster_cache_nodes[0].address
}

output "alb_dns_name" {
  value = module.alb.lb_dns_name
}