from pyhive import hive
from flask import g
from applications.config import BaseConfig

class HiveConnection:
    @staticmethod
    def get_connection():
        if not hasattr(g, 'hive_conn'):
            g.hive_conn = hive.Connection(
                host=BaseConfig.HIVE_HOST,
                port=BaseConfig.HIVE_PORT,
                username=BaseConfig.HIVE_USER,
                database=BaseConfig.HIVE_DATABASE
            )
        return g.hive_conn
