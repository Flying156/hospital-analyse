from flask import jsonify


def success_api(msg: str = "成功"):
    """
    返回成功的 API 响应。

    :param msg: 成功消息内容，默认为 "成功"。
    :return: 返回 JSON 格式的响应，包含 `success` 和 `msg` 字段。
    """
    return jsonify(success=True, msg=msg)


def fail_api(msg: str = "失败"):
    """
    返回失败的 API 响应。

    :param msg: 失败消息内容，默认为 "失败"。
    :return: 返回 JSON 格式的响应，包含 `success` 和 `msg` 字段。
    """
    return jsonify(success=False, msg=msg)


def table_api(msg: str = "", count=0, data=None, limit=10):
    """
    返回动态表格渲染所需的 API 响应。

    :param msg: 响应消息内容，默认为空字符串。
    :param count: 数据总数，默认为 0。
    :param data: 表格数据，默认为 None。
    :param limit: 每页数据条数，默认为 10。
    :return: 返回 JSON 格式的响应，包含 `msg`、`code`、`data`、`count` 和 `limit` 字段。
    """
    res = {
        'msg': msg,
        'code': 0,
        'data': data,
        'count': count,
        'limit': limit
    }
    return jsonify(res)