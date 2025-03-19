"""
初始化插件
"""
import os
import logging
from flask import Flask, request

# 获取插件所在的目录（结尾没有分割符号）
dir_path = os.path.dirname(__file__).replace("\\", "/")
folder_name = dir_path[dir_path.rfind("/") + 1:]  # 插件文件夹名称


def event_init(app: Flask):
    """初始化完成时会调用这里"""

    # 更改IP地址，只有在最新版的flask中才能生效
    @app.before_request
    def before_request():
        request.remote_addr = get_user_ip(request)


def get_user_ip(request):
    """获取用户真实IP"""
    if 'HTTP_X_FORWARDED_FOR' in request.headers:
        arr = request.headers['HTTP_X_FORWARDED_FOR'].strip().split(",")
        i = 0
        while i < len(arr):
            if arr[i].find("unknown") != -1:
                del arr[i]
            else:
                i += 1
        if len(arr) != 0:
            return arr[0].strip()
    elif 'HTTP_CLIENT_IP' in request.headers:
        return request.headers['HTTP_CLIENT_IP']
    elif 'REMOTE_ADDR' in request.headers:
        return request.headers['REMOTE_ADDR']
    elif 'X-Forwarded-For' in request.headers:
        return request.headers['X-Forwarded-For']
    return request.remote_addr
