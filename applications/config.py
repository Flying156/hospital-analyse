import logging
from datetime import timedelta


class BaseConfig:
    # 超级管理员账号
    SUPERADMIN = 'admin'

    # 系统名称
    SYSTEM_NAME = '医疗资源统计与分析可视化系统'

    # 主题面板的链接列表配置
    SYSTEM_PANEL_LINKS = [
        {
            "icon": "layui-icon layui-icon-auz",
            "title": "官方网站",
            "href": "http://www.pearadmin.com"
        },
        {
            "icon": "layui-icon layui-icon-auz",
            "title": "开发文档",
            "href": "http://www.pearadmin.com"
        },
        {
            "icon": "layui-icon layui-icon-auz",
            "title": "开源地址",
            "href": "https://gitee.com/Jmysy/Pear-Admin-Layui"
        }
    ]


    # JSON 配置
    JSON_AS_ASCII = False


    SQLALCHEMY_DATABASE_URI="mysql+pymysql://root:123456@127.0.0.1:3306/hospital"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 数据库的配置信息
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///../pear.db'

    # config.py
    REDIS_URL = "redis://:localhost:6379/0"

    # 默认日志等级
    LOG_LEVEL = logging.WARN

    HIVE_HOST="localhost"
    HIVE_PORT="10000"
    HIVE_USER="mike"
    HIVE_DATABASE="default"


    # 插件配置，填写插件的文件名名称，默认不启用插件。
    PLUGIN_ENABLE_FOLDERS = []

    # Session 设置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    SESSION_TYPE = "filesystem"  # 默认使用文件系统来保存会话
    SESSION_PERMANENT = False  # 会话是否持久化
    SESSION_USE_SIGNER = True  # 是否对发送到浏览器上 session 的 cookie 值进行加密

    SECRET_KEY = "pear-system-flask"
