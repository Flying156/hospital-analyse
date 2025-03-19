from io import BytesIO
from flask import make_response
from flask_login import current_user

from applications.common.utils.validate import str_escape
from applications.common.utils.captcha import vieCode
from applications.extensions import db
from applications.models import AdminLog


def get_captcha():
    """
    生成验证码图片及其对应的验证码字符串。

    :return: 返回验证码图片的响应对象和验证码字符串。
    """
    image, code = vieCode().GetCodeImage()
    code = ''.join(code).lower()
    out = BytesIO()
    image.save(out, 'png')
    out.seek(0)
    resp = make_response(out.read())
    resp.content_type = 'image/png'
    return resp, code


def normal_log(method, url, ip, user_agent, desc, uid, is_access):
    """
    记录通用日志信息到数据库。

    :param method: 请求方法（如 GET、POST）。
    :param url: 请求的 URL。
    :param ip: 客户端的 IP 地址。
    :param user_agent: 客户端的 User-Agent 信息。
    :param desc: 日志描述信息。
    :param uid: 用户 ID。
    :param is_access: 是否成功访问（True 或 False）。
    :return: 返回日志记录的 ID。
    """
    info = {
        'method': method,
        'url': url,
        'ip': ip,
        'user_agent': user_agent,
        'desc': desc,
        'uid': uid,
        'success': int(is_access)
    }
    log = AdminLog(
        url=info.get('url'),
        ip=info.get('ip'),
        user_agent=info.get('user_agent'),
        desc=info.get('desc'),
        uid=info.get('uid'),
        method=info.get('method'),
        success=info.get('success')
    )
    db.session.add(log)
    db.session.commit()
    return log.id


def login_log(request, uid, is_access):
    """
    记录用户登录日志。

    :param request: Flask 请求对象。
    :param uid: 用户 ID。
    :param is_access: 是否成功登录（True 或 False）。
    :return: 返回日志记录的 ID。
    """
    method = request.method
    url = request.path
    ip = request.remote_addr
    user_agent = str_escape(request.headers.get('User-Agent'))
    desc = str_escape(request.form.get('username'))
    return normal_log(method, url, ip, user_agent, desc, uid, is_access)


def admin_log(request, is_access, desc=None):
    """
    记录管理员操作日志。

    :param request: Flask 请求对象。
    :param is_access: 是否成功操作（True 或 False）。
    :param desc: 日志描述信息（可选）。如果未提供，则从请求数据中提取。
    :return: 返回日志记录的 ID。
    """
    method = request.method
    url = request.path
    ip = request.remote_addr
    user_agent = str_escape(request.headers.get('User-Agent'))
    request_data = request.json if request.headers.get('Content-Type') == 'application/json' else request.values
    if desc is None:
        desc = str_escape(str(dict(request_data)))
    return normal_log(method, url, ip, user_agent, desc, current_user.id, is_access)
