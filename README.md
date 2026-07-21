# InterviewAI Pro - AI-Powered Mock Interview Platform

## Overview
A production-ready AI mock interview platform that helps users practice interviews using voice interactions and real-time feedback powered by Google Gemini.

## Quick Start
1. Create virtual environment: `python -m venv venv`
2. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
3. Install dependencies: `pip install -r requirements.txt`
4. Copy config template: `copy .env.example .env` (or rename it)
5. Edit `.env`:
   - Set `FLASK_SECRET_KEY` to a random string.
   - Generate `ENCRYPTION_KEY` using: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
6. Run the application: `python run.py`
7. Open http://localhost:5000 in your browser.

Note: The database is created automatically on the first run.

## Features
- AI-powered interviews with Gemini
- Voice-driven practice with Web Speech API
- Resume parsing and analysis
- Company-specific preparation modes
- Real-time feedback and scoring
- Progress tracking, dashboards, and gamification
- Progressive Web App (PWA) support

## Tech Stack
Flask, SQLAlchemy, Google Gemini API, Bootstrap 5, Vanilla JavaScript, Web Speech API.
