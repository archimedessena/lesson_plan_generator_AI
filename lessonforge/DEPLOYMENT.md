# LessonForge Deployment Guide

## Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Create production `.env` file from `.env.example`
- [ ] Set strong `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up PostgreSQL database
- [ ] Set up Redis instance
- [ ] Obtain Anthropic API key
- [ ] Configure Paystack keys
- [ ] Set up email service (Mailgun/SendGrid)

### 2. Security
- [ ] SSL certificate installed
- [ ] HTTPS redirect enabled
- [ ] Security headers configured
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] Database passwords are strong
- [ ] API keys stored securely

### 3. Database
- [ ] Migrations generated
- [ ] Migrations applied
- [ ] Superuser created
- [ ] Initial data loaded (templates)
- [ ] Database backups configured

### 4. Static Files
- [ ] Static files collected
- [ ] WhiteNoise configured
- [ ] CDN configured (optional)
- [ ] Media storage configured

### 5. Monitoring
- [ ] Sentry configured for error tracking
- [ ] Application logging enabled
- [ ] Performance monitoring setup
- [ ] Uptime monitoring configured

## Deployment Options

### Option 1: Heroku (Easiest)

1. Install Heroku CLI
2. Login to Heroku:
```bash
heroku login
```

3. Create app:
```bash
heroku create lessonforge-prod
```

4. Add PostgreSQL:
```bash
heroku addons:create heroku-postgresql:mini
```

5. Add Redis:
```bash
heroku addons:create heroku-redis:mini
```

6. Set environment variables:
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ANTHROPIC_API_KEY=your-api-key
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=lessonforge-prod.herokuapp.com
# ... set all other env vars
```

7. Deploy:
```bash
git push heroku main
```

8. Run migrations:
```bash
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

9. Scale workers:
```bash
heroku ps:scale web=1 worker=1
```

### Option 2: DigitalOcean App Platform

1. Connect GitHub repository
2. Configure environment variables in dashboard
3. Add PostgreSQL database addon
4. Add Redis database addon
5. Configure build command: `pip install -r requirements.txt`
6. Configure run command: `gunicorn config.wsgi:application`
7. Deploy

### Option 3: AWS (EC2 + RDS + ElastiCache)

#### 1. Launch EC2 Instance
- Ubuntu 22.04 LTS
- t3.small or larger
- Configure security groups (80, 443, 22)

#### 2. SSH into instance and setup:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv postgresql-client nginx git

# Create user
sudo useradd -m -s /bin/bash lessonforge
sudo su - lessonforge

# Clone repository
git clone <your-repo-url> lessonforge
cd lessonforge

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt gunicorn

# Create .env file
nano .env
# Add all environment variables
```

#### 3. Configure PostgreSQL (RDS):
```bash
# In AWS Console:
- Create RDS PostgreSQL instance
- Note connection details
- Update DATABASE_URL in .env
```

#### 4. Configure Redis (ElastiCache):
```bash
# In AWS Console:
- Create ElastiCache Redis cluster
- Note endpoint
- Update REDIS_URL in .env
```

#### 5. Run migrations:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

#### 6. Configure Gunicorn:
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add:
```ini
[Unit]
Description=gunicorn daemon for LessonForge
After=network.target

[Service]
User=lessonforge
Group=lessonforge
WorkingDirectory=/home/lessonforge/lessonforge
ExecStart=/home/lessonforge/lessonforge/venv/bin/gunicorn \
          --workers 4 \
          --bind unix:/home/lessonforge/lessonforge/gunicorn.sock \
          --timeout 120 \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start Gunicorn:
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

#### 7. Configure Nginx:
```bash
sudo nano /etc/nginx/sites-available/lessonforge
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/lessonforge/lessonforge/staticfiles/;
    }
    
    location /media/ {
        alias /home/lessonforge/lessonforge/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/lessonforge/lessonforge/gunicorn.sock;
        proxy_read_timeout 120s;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/lessonforge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 8. Configure SSL (Let's Encrypt):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 9. Configure Celery:
```bash
sudo nano /etc/systemd/system/celery.service
```

Add:
```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
User=lessonforge
Group=lessonforge
WorkingDirectory=/home/lessonforge/lessonforge
ExecStart=/home/lessonforge/lessonforge/venv/bin/celery -A config worker -l info

[Install]
WantedBy=multi-user.target
```

Start Celery:
```bash
sudo systemctl start celery
sudo systemctl enable celery
```

### Option 4: Docker Deployment

```bash
# Build image
docker build -t lessonforge:latest .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Or run manually
docker run -d \
  --name lessonforge \
  -p 8000:8000 \
  --env-file .env \
  lessonforge:latest
```

## Post-Deployment

### 1. Verify deployment:
- [ ] Homepage loads
- [ ] Registration works
- [ ] Login works
- [ ] Lesson plan generation works
- [ ] PDF download works
- [ ] Email sending works
- [ ] Payment flow works

### 2. Set up monitoring:
```bash
# Check logs
heroku logs --tail  # For Heroku
sudo journalctl -u gunicorn -f  # For Ubuntu/systemd
```

### 3. Configure backups:
```bash
# PostgreSQL backup script
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Setup cron for daily backups
crontab -e
# Add: 0 2 * * * /path/to/backup-script.sh
```

### 4. Performance optimization:
- [ ] Enable caching
- [ ] Configure CDN for static files
- [ ] Optimize database queries
- [ ] Set up load balancing (if needed)

## Maintenance

### Regular Tasks:
1. **Daily**: Check error logs
2. **Weekly**: Review usage metrics
3. **Monthly**: Update dependencies
4. **Quarterly**: Security audit

### Update Procedure:
```bash
# Pull latest code
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart celery
```

## Troubleshooting

### Common Issues:

**Static files not loading:**
```bash
python manage.py collectstatic --clear
sudo systemctl restart nginx
```

**Database connection error:**
```bash
# Check DATABASE_URL is correct
echo $DATABASE_URL
# Test connection
psql $DATABASE_URL
```

**Celery not processing tasks:**
```bash
sudo systemctl status celery
sudo journalctl -u celery -n 50
```

**High memory usage:**
```bash
# Check processes
htop
# Reduce Gunicorn workers if needed
```

## Support

For deployment issues:
- Email: support@lessonforge.com
- Documentation: https://docs.lessonforge.com
- GitHub Issues: https://github.com/yourusername/lessonforge/issues
