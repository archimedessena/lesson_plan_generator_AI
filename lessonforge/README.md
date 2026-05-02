# LessonForge - AI-Powered Lesson Planning Platform

LessonForge is a production-ready SaaS application that helps Ghanaian educators generate comprehensive, curriculum-aligned lesson plans using AI. Built with Django and powered by Anthropic's Claude AI.

## 🚀 Features

- **AI-Powered Generation**: Create complete lesson plans in minutes using Claude AI
- **Curriculum Support**: Full support for Cambridge IGCSE, A-Level, and WASSCE
- **PDF Export**: Download professional PDF lesson plans
- **Template Library**: Pre-built templates for different subjects and lesson types
- **User Management**: Complete authentication and profile system
- **Subscription System**: Tiered pricing with Paystack integration
- **Usage Tracking**: Monitor API usage and costs
- **Responsive Design**: Works on desktop, tablet, and mobile

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+ (SQLite for development)
- Redis 7+ (for caching and Celery)
- Anthropic API key

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd lessonforge
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment setup

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ANTHROPIC_API_KEY=your-api-key-here
DATABASE_URL=sqlite:///db.sqlite3  # Or PostgreSQL URL
REDIS_URL=redis://localhost:6379/0
```

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create superuser

```bash
python manage.py createsuperuser
```

### 7. Load initial data (optional)

```bash
python manage.py loaddata fixtures/templates.json
```

### 8. Run development server

```bash
python manage.py runserver
```

Visit http://localhost:8000

## 🐳 Docker Setup

### Quick Start with Docker Compose

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Visit http://localhost:8000
```

### Production Docker Build

```bash
docker build -t lessonforge:latest .
docker run -p 8000:8000 --env-file .env lessonforge:latest
```

## 🔧 Configuration

### Database Configuration

**Development (SQLite):**
```env
DATABASE_URL=sqlite:///db.sqlite3
```

**Production (PostgreSQL):**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/lessonforge
```

### Redis Configuration

```env
REDIS_URL=redis://localhost:6379/0
```

### Anthropic API

Get your API key from https://console.anthropic.com/

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Paystack Integration

1. Sign up at https://paystack.com/
2. Get your API keys from the dashboard
3. Add to `.env`:

```env
PAYSTACK_PUBLIC_KEY=pk_test_...
PAYSTACK_SECRET_KEY=sk_test_...
```

### Email Configuration

**Development (Console):**
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Production (Mailgun):**
```env
ANYMAIL_SERVICE=mailgun
MAILGUN_API_KEY=your-key
MAILGUN_SENDER_DOMAIN=mg.yourdomain.com
EMAIL_BACKEND=anymail.backends.mailgun.EmailBackend
```

## 🚀 Deployment

### Heroku Deployment

1. Install Heroku CLI
2. Create app:

```bash
heroku create lessonforge
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini
```

3. Set environment variables:

```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ANTHROPIC_API_KEY=your-api-key
heroku config:set DEBUG=False
```

4. Deploy:

```bash
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### DigitalOcean App Platform

1. Connect GitHub repository
2. Set environment variables in dashboard
3. Add PostgreSQL and Redis databases
4. Deploy

### AWS/VPS Deployment

1. Set up server (Ubuntu 22.04 recommended)
2. Install dependencies:

```bash
sudo apt update
sudo apt install python3-pip python3-venv postgresql postgresql-contrib redis-server nginx
```

3. Clone repository and configure
4. Set up Gunicorn service:

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

5. Configure Nginx reverse proxy
6. Set up SSL with Let's Encrypt

## 📊 Background Tasks

Start Celery worker for background tasks:

```bash
celery -A config worker -l info
```

Start Celery beat for scheduled tasks:

```bash
celery -A config beat -l info
```

## 🧪 Testing

Run tests:

```bash
python manage.py test
```

With coverage:

```bash
coverage run --source='.' manage.py test
coverage report
```

## 📈 Monitoring

### Sentry Integration

Add to `.env`:

```env
SENTRY_DSN=your-sentry-dsn
```

### Application Logs

Logs are stored in `/logs/lessonforge.log`

View live logs:

```bash
tail -f logs/lessonforge.log
```

## 🔒 Security Checklist

- [ ] Change SECRET_KEY in production
- [ ] Set DEBUG=False in production
- [ ] Configure ALLOWED_HOSTS
- [ ] Use HTTPS (SSL certificate)
- [ ] Set up CSRF and CORS properly
- [ ] Use strong database passwords
- [ ] Enable rate limiting
- [ ] Set up security headers
- [ ] Regular dependency updates
- [ ] Database backups

## 📝 API Documentation

API endpoints available at `/api/`:

- `/api/lesson-plans/` - List/create lesson plans
- `/api/templates/` - List templates
- `/api/auth/login/` - User login
- `/api/auth/register/` - User registration

Full API documentation: http://localhost:8000/api/docs/

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🆘 Support

- Email: support@lessonforge.com
- Documentation: https://docs.lessonforge.com
- Issues: https://github.com/yourusername/lessonforge/issues

## 🙏 Acknowledgments

- Anthropic Claude AI for lesson plan generation
- Django framework and community
- Bootstrap for UI components
- Ghanaian educators for feedback and testing

## 📱 Contact

For questions or support, reach out to:
- Email: archimedes@lessonforge.com
- GitHub: @yourusername

---

Built with ❤️ for Ghanaian educators
