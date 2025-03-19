import logging
from datetime import timedelta


class BaseConfig:
    # 超级管理员账号
    SUPERADMIN = 'admin'

    # 系统名称
    SYSTEM_NAME = 'Pear Admin'

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

    # 配置多个数据库连接的连接串写法示例
    # HOSTNAME: 指数据库的IP地址、USERNAME：指数据库登录的用户名、PASSWORD：指数据库登录密码、PORT：指数据库开放的端口、DATABASE：指需要连接的数据库名称
    # MSSQL:    f"mssql+pymssql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=cp936"
    # MySQL:    f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"
    # Oracle:   f"oracle+cx_oracle://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}"
    # SQLite    "sqlite:/// database.db"
    # Postgres f"postgresql+psycopg2://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}"
    # Oracle的第二种连接方式
    # dsnStr = cx_Oracle.makedsn({HOSTNAME}, 1521, service_name='orcl')
    # connect_str = "oracle://%s:%s@%s" % ('{USERNAME}', ' {PASSWORD}', dsnStr)

    #  在SQLALCHEMY_BINDS 中设置：'{数据库连接别名}': '{连接串}'
    # 最后在models的数据模型class中，在__tablename__前设置        __bind_key__ = '{数据库连接别名}'  即可，表示该数据模型不使用默认的数据库连接，改用“SQLALCHEMY_BINDS”中设置的其他数据库连接
    #  SQLALCHEMY_BINDS = {
    #    'testMySQL': 'mysql+pymysql://test:123456@192.168.1.1:3306/test?charset=utf8',
    #    'testMsSQL': 'mssql+pymssql://test:123456@192.168.1.1:1433/test?charset=cp936',
    #    'testOracle': 'oracle+cx_oracle://test:123456@192.168.1.1:1521/test',
    #    'testSQLite': 'sqlite:///database.db
    # }
    SQLALCHEMY_DATABASE_URI="mysql+pymysql://root:123456@127.0.0.1:3306/hospital"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 数据库的配置信息
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///../pear.db'

    # 默认日志等级
    LOG_LEVEL = logging.WARN


    # 插件配置，填写插件的文件名名称，默认不启用插件。
    PLUGIN_ENABLE_FOLDERS = []

    # Session 设置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    SESSION_TYPE = "filesystem"  # 默认使用文件系统来保存会话
    SESSION_PERMANENT = False  # 会话是否持久化
    SESSION_USE_SIGNER = True  # 是否对发送到浏览器上 session 的 cookie 值进行加密

    SECRET_KEY = "pear-system-flask"
