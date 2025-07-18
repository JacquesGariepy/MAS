# Docker Security Hardening Guide for MAS

## Overview

This guide provides step-by-step instructions to harden the Docker environment for the Multi-Agent System, implementing defense-in-depth security measures.

## 1. Hardened Docker Compose Configuration

### 1.1 Create Secure Docker Compose File

Create `docker-compose.secure.yml`:

```yaml
version: '3.8'

services:
  core:
    build:
      context: ./services/core
      dockerfile: Dockerfile.secure
    image: mas-core:secure
    container_name: mas-core-secure
    
    # Security configurations
    security_opt:
      - no-new-privileges:true
      - seccomp:./security/seccomp-profile.json
      - apparmor:docker-mas-core
    
    # Capability dropping
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - DAC_OVERRIDE
      - SETGID
      - SETUID
      - NET_BIND_SERVICE
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    
    # User mapping
    user: "1000:1000"
    
    # Read-only root filesystem
    read_only: true
    
    # Temporary filesystems for writable areas
    tmpfs:
      - /tmp:noexec,nosuid,size=100M
      - /app/tmp:noexec,nosuid,size=100M
      - /run:noexec,nosuid,size=10M
    
    # Volume mounts with restrictions
    volumes:
      # Source code - read-only
      - ./services/core/src:/app/src:ro
      
      # Agent workspaces - isolated per agent
      - type: volume
        source: agent_workspaces
        target: /app/agent_workspaces
        volume:
          nocopy: true
      
      # Logs - write only, no execute
      - type: volume
        source: logs
        target: /app/logs
        volume:
          nocopy: true
      
      # Cache directory
      - type: tmpfs
        target: /app/.cache
        tmpfs:
          size: 100M
    
    # Network configuration
    networks:
      - mas_internal
      - mas_external
    
    # Port mapping
    ports:
      - "127.0.0.1:8088:8000"  # Bind only to localhost
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 40s
    
    # Environment variables
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - PYTHONDONTWRITEBYTECODE=1
      - PYTHONUNBUFFERED=1
    
    # Secrets management
    secrets:
      - db_password
      - jwt_secret
      - llm_api_key
    
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    
    # Restart policy
    restart: unless-stopped
    
    # Logging configuration
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=mas-core"

  db:
    image: postgres:15-alpine
    container_name: mas-db-secure
    
    # Security
    security_opt:
      - no-new-privileges:true
    
    # User
    user: "70:70"  # postgres user
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    
    # Environment
    environment:
      POSTGRES_DB: mas
      POSTGRES_USER: mas_user
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256 --auth-local=trust"
    
    # Volumes
    volumes:
      - postgres_data:/var/lib/postgresql/data:Z
      - ./security/postgres/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    
    # Network
    networks:
      - mas_internal
    
    # No exposed ports - internal only
    expose:
      - 5432
    
    # Secrets
    secrets:
      - db_password
    
    # Health check
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mas_user -d mas"]
      interval: 10s
      timeout: 5s
      retries: 5
    
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: mas-redis-secure
    
    # Security
    security_opt:
      - no-new-privileges:true
    
    # User
    user: "999:999"  # redis user
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    
    # Command with security options
    command: >
      redis-server
      --appendonly yes
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --protected-mode yes
      --bind 0.0.0.0
    
    # Volumes
    volumes:
      - redis_data:/data:Z
    
    # Network
    networks:
      - mas_internal
    
    # No exposed ports
    expose:
      - 6379
    
    # Environment
    environment:
      REDIS_PASSWORD_FILE: /run/secrets/redis_password
    
    secrets:
      - redis_password
    
    restart: unless-stopped

# Networks
networks:
  mas_internal:
    driver: bridge
    internal: true
    driver_opts:
      com.docker.network.bridge.name: mas_int
  
  mas_external:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: mas_ext

# Volumes
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/postgres
  
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/redis
  
  agent_workspaces:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/agent_workspaces
  
  logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./logs

# Secrets
secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  llm_api_key:
    file: ./secrets/llm_api_key.txt
  redis_password:
    file: ./secrets/redis_password.txt
```

