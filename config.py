import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    # MySQL credentials (from environment variables)
    MYSQL_USER = os.environ.get('MYSQL_USER', 'avnadmin')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'defaultdb')

    # Build SQLAlchemy connection string with SSL (for Aiven)
    # SSL CA path for Render (Linux) – /etc/ssl/certs/ca-certificates.crt
    # If that fails, you can download the CA cert from Aiven and reference it.
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        "?ssl_ca=/etc/ssl/certs/ca-certificates.crt"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }