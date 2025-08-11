# DigitalOcean Deployment Guide for MSP Dashboard

This guide will help you deploy your MSP Dashboard application to DigitalOcean with SSL certificates and proper configuration for `*.rocket-command.com` subdomains.

## Prerequisites

1. A DigitalOcean account
2. A domain name (rocket-command.com) with DNS access
3. Docker and Docker Compose installed on your DigitalOcean droplet

## Step 1: Create a DigitalOcean Droplet

1. Log into your DigitalOcean account
2. Create a new droplet with the following specifications:
   - **Image**: Ubuntu 22.04 LTS
   - **Size**: Basic plan with at least 2GB RAM (recommended: 4GB RAM)
   - **Datacenter**: Choose the closest to your users
   - **Authentication**: SSH key (recommended) or password
   - **Hostname**: `msp-dashboard`

## Step 2: Configure DNS Records

Before deploying, configure your DNS records:

1. Go to your domain registrar's DNS settings
2. Add the following records:
   ```
   Type: A
   Name: @
   Value: [Your DigitalOcean droplet IP]
   TTL: 300
   ```
   ```
   Type: A
   Name: *
   Value: [Your DigitalOcean droplet IP]
   TTL: 300
   ```

## Step 3: Connect to Your Droplet

```bash
ssh root@[your-droplet-ip]
```

## Step 4: Install Docker and Docker Compose

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add user to docker group
usermod -aG docker $USER
```

## Step 5: Clone Your Repository

```bash
# Install git
apt install git -y

# Clone your repository
git clone https://github.com/your-username/msp-dashboard.git
cd msp-dashboard
```

## Step 6: Configure Environment Variables

```bash
# Copy the environment template
cp env.example .env

# Edit the environment file
nano .env
```

Update the following variables in your `.env` file:

```bash
# Generate a secure secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

# Update these values
DB_PASSWORD=your-secure-database-password
ADMIN_PASSWORD=your-secure-admin-password
CERTBOT_EMAIL=your-email@rocket-command.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Step 7: Make Deployment Script Executable

```bash
chmod +x deploy.sh
```

## Step 8: Deploy the Application

```bash
# Run the deployment script
./deploy.sh
```

The script will:
- Build and start all services
- Set up SSL certificates automatically
- Run database migrations
- Create a superuser account
- Configure automatic SSL renewal

## Step 9: Verify Deployment

After deployment, verify everything is working:

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Test the application
curl -I https://rocket-command.com/health/
```

## Step 10: Configure Firewall

```bash
# Allow SSH, HTTP, and HTTPS
ufw allow ssh
ufw allow 80
ufw allow 443
ufw enable
```

## Step 11: Set Up Monitoring (Optional)

### Install monitoring tools:

```bash
# Install htop for system monitoring
apt install htop -y

# Install logrotate for log management
apt install logrotate -y
```

### Create a monitoring script:

```bash
cat > /root/monitor.sh << 'EOF'
#!/bin/bash
echo "=== System Status ==="
df -h
echo ""
echo "=== Memory Usage ==="
free -h
echo ""
echo "=== Docker Status ==="
docker-compose ps
echo ""
echo "=== Recent Logs ==="
docker-compose logs --tail=20
EOF

chmod +x /root/monitor.sh
```

## Step 12: Set Up Backups

Create a backup script:

```bash
cat > /root/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U postgres msp_dashboard > $BACKUP_DIR/db_backup_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz media/

# Backup SSL certificates
tar -czf $BACKUP_DIR/ssl_backup_$DATE.tar.gz ssl_certs/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /root/backup.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /root/backup.sh") | crontab -
```

## Troubleshooting

### Common Issues:

1. **SSL Certificate Issues**:
   ```bash
   # Renew certificates manually
   docker-compose run --rm certbot renew
   docker-compose restart nginx
   ```

2. **Database Connection Issues**:
   ```bash
   # Check database logs
   docker-compose logs db
   
   # Restart database
   docker-compose restart db
   ```

3. **Application Not Starting**:
   ```bash
   # Check application logs
   docker-compose logs app
   
   # Rebuild application
   docker-compose build --no-cache app
   docker-compose up -d app
   ```

4. **Nginx Issues**:
   ```bash
   # Check nginx configuration
   docker-compose exec nginx nginx -t
   
   # Restart nginx
   docker-compose restart nginx
   ```

### Useful Commands:

```bash
# View all logs
docker-compose logs -f

# Restart all services
docker-compose restart

# Update application
git pull
docker-compose build --no-cache
docker-compose up -d

# Check disk usage
df -h

# Check memory usage
free -h

# Monitor system resources
htop
```

## Security Considerations

1. **Change default passwords** in the `.env` file
2. **Set up firewall rules** to restrict access
3. **Regularly update** your system and Docker images
4. **Monitor logs** for suspicious activity
5. **Set up alerts** for system issues

## Performance Optimization

1. **Enable gzip compression** (already configured in nginx)
2. **Use CDN** for static assets (optional)
3. **Monitor resource usage** and scale if needed
4. **Optimize database queries** and add indexes as needed

## Maintenance

### Regular Tasks:

1. **Weekly**: Check logs and system resources
2. **Monthly**: Update Docker images and system packages
3. **Quarterly**: Review security settings and backup procedures

### Update Procedure:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

# Run migrations
docker-compose exec app python manage.py migrate

# Collect static files
docker-compose exec app python manage.py collectstatic --noinput
```

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify DNS settings
3. Check firewall configuration
4. Ensure SSL certificates are valid
5. Review the troubleshooting section above

Your MSP Dashboard should now be accessible at `https://rocket-command.com` with support for all subdomains under `*.rocket-command.com`. 