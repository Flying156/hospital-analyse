from flask import Blueprint, session, redirect, url_for, render_template, request
from flask_login import current_user, login_user, login_required, logout_user

from applications.common.admin import get_captcha, login_log
from werkzeug.security import generate_password_hash
from applications.extensions import db
from applications.common.utils.http import fail_api, success_api
from applications.models import User, Role

bp = Blueprint('passport', __name__, url_prefix='/passport')


# 获取验证码
@bp.get('/getCaptcha')
def captcha():
    resp, code = get_captcha()
    session["code"] = code
    return resp


# 登录
@bp.get('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    return render_template('system/login.html')


# 登录
@bp.post('/login')
def login_post():
    req = request.form
    username = req.get('username')
    password = req.get('password')
    remember = bool(req.get('remember-me'))
    code = req.get('captcha').__str__().lower()

    if not username or not password or not code:
        return fail_api(msg="用户名或密码没有输入")
    s_code = session.get("code", None)
    session["code"] = None

    if not all([code, s_code]):
        return fail_api(msg="参数错误")

    if code != s_code:
        return fail_api(msg="验证码错误")
    user = User.query.filter_by(username=username).first()

    if not user:
        return fail_api(msg="不存在的用户")

    if user.enable == 0:
        return fail_api(msg="用户被暂停使用")

    if username == user.username and user.validate_password(password):
        # 登录
        login_user(user, remember=remember)
        # 记录登录日志
        login_log(request, uid=user.id, is_access=True)
        # 授权路由存入session
        role = current_user.role
        user_power = []
        for i in role:
            if i.enable == 0:
                continue
            for p in i.power:
                if p.enable == 0:
                    continue
                user_power.append(p.code)
        session['permissions'] = user_power
        # # 角色存入session
        # roles = []
        # for role in current_user.role.all():
        #     roles.append(role.id)
        # session['role'] = [roles]

        return success_api(msg="登录成功")

    login_log(request, uid=user.id, is_access=False)
    return fail_api(msg="用户名或密码错误")

@bp.get('/register')
def register():
    return render_template('system/register.html')

@bp.post('/register')
def register_post():
    req = request.form
    username = req.get('username')
    password = req.get('password')
    code = req.get('captcha').__str__().lower()
    if not username or not password or not code:
        return fail_api(msg="用户名或密码没有输入")
    s_code = session.get("code", None)
    session["code"] = None
    if not all([code, s_code]):
        return fail_api(msg="参数错误")

    if code != s_code:
        return fail_api(msg="验证码错误")
    user = User.query.filter_by(username=username).first()
    if user:
        return fail_api(msg="用户名已经存在")

    new_user = User(username=username, enable=1)
    new_user.set_password(password)
    try:
        role = Role.query.get(2)
        new_user.role.append(role)
        db.session.add(new_user)
        db.session.commit()
        login_log(request, uid=user.id, is_access=True)
        return success_api(msg="用户注册成功")
    except Exception as e:
        db.session.rollback()
        return fail_api(msg="注册失败")


# 退出登录
@bp.post('/logout')
@login_required
def logout():
    logout_user()

    if 'permissions' in session:
        session.pop('permissions')

    return success_api(msg="注销成功")
