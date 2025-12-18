#!/bin/bash
# Simple run script for MediSheba (Flask) - adjust environment as needed
export FLASK_APP=app.py
export FLASK_ENV=development
python3 -m pip install -r requirements.txt
flask run --host=0.0.0.0 --port=5000
