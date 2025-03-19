from applications.view.system import register_system_bps
from applications.extensions.init_plugins import broadcast_execute


def init_bps(app):
    register_system_bps(app)

    # 插件初始化函数
    broadcast_execute(app, 'event_init')
