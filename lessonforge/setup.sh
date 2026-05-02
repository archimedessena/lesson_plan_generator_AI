#!/bin/bash

# LessonForge Quick Setup Script
# This script sets up the development environment

set -e

echo "======================================"
echo "  LessonForge Development Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.11+ required. Found $python_version"
    exit 1
fi
echo "✓ Python $python_version detected"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ Pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your configuration:"
    echo "   - SECRET_KEY (generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - Other API keys as needed"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p media/lesson_plans
mkdir -p media/profile_pictures
mkdir -p staticfiles
mkdir -p logs
echo "✓ Directories created"
echo ""

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput
echo "✓ Migrations completed"
echo ""

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "✓ Static files collected"
echo ""

# Create superuser
echo "======================================"
echo "  Create Superuser Account"
echo "======================================"
echo ""
echo "Please create an admin account:"
python manage.py createsuperuser
echo ""

# Load initial data (optional)
read -p "Load sample templates? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "fixtures/templates.json" ]; then
        python manage.py loaddata fixtures/templates.json
        echo "✓ Sample templates loaded"
    else
        echo "⚠️  fixtures/templates.json not found, skipping..."
    fi
fi
echo ""

# Success message
echo "======================================"
echo "  Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Start the development server:"
echo "   python manage.py runserver"
echo ""
echo "3. (Optional) Start Celery worker in another terminal:"
echo "   celery -A config worker -l info"
echo ""
echo "4. Visit http://localhost:8000"
echo ""
echo "Admin panel: http://localhost:8000/admin"
echo ""
echo "Happy coding!"
echo ""
