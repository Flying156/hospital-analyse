# app.py
from flask import Flask
from flask_redis import FlaskRedis

redis = FlaskRedis()
def init_redis(app: Flask):
    app.config['REDIS_URL'] = "redis://localhost:6379/0"
    redis.init_app(app)