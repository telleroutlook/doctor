# 数据库配置
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "username": "root",
    "password": "password",
    "database": "msd_manuals",
    "charset": "utf8mb4",
    "pool_size": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": true
}

# SQLite备用配置（用于测试）
SQLITE_CONFIG = {
    "database": "msd_manuals.db",
    "timeout": 30,
    "check_same_thread": False
}

class DatabaseManager:
    def __init__(self, config_type="mysql"):
        self.config_type = config_type
        if config_type == "mysql":
            import mysql.connector
            self.config = DATABASE_CONFIG
        else:
            import sqlite3
            self.config = SQLITE_CONFIG
    
    def get_connection(self):
        if self.config_type == "mysql":
            import mysql.connector
            return mysql.connector.connect(**self.config)
        else:
            import sqlite3
            return sqlite3.connect(self.config["database"])
