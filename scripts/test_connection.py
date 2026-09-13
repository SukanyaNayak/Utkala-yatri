"""
Quick standalone check that MONGODB_URI in .env is correct and reachable.

Run from the project root (with your venv activated):
    python scripts/test_connection.py
"""

import sys
import os

# Allow running this script directly from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.mongodb_service import test_connection

if __name__ == "__main__":
    success, message = test_connection()
    print(message)
    sys.exit(0 if success else 1)