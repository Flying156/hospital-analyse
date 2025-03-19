import datetime

from flask.cli import AppGroup

from ..models import Gift
from applications.models import Power
from applications.extensions import db

gift_cli = AppGroup("gift")

now_time = datetime.datetime.now()

powerdata = [
    Power(
        name='兑换码添加',
        type='2',
        code='system:gift:add',
        url='',
        open_type='',
        parent_id='60',
        icon='',
        sort=0,
        create_time=now_time,
        enable=1
    ), Power(
        name='兑换码删除',
        type='2',
        code='system:gift:remove',
        url='',
        open_type='',
        parent_id='60',
        icon='',
        sort=0,
        create_time=now_time,
        enable=1
    ), Power(
        name='兑换码编辑',
        type='2',
        code='system:gift:edit',
        url='',
        open_type='',
        parent_id='60',
        icon='',
        sort=0,
        create_time=now_time,
        enable=1
    )
]

giftdata = [
    Gift(
        id=0,
        key='myTestCode',
        content='8折优惠',
        enable=1,
        used=0,
        create_at=now_time
    ),
    Gift(
        id=1,
        key='DisableCode',
        content='1折优惠',
        enable=0,
        used=0,
        create_at=now_time
    )
]


@gift_cli.command("init")
def init_db():
    print("存入兑换码管理页面数据")

    top_power = Power(
        name='兑换码管理',
        type='1',
        code='system:gift:main',
        url='/system/gift/',
        open_type='_iframe',
        parent_id='1',
        icon='layui-icon layui-icon layui-icon layui-icon-diamond',
        sort=8,
        create_time=now_time,
        enable=1
    )

    db.session.add(top_power)
    db.session.commit()  # 提交了才有 id

    for i in range(len(powerdata)):
        powerdata[i].parent_id = top_power.id

    db.session.add_all(powerdata)

    db.session.add_all(giftdata)
    db.session.commit()
