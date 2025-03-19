import datetime
from applications.extensions import db


class Gift(db.Model):
    __tablename__ = 'admin_gift'
    id = db.Column(db.Integer, primary_key=True, comment="唯一ID")
    key = db.Column(db.String(50), comment="兑换码")
    content = db.Column(db.String(), comment="具体内容")
    enable = db.Column(db.Integer, default=0, comment='是否启用')
    used = db.Column(db.Integer, default=0, comment='是否已经使用')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')