import os

from flask import Flask
from flask import Blueprint

import json
import importlib

plugin_bp = Blueprint('plugin', __name__, url_prefix='/plugin')

PLUGIN_ENABLE_FOLDERS = []
PLUGIN_IMPORTLIB = []


def register_plugin(app: Flask):
    """
    获取所有插件并加载
    """
    global PLUGIN_ENABLE_FOLDERS
    app.register_blueprint(plugin_bp)
    # 载入插件过程
    # plugin_folder 配置的是插件的文件夹名
    PLUGIN_ENABLE_FOLDERS = app.config['PLUGIN_ENABLE_FOLDERS']

    for plugin_folder in PLUGIN_ENABLE_FOLDERS:

        plugin_info = {
            'plugin_name': plugin_folder
        }

        try:
            if os.path.exists("plugins/" + plugin_folder + "/__init__.json"):
                with open("plugins/" + plugin_folder + "/__init__.json", "r", encoding='utf-8') as f:
                    plugin_info = json.loads(f.read())

            # 将插件全部载入
            PLUGIN_IMPORTLIB.append(importlib.import_module('plugins.' + plugin_folder))

            print(f" * Plugin: Loaded plugin: {plugin_info['plugin_name']} .")
        except BaseException as e:
            info = f" * Plugin: Crash a error when loading {plugin_info['plugin_name'] if len(plugin_info) != 0 else 'plugin'} :" + "\n"
            app.logger.error(info)
            app.logger.exception(e)


def broadcast_execute(app: Flask, function_name):
    for plugin in PLUGIN_IMPORTLIB:

        try:
            # 初始化完成事件
            try:
                getattr(plugin, function_name)(app)
            except AttributeError:  # 没有插件启用事件就不调用
                pass

        except BaseException as e:
            app.logger.exception(e)

    if function_name == 'event_finish':
        with app.app_context():
            broadcast_execute(app, 'event_context')