from flask import Flask
from .init_sqlalchemy import db, ma, init_databases
from .init_login import init_login_manager
from .init_template_directives import init_template_directives
from .init_error_views import init_error_views
from .init_migrate import init_migrate
from .init_session import init_session
from .init_plugins import register_plugin, broadcast_execute
from .init_redis import init_redis


def init_plugs(app: Flask) -> None:
    # 注册插件
    register_plugin(app)
    broadcast_execute(app, 'event_begin')

    # 注册 Flask 功能
    init_login_manager(app)
    init_databases(app)
    init_migrate(app)
    init_session(app)
    init_redis(app)

    # 系统蓝图相关
    init_template_directives(app)
    init_error_views(app)
