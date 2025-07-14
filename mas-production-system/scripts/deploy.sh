#!/bin/bash
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Configuration
ENVIRONMENT=${1:-staging}
NAMESPACE="mas-system"
TIMEOUT="10m"

echo -e "${YELLOW}Deploying to ${ENVIRONMENT}...${NC}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    echo -e "${RED}Invalid environment: $ENVIRONMENT${NC}"
    exit 1
fi

# Load environment configuration
source "config/${ENVIRONMENT}.env"

# Connect to cluster
echo -e "${YELLOW}Connecting to Kubernetes cluster...${NC}"
aws eks update-kubeconfig --name "${CLUSTER_NAME}" --region "${AWS_REGION}"

# Create namespace if not exists
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Apply ConfigMaps and Secrets
echo -e "${YELLOW}Applying configuration...${NC}"
kubectl apply -f "infrastructure/kubernetes/configmap-${ENVIRONMENT}.yaml"

# Deploy database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
kubectl apply -f infrastructure/kubernetes/jobs/db-migration.yaml
kubectl wait --for=condition=complete job/db-migration -n "${NAMESPACE}" --timeout="${TIMEOUT}"

# Deploy services
echo -e "${YELLOW}Deploying services...${NC}"
for service in core api auth gateway; do
    echo -e "  Deploying ${service}..."
    kubectl apply -f "infrastructure/kubernetes/deployments/${service}.yaml"
done

# Wait for rollout
echo -e "${YELLOW}Waiting for rollout to complete...${NC}"
kubectl rollout status deployment/mas-core -n "${NAMESPACE}" --timeout="${TIMEOUT}"
kubectl rollout status deployment/mas-api -n "${NAMESPACE}" --timeout="${TIMEOUT}"

# Run health checks
echo -e "${YELLOW}Running health checks...${NC}"
./scripts/health-checks.sh "${ENVIRONMENT}"

# Update DNS if production
if [[ "$ENVIRONMENT" == "production" ]]; then
    echo -e "${YELLOW}Updating DNS...${NC}"
    ./scripts/update-dns.sh
fi

echo -e "${GREEN}Deployment to ${ENVIRONMENT} complete!${NC}"

# Send notification
if [[ -n "${SLACK_WEBHOOK:-}" ]]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"Deployment to ${ENVIRONMENT} completed successfully\"}" \
        "${SLACK_WEBHOOK}"
fi