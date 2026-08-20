"""Database Seeder Script."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from pms_app.extensions import db

def seed():
    print("Seeding database...")
    # TODO: Implement

if __name__ == "__main__":
    with app.app_context():
        seed()
