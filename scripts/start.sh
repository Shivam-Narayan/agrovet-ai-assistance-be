#!/bin/bash
# start.sh - Entry point for Linux/Mac environments

cd backend || exit

echo "Installing requirements..."
pip install -r requirements.txt

echo "Making migrations..."
python manage.py makemigrations agrovet account

echo "Applying migrations..."
python manage.py migrate

echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000
