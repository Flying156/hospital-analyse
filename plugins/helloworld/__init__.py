"""
初始化插件
"""
import os

from flask import Flask
from .main import helloworld_blueprint

from applications.models import Dept
from applications.common import curd
from applications.schemas import DeptSchema

# 获取插件所在的目录（结尾没有分割符号）
dir_path = os.path.dirname(__file__).replace("\\", "/")
folder_name = dir_path[dir_path.rfind("/") + 1:]  # 插件文件夹名称


def event_begin(app: Flask):  # 在项目所有功能注册之前调用
    print("所有功能初始化之前加载")


def event_init(app: Flask):
    """初始化完成时会调用这里"""
    print("初始插件初始化视图")
    app.register_blueprint(helloworld_blueprint)


def event_finish(app: Flask):  # 在项目所有功能注册之后调用（插件已经加载完毕）
    print("所有初始化完毕")


def event_context(app: Flask):  # Flask 初始化完成，等待第一个请求之前，等同于 with app.app_context():
    print("第一个请求来之前加载")

    # 数据库已经初始化完成，尝试读取
    dept = Dept.query.order_by(Dept.sort).all()
    power_data = curd.model_to_dicts(schema=DeptSchema, data=dept)

    # print(power_data)