### 1.2 Create Hardened Dockerfile

Create `services/core/Dockerfile.secure`:

```dockerfile
# Build stage
FROM python:3.11-slim as builder

# Security: Don't run as root during build
RUN useradd -r -u 1001 builder
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-prod.txt ./
RUN chown -R builder:builder /build

# Switch to non-root user for pip install
USER builder

# Install Python dependencies
RUN pip install --user --no-cache-dir --upgrade pip && \
    pip install --user --no-cache-dir -r requirements-prod.txt

# Runtime stage
FROM python:3.11-slim

# Security hardening
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    dumb-init \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create non-root user
RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -s /sbin/nologin -c "App user" appuser

# Create necessary directories with proper permissions
RUN mkdir -p /app /app/logs /app/tmp /app/agent_workspaces /app/.cache && \
    chown -R appuser:appuser /app && \
    chmod 750 /app && \
    chmod 770 /app/logs /app/tmp /app/agent_workspaces

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /build/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code
COPY --chown=appuser:appuser . .

# Security: Remove unnecessary files
RUN find /app -name "*.pyc" -delete && \
    find /app -name "__pycache__" -type d -exec rm -rf {} + && \
    find /app -type f -name "*.py" -exec chmod 644 {} + && \
    find /app -type d -exec chmod 755 {} +

# Security: Set up Python environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Switch to non-root user
USER appuser

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port (documentation only, not binding)
EXPOSE 8000

# Run with gunicorn
CMD ["gunicorn", "src.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
```

## 2. Security Profiles

### 2.1 Seccomp Profile

