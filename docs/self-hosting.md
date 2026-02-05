# Self-Hosting Guide

Deploy DocsMCP on your own server for production use.

---

## Overview

This guide covers deploying DocsMCP on a VPS for:
- Remote access from Claude Desktop
- Team sharing
- Always-on documentation indexing

**Estimated time:** 30-60 minutes

---

## Prerequisites

- VPS with 1GB+ RAM (2GB recommended)
- Ubuntu 22.04+ or Debian 12+ (other Linux works too)
- Domain name (optional but recommended for SSL)
- Basic Linux command-line knowledge

---

## Recommended VPS Providers

Budget-friendly options that work well:

| Provider | Plan | Price | Specs |
|----------|------|-------|-------|
| Hetzner | CX22 | €4/mo | 2 vCPU, 4GB RAM |
| DigitalOcean | Basic | $6/mo | 1 vCPU, 1GB RAM |
| Vultr | Cloud | $6/mo | 1 vCPU, 1GB RAM |
| Linode | Nanode | $5/mo | 1 vCPU, 1GB RAM |
| Oracle Cloud | Free | $0 | 1 vCPU, 1GB RAM |

**Recommendation:** Hetzner CX22 offers the best value for DocsMCP.

---

## Step 1: Initial Server Setup

### Connect to Your Server

```bash
ssh root@your-server-ip
```

### Update System

```bash
apt update && apt upgrade -y
```

### Create Non-Root User

```bash
adduser docsmcp
usermod -aG sudo docsmcp
su - docsmcp
```

### Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker

# Verify
docker --version
```

---

## Step 2: Install DocsMCP

### Clone Repository

```bash
cd ~
git clone https://github.com/laxmanisawesome/docsmcp.git
cd docsmcp
```

### Configure Environment

```bash
cp .env.example .env
```

Generate a secure API token:

```bash
# Generate random token
openssl rand -hex 32

# Edit .env and set:
# API_TOKEN=<your-generated-token>
nano .env
```

Recommended production settings:

```bash
# .env
API_TOKEN=your-secure-32-char-token-here
HOST=127.0.0.1
PORT=8090
DATA_DIR=/home/docsmcp/docsmcp/data
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_VECTOR_INDEX=0
MAX_PAGES_PER_PROJECT=5000
RATE_LIMIT_REQUESTS=60
```

### Start DocsMCP

```bash
docker-compose up -d
```

### Verify Installation

```bash
curl http://localhost:8090/health
# Should return: {"status": "healthy", ...}
```

---

## Step 3: Set Up Reverse Proxy (nginx)

### Install nginx

```bash
sudo apt install nginx -y
```

### Configure nginx

```bash
sudo nano /etc/nginx/sites-available/docsmcp
```

**Without SSL (HTTP only):**

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Or use IP: your-server-ip

    location / {
        proxy_pass http://127.0.0.1:8090;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/docsmcp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Test External Access

```bash
curl http://your-server-ip/health
```

---

## Step 4: Enable SSL (Recommended)

### Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Obtain Certificate

```bash
sudo certbot --nginx -d your-domain.com
```

Follow the prompts. Certbot will:
1. Verify domain ownership
2. Obtain SSL certificate
3. Configure nginx automatically
4. Set up auto-renewal

### Verify SSL

```bash
curl https://your-domain.com/health
```

### Auto-Renewal

Certbot sets up auto-renewal. Verify:

```bash
sudo certbot renew --dry-run
```

---

## Step 5: Firewall Configuration

### Enable UFW

```bash
sudo ufw enable
```

### Allow Required Ports

```bash
# SSH (always allow first!)
sudo ufw allow ssh

# HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

### Optional: Restrict to Specific IPs

For maximum security, only allow your IP:

```bash
# Replace with your home/office IP
sudo ufw allow from YOUR_IP to any port 443

# Remove general HTTPS rule
sudo ufw delete allow 443/tcp
```

---

## Step 6: Configure Claude Desktop

Update your Claude Desktop config to connect to the remote server:

### With SSL (Recommended)

```json
{
  "mcpServers": {
    "docs": {
      "url": "https://your-domain.com/mcp",
      "headers": {
        "Authorization": "Bearer your-api-token"
      }
    }
  }
}
```

### Without SSL (Not Recommended)

