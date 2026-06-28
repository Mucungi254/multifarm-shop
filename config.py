import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    MYSQL_USER = os.environ.get('MYSQL_USER', 'avnadmin')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'defaultdb')

    # Determine the CA certificate path
    # Render uses /opt/render/project/src as the root
    # Locally, it's the project folder
    if os.environ.get('RENDER'):
        CA_CERT_PATH = "/opt/render/project/src/ca.pem"
    else:
        CA_CERT_PATH = Path(__file__).parent / "ca.pem"

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'connect_args': {
            'ssl': {
                'ca': str(CA_CERT_PATH)
            }
        }
    }