Create `security/seccomp-profile.json`:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "archMap": [
    {
      "architecture": "SCMP_ARCH_X86_64",
      "subArchitectures": [
        "SCMP_ARCH_X86",
        "SCMP_ARCH_X32"
      ]
    }
  ],
  "syscalls": [
    {
      "names": [
        "accept", "accept4", "access", "adjtimex", "alarm", "bind",
        "brk", "capget", "capset", "chdir", "chmod", "chown", "chown32",
        "clock_adjtime", "clock_adjtime64", "clock_getres", "clock_getres_time64",
        "clock_gettime", "clock_gettime64", "clock_nanosleep", "clock_nanosleep_time64",
        "close", "close_range", "connect", "copy_file_range", "creat",
        "dup", "dup2", "dup3", "epoll_create", "epoll_create1", "epoll_ctl",
        "epoll_ctl_old", "epoll_pwait", "epoll_pwait2", "epoll_wait",
        "epoll_wait_old", "eventfd", "eventfd2", "execve", "execveat",
        "exit", "exit_group", "faccessat", "faccessat2", "fadvise64",
        "fadvise64_64", "fallocate", "fanotify_mark", "fchdir", "fchmod",
        "fchmodat", "fchown", "fchown32", "fchownat", "fcntl", "fcntl64",
        "fdatasync", "fgetxattr", "flistxattr", "flock", "fork", "fremovexattr",
        "fsetxattr", "fstat", "fstat64", "fstatat64", "fstatfs", "fstatfs64",
        "fsync", "ftruncate", "ftruncate64", "futex", "futex_time64",
        "futimesat", "getcpu", "getcwd", "getdents", "getdents64", "getegid",
        "getegid32", "geteuid", "geteuid32", "getgid", "getgid32", "getgroups",
        "getgroups32", "getitimer", "getpeername", "getpgid", "getpgrp",
        "getpid", "getppid", "getpriority", "getrandom", "getresgid",
        "getresgid32", "getresuid", "getresuid32", "getrlimit", "get_robust_list",
        "getrusage", "getsid", "getsockname", "getsockopt", "get_thread_area",
        "gettid", "gettimeofday", "getuid", "getuid32", "getxattr", "inotify_add_watch",
        "inotify_init", "inotify_init1", "inotify_rm_watch", "io_cancel",
        "ioctl", "io_destroy", "io_getevents", "io_pgetevents", "io_pgetevents_time64",
        "ioprio_get", "ioprio_set", "io_setup", "io_submit", "ipc", "kill",
        "lchown", "lchown32", "lgetxattr", "link", "linkat", "listen",
        "listxattr", "llistxattr", "_llseek", "lremovexattr", "lseek",
        "lsetxattr", "lstat", "lstat64", "madvise", "membarrier", "memfd_create",
        "mincore", "mkdir", "mkdirat", "mknod", "mknodat", "mlock", "mlock2",
        "mlockall", "mmap", "mmap2", "mprotect", "mq_getsetattr", "mq_notify",
        "mq_open", "mq_timedreceive", "mq_timedreceive_time64", "mq_timedsend",
        "mq_timedsend_time64", "mq_unlink", "mremap", "msgctl", "msgget",
        "msgrcv", "msgsnd", "msync", "munlock", "munlockall", "munmap",
        "nanosleep", "newfstatat", "_newselect", "open", "openat", "openat2",
        "pause", "pipe", "pipe2", "poll", "ppoll", "ppoll_time64", "prctl",
        "pread64", "preadv", "preadv2", "prlimit64", "pselect6", "pselect6_time64",
        "pwrite64", "pwritev", "pwritev2", "read", "readahead", "readlink",
        "readlinkat", "readv", "recv", "recvfrom", "recvmmsg", "recvmmsg_time64",
        "recvmsg", "remap_file_pages", "removexattr", "rename", "renameat",
        "renameat2", "restart_syscall", "rmdir", "rt_sigaction", "rt_sigpending",
        "rt_sigprocmask", "rt_sigqueueinfo", "rt_sigreturn", "rt_sigsuspend",
        "rt_sigtimedwait", "rt_sigtimedwait_time64", "rt_tgsigqueueinfo",
        "sched_getaffinity", "sched_getattr", "sched_getparam", "sched_get_priority_max",
        "sched_get_priority_min", "sched_getscheduler", "sched_rr_get_interval",
        "sched_rr_get_interval_time64", "sched_setaffinity", "sched_setattr",
        "sched_setparam", "sched_setscheduler", "sched_yield", "seccomp",
        "select", "semctl", "semget", "semop", "semtimedop", "semtimedop_time64",
        "send", "sendfile", "sendfile64", "sendmmsg", "sendmsg", "sendto",
        "setfsgid", "setfsgid32", "setfsuid", "setfsuid32", "setgid", "setgid32",
        "setgroups", "setgroups32", "setitimer", "setpgid", "setpriority",
        "setregid", "setregid32", "setresgid", "setresgid32", "setresuid",
        "setresuid32", "setreuid", "setreuid32", "setrlimit", "set_robust_list",
        "setsid", "setsockopt", "set_thread_area", "set_tid_address", "setuid",
        "setuid32", "setxattr", "shmat", "shmctl", "shmdt", "shmget", "shutdown",
        "sigaltstack", "signalfd", "signalfd4", "sigreturn", "socket", "socketcall",
        "socketpair", "splice", "stat", "stat64", "statfs", "statfs64", "statx",
        "symlink", "symlinkat", "sync", "sync_file_range", "syncfs", "sysinfo",
        "tee", "tgkill", "time", "timer_create", "timer_delete", "timer_getoverrun",
        "timer_gettime", "timer_gettime64", "timer_settime", "timer_settime64",
        "timerfd_create", "timerfd_gettime", "timerfd_gettime64", "timerfd_settime",
        "timerfd_settime64", "times", "tkill", "truncate", "truncate64", "ugetrlimit",
        "umask", "uname", "unlink", "unlinkat", "utime", "utimensat", "utimensat_time64",
        "utimes", "vfork", "vmsplice", "wait4", "waitid", "waitpid", "write", "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["ptrace"],
      "action": "SCMP_ACT_ALLOW",
      "args": [
        {
          "index": 0,
          "value": 0,
          "op": "SCMP_CMP_EQ"
        }
      ]
    },
    {
      "names": ["personality"],
      "action": "SCMP_ACT_ALLOW",
      "args": [
        {
          "index": 0,
          "value": 0,
          "op": "SCMP_CMP_EQ"
        }
      ]
    },
    {
      "names": ["clone"],
      "action": "SCMP_ACT_ALLOW",
      "args": [
        {
          "index": 0,
          "value": 2114060288,
          "op": "SCMP_CMP_MASKED_EQ",
          "comment": "CLONE_NEWUSER"
        }
      ]
    }
  ]
}
```

### 2.2 AppArmor Profile

Create `security/apparmor/docker-mas-core`:

```
#include <tunables/global>

profile docker-mas-core flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/python>
  
  # Network access
  network inet stream,
  network inet6 stream,
  
  # File access
  /app/ r,
  /app/** r,
  /app/src/** r,
  /app/logs/** rw,
  /app/agent_workspaces/** rw,
  /app/tmp/** rw,
  /app/.cache/** rw,
  
  # Python
  /usr/bin/python3.11 ix,
  /usr/local/bin/python3.11 ix,
  /home/appuser/.local/** r,
  
  # System files
  /etc/passwd r,
  /etc/group r,
  /etc/nsswitch.conf r,
  /etc/resolv.conf r,
  /etc/hosts r,
  /etc/localtime r,
  
  # Proc files
  /proc/sys/kernel/random/boot_id r,
  /proc/self/fd/ r,
  /proc/meminfo r,
  /proc/stat r,
  
  # Deny everything else
  deny /** w,
  deny /etc/** w,
  deny /root/** rwx,
  deny /home/** rwx,
  deny /var/** w,
  deny /boot/** rwx,
  deny /dev/** rwx,
  deny /lib/** w,
  deny /media/** rwx,
  deny /mnt/** rwx,
  deny /opt/** w,
  deny /proc/** w,
  deny /sbin/** rwx,
  deny /srv/** rwx,
  deny /sys/** rwx,
  deny /usr/** w,
}
```

## 3. Setup Scripts

### 3.1 Security Setup Script

Create `scripts/setup-security.sh`:

```bash
#!/bin/bash
set -euo pipefail

echo "Setting up MAS Docker security..."

# Create directories
mkdir -p security/{postgres,apparmor,secrets}
mkdir -p data/{postgres,redis,agent_workspaces}
mkdir -p logs

# Set permissions
chmod 700 security/secrets
chmod 755 data/{postgres,redis,agent_workspaces}
chmod 755 logs

# Generate secrets if they don't exist
if [ ! -f security/secrets/db_password.txt ]; then
    openssl rand -base64 32 > security/secrets/db_password.txt
    chmod 600 security/secrets/db_password.txt
fi

if [ ! -f security/secrets/jwt_secret.txt ]; then
    openssl rand -base64 64 > security/secrets/jwt_secret.txt
    chmod 600 security/secrets/jwt_secret.txt
fi

if [ ! -f security/secrets/redis_password.txt ]; then
    openssl rand -base64 32 > security/secrets/redis_password.txt
    chmod 600 security/secrets/redis_password.txt
fi

# Create PostgreSQL config
cat > security/postgres/postgresql.conf <<EOF
# Security settings
ssl = on
ssl_cert_file = '/var/lib/postgresql/server.crt'
ssl_key_file = '/var/lib/postgresql/server.key'
ssl_ciphers = 'HIGH:MEDIUM:!3DES:!aNULL:!MD5:!RC4'
ssl_prefer_server_ciphers = on
ssl_min_protocol_version = 'TLSv1.2'

# Connection settings
listen_addresses = '*'
max_connections = 100
password_encryption = scram-sha-256

# Logging
log_connections = on
log_disconnections = on
log_hostname = off
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# Performance
shared_buffers = 256MB
work_mem = 4MB
maintenance_work_mem = 64MB
EOF

# Load AppArmor profile if AppArmor is available
if command -v aa-status &> /dev/null; then
    echo "Loading AppArmor profile..."
    sudo cp security/apparmor/docker-mas-core /etc/apparmor.d/
    sudo apparmor_parser -r /etc/apparmor.d/docker-mas-core
fi

echo "Security setup complete!"
```

### 3.2 Security Check Script

Create `scripts/check-security.sh`:

```bash
#!/bin/bash

echo "MAS Docker Security Check"
echo "========================="

# Check Docker daemon security
echo -e "\n[Docker Daemon Security]"
docker version --format '{{.Server.Version}}' | xargs -I {} echo "Docker version: {}"

# Check container security
echo -e "\n[Container Security Settings]"
for container in $(docker ps --format "{{.Names}}"); do
    echo -e "\nContainer: $container"
    
    # Check if running as root
    docker exec $container id -u | xargs -I {} echo "  User ID: {}"
    
    # Check capabilities
    echo "  Capabilities:"
    docker inspect $container --format='{{range .HostConfig.CapDrop}}  - Dropped: {{.}}{{end}}'
    docker inspect $container --format='{{range .HostConfig.CapAdd}}  - Added: {{.}}{{end}}'
    
    # Check security options
    echo "  Security Options:"
    docker inspect $container --format='{{range .HostConfig.SecurityOpt}}  - {{.}}{{end}}'
    
    # Check read-only root
    docker inspect $container --format='  Read-only root: {{.HostConfig.ReadonlyRootfs}}'
    
    # Check resource limits
    docker inspect $container --format='  Memory limit: {{.HostConfig.Memory}}'
    docker inspect $container --format='  CPU limit: {{.HostConfig.CpuQuota}}'
done

# Check volumes
echo -e "\n[Volume Security]"
for volume in $(docker volume ls -q | grep mas); do
    echo -e "\nVolume: $volume"
    docker volume inspect $volume --format='  Driver: {{.Driver}}'
    docker volume inspect $volume --format='  Mountpoint: {{.Mountpoint}}'
done

# Check networks
echo -e "\n[Network Security]"
for network in $(docker network ls --format "{{.Name}}" | grep mas); do
    echo -e "\nNetwork: $network"
    docker network inspect $network --format='  Internal: {{.Internal}}'
    docker network inspect $network --format='  Driver: {{.Driver}}'
done

# Check secrets
echo -e "\n[Secrets Status]"
for secret in db_password jwt_secret llm_api_key redis_password; do
    if [ -f "security/secrets/${secret}.txt" ]; then
        echo "  ✓ ${secret} exists"
        stat -c "    Permissions: %a" "security/secrets/${secret}.txt"
    else
        echo "  ✗ ${secret} missing"
    fi
done

echo -e "\n[Security Scan Complete]"
```

## 4. Runtime Security Monitoring

### 4.1 Security Monitoring Script

Create `scripts/monitor-security.py`:

```python
#!/usr/bin/env python3
import docker
import json
import time
from datetime import datetime
from pathlib import Path

class SecurityMonitor:
    def __init__(self):
        self.client = docker.from_env()
        self.alerts = []
    
    def check_container_security(self, container):
        """Check container security settings"""
        issues = []
        
        # Check if running as root
        result = container.exec_run("id -u")
        if result.output.decode().strip() == "0":
            issues.append("Container running as root")
        
        # Check for privileged mode
        if container.attrs['HostConfig']['Privileged']:
            issues.append("Container running in privileged mode")
        
        # Check capabilities
        cap_add = container.attrs['HostConfig'].get('CapAdd', [])
        dangerous_caps = ['SYS_ADMIN', 'SYS_PTRACE', 'SYS_MODULE']
        for cap in cap_add:
            if cap in dangerous_caps:
                issues.append(f"Dangerous capability added: {cap}")
        
        # Check for host network mode
        if container.attrs['HostConfig']['NetworkMode'] == 'host':
            issues.append("Container using host network mode")
        
        # Check for host PID mode
        if container.attrs['HostConfig']['PidMode'] == 'host':
            issues.append("Container using host PID namespace")
        
        return issues
    
    def check_file_operations(self, container):
        """Monitor file operations"""
        # Check agent workspace usage
        workspace_path = "/app/agent_workspaces"
        result = container.exec_run(f"du -sh {workspace_path}")
        if result.exit_code == 0:
            size = result.output.decode().split()[0]
            print(f"  Agent workspace usage: {size}")
        
        # Check for suspicious file access
        result = container.exec_run("find /app -type f -mmin -5 -ls")
        if result.exit_code == 0:
            recent_files = result.output.decode().strip()
            if recent_files:
                print("  Recent file modifications:")
                for line in recent_files.split('\n')[:5]:
                    print(f"    {line}")
    
    def monitor(self):
        """Main monitoring loop"""
        print(f"Security monitoring started at {datetime.now()}")
        
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Security Check")
            
            for container in self.client.containers.list():
                if 'mas' in container.name:
                    print(f"\nChecking container: {container.name}")
                    
                    # Security checks
                    issues = self.check_container_security(container)
                    if issues:
                        print("  Security issues:")
                        for issue in issues:
                            print(f"    ⚠️  {issue}")
                            self.alerts.append({
                                'timestamp': datetime.now().isoformat(),
                                'container': container.name,
                                'issue': issue
                            })
                    else:
                        print("  ✅ Security checks passed")
                    
                    # File operations
                    self.check_file_operations(container)
                    
                    # Resource usage
                    stats = container.stats(stream=False)
                    cpu_percent = self.calculate_cpu_percent(stats)
                    memory_usage = stats['memory_stats']['usage'] / (1024**2)  # MB
                    print(f"  Resources: CPU: {cpu_percent:.1f}%, Memory: {memory_usage:.1f}MB")
            
            # Save alerts
            if self.alerts:
                with open('security_alerts.json', 'w') as f:
                    json.dump(self.alerts, f, indent=2)
            
            time.sleep(60)  # Check every minute
    
    def calculate_cpu_percent(self, stats):
        """Calculate CPU percentage"""
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                   stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                      stats['precpu_stats']['system_cpu_usage']
        
        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * \
                         len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
            return cpu_percent
        return 0.0

if __name__ == "__main__":
    monitor = SecurityMonitor()
    try:
        monitor.monitor()
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
```

## 5. Deployment Guide

### 5.1 Initial Deployment

```bash
# 1. Run security setup
chmod +x scripts/setup-security.sh
./scripts/setup-security.sh

# 2. Build secure image
docker-compose -f docker-compose.secure.yml build

# 3. Start services
docker-compose -f docker-compose.secure.yml up -d

# 4. Check security
chmod +x scripts/check-security.sh
./scripts/check-security.sh

# 5. Start monitoring
python3 scripts/monitor-security.py
```

### 5.2 Security Checklist

- [ ] All containers running as non-root users
- [ ] Capabilities dropped (ALL) with minimal additions
- [ ] Read-only root filesystem enabled
- [ ] Resource limits configured
- [ ] Secrets stored securely (not in environment)
- [ ] Network isolation implemented
- [ ] Seccomp profiles applied
- [ ] AppArmor/SELinux profiles loaded
- [ ] Volume permissions restricted
- [ ] Logging configured
- [ ] Health checks enabled
- [ ] Security monitoring active

## 6. Incident Response

### 6.1 Security Breach Response

1. **Immediate Actions:**
   ```bash
   # Stop affected container
   docker stop mas-core-secure
   
   # Preserve evidence
   docker logs mas-core-secure > incident_logs.txt
   docker inspect mas-core-secure > incident_inspect.json
   
   # Check for file modifications
   docker exec mas-core-secure find /app -type f -mtime -1 -ls
   ```

2. **Investigation:**
   - Review security alerts
   - Check audit logs
   - Analyze file changes
   - Review network connections

3. **Recovery:**
   - Rebuild from secure image
   - Restore from clean backup
   - Rotate all secrets
   - Apply security patches

## Conclusion

This hardened Docker configuration provides:
- Defense in depth security layers
- Principle of least privilege
- Resource isolation
- Security monitoring
- Incident response capabilities

Regular security audits and updates are essential to maintain security posture.