```json
{
  "mcpServers": {
    "docs": {
      "url": "http://your-server-ip/mcp",
      "headers": {
        "Authorization": "Bearer your-api-token"
      }
    }
  }
}
```

---

## Step 7: Set Up Backups

### Automated Daily Backups

Create backup script:

```bash
nano ~/docsmcp/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/docsmcp/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DATA_DIR="/home/docsmcp/docsmcp/data"

mkdir -p "$BACKUP_DIR"

# Create backup
tar -czf "$BACKUP_DIR/docsmcp_backup_$DATE.tar.gz" -C "$DATA_DIR" .

# Keep only last 7 days
find "$BACKUP_DIR" -name "docsmcp_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: docsmcp_backup_$DATE.tar.gz"
```

```bash
chmod +x ~/docsmcp/backup.sh
```

### Add to Crontab

```bash
crontab -e
```

Add:

```cron
# Daily backup at 3 AM
0 3 * * * /home/docsmcp/docsmcp/backup.sh >> /home/docsmcp/backup.log 2>&1
```

### Optional: Remote Backup

Send backups to remote storage:

```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure (follow prompts for your provider)
rclone config

# Add to backup script:
rclone copy "$BACKUP_DIR/docsmcp_backup_$DATE.tar.gz" remote:docsmcp-backups/
```

---

## Step 8: Monitoring

### Basic Health Check

Create monitoring script:

```bash
nano ~/docsmcp/monitor.sh
```

```bash
#!/bin/bash
HEALTH_URL="http://localhost:8090/health"
WEBHOOK_URL=""  # Optional: Slack/Discord webhook

response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")

if [ "$response" != "200" ]; then
    echo "$(date): DocsMCP health check failed with status $response"
    
    # Restart container
    cd ~/docsmcp && docker-compose restart
    
    # Send alert (if webhook configured)
    if [ -n "$WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"⚠️ DocsMCP health check failed, restarting..."}' \
            "$WEBHOOK_URL"
    fi
fi
```

```bash
chmod +x ~/docsmcp/monitor.sh
```

Add to crontab (every 5 minutes):

```cron
*/5 * * * * /home/docsmcp/docsmcp/monitor.sh >> /home/docsmcp/monitor.log 2>&1
```

### Docker Logs

View logs:

```bash
cd ~/docsmcp
docker-compose logs -f
```

### System Resources

```bash
# Check memory usage
free -h

# Check disk usage
df -h

# Check Docker stats
docker stats
```

---

## Step 9: Scheduled Scrapes

### Via Crontab

```bash
crontab -e
```

Add scheduled scrapes:

```cron
# Scrape React docs daily at 2 AM
0 2 * * * curl -X POST https://your-domain.com/api/projects/react/scrape -H "Authorization: Bearer your-token"

# Scrape Python docs weekly on Sunday at 3 AM
0 3 * * 0 curl -X POST https://your-domain.com/api/projects/python/scrape -H "Authorization: Bearer your-token"
```

---

## Security Checklist

Before exposing to the internet:

- [ ] **Strong API token** — 32+ characters, randomly generated
- [ ] **SSL enabled** — Never expose HTTP to public internet
- [ ] **Firewall configured** — Only required ports open
- [ ] **Fail2ban installed** — Protect against brute force
- [ ] **Automatic updates** — `unattended-upgrades` package
- [ ] **Backups configured** — Test restore procedure
- [ ] **Monitoring active** — Health checks and alerts

### Install Fail2ban

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Enable Automatic Updates

```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Check if port is in use
sudo lsof -i :8090

# Restart Docker
sudo systemctl restart docker
```

### nginx 502 Bad Gateway

1. Verify DocsMCP is running:
   ```bash
   docker-compose ps
   ```

2. Check nginx can reach backend:
   ```bash
   curl http://127.0.0.1:8090/health
   ```

3. Check nginx error logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Check nginx config
sudo nginx -t
```

### Out of Disk Space

```bash
# Check usage
df -h

# Clean Docker
docker system prune -a

# Remove old backups
find ~/backups -name "*.tar.gz" -mtime +7 -delete
```

---

## Updating DocsMCP

```bash
cd ~/docsmcp
git pull
docker-compose pull
docker-compose up -d
```

---

## Next Steps

- [Configuration Guide](configuration.md) — Fine-tune settings
- [API Reference](api-reference.md) — Endpoint documentation
- [MCP Setup](mcp-setup.md) — Connect clients
