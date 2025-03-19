import os

from flask import Blueprint, request, render_template

from ..models import Gift
from ..schemas import GiftSchema
from applications.extensions import db

from applications.common.helper import ModelFilter
from applications.common.curd import enable_status, disable_status, delete_one_by_id, get_one_by_id
from applications.common.utils.http import table_api, success_api, fail_api
from applications.common.utils.rights import authorize

# 获取插件所在的目录（结尾没有分割符号）
dir_path = os.path.dirname(__file__).replace("\\", "/")

bp = Blueprint('gift', __name__, url_prefix='/system/gift',
               template_folder=dir_path + '/../templates')


@bp.get('/')
@authorize("system:gift:main")
def index():
    return render_template('system/gift/main.html')


@bp.get('/add')
@authorize("system:gift:main")
def add():
    return render_template('system/gift/add.html')


@bp.get('/data')
@authorize("system:gift:main")
def data():
    key = request.args.get('key', type=str)

    mf = ModelFilter()
    if key:
        mf.vague('key', key)  # 模糊查询

    data, total, page, limit = db.session.query(Gift).filter(mf.get_filter(Gift)).layui_paginate_json(GiftSchema)

    return table_api(
        data=data,
        count=total,
        limit=limit
    )


@bp.put('/enable')
@authorize("system:gift:edit")
def enable_api():
    data = request.get_json(force=True)

    if enable_status(Gift, data.get('id')):
        return success_api(msg="启用成功")

    return success_api(msg="启用失败")


@bp.put('/disable')
@authorize("system:gift:edit")
def disable_api():
    req_json = request.get_json(force=True)

    if disable_status(Gift, req_json.get('id')):
        return success_api(msg="禁用成功")

    return success_api(msg="禁用失败")


@bp.delete('/remove/<int:_id>')
@authorize("system:gift:remove")
def remove_api(_id):
    if delete_one_by_id(Gift, _id):
        return success_api(msg="删除成功")

    return success_api(msg="删除失败")


@bp.post('/save')
@authorize("system:gift:add", log=True)
def save():
    req_json = request.get_json(force=True)

    data = {
        'key': req_json.get('key'),
        'content': req_json.get('content'),
        'enable': req_json.get('enable'),
        'used': 0
    }

    # 效验参数
    if not all(list(data.keys())):
        return fail_api(msg="参数不全")

    if not data['enable'].isdigit():
        return fail_api(msg="参数 enable 错误")

    try:
        db.session.add(Gift(**data))
        db.session.commit()
        return success_api(msg="添加成功")
    except Exception as e:
        return fail_api(msg="添加失败")


@bp.get('/edit/<int:_id>')
@authorize("system:gift:edit", log=True)
def edit(_id):
    gift = get_one_by_id(Gift, _id)
    return render_template('system/gift/edit.html', gift=gift)


@bp.post('/update')
@authorize("system:gift:edit", log=True)
def update():
    req_json = request.get_json(force=True)

    _id = req_json.get('id')

    data = {
        'key': req_json.get('key'),
        'content': req_json.get('content'),
        'enable': req_json.get('enable'),
        'used': 0
    }

    # 效验参数
    if not all(list(data.keys())):
        return fail_api(msg="参数不全")

    if not data['enable'].isdigit():
        return fail_api(msg="参数 enable 错误")

    try:
        db.session.query(Gift).filter(Gift.id == _id).update(data)
        db.session.commit()
        return success_api(msg="编辑成功")
    except Exception as e:
        return fail_api(msg="编辑失败")
