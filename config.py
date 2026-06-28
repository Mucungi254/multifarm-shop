import os

class Config:
    SECRET_KEY = 'MediocrityIsTheEnemyOfGreatness'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''  # XAMPP default
    MYSQL_DB = 'multifarm_shop_db'
    MYSQL_CURSORCLASS = 'DictCursor'