import datetime
from marshmallow import Schema
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from applications.extensions import db, ma


class LogicalDeleteMixin(object):
    """
    逻辑删除混入类，为模型提供软删除功能。

    示例：
        class Test(db.Model, LogicalDeleteMixin):
            __tablename__ = 'admin_test'
            id = db.Column(db.Integer, primary_key=True, comment='角色ID')

        # 软删除
        Test.query.filter_by(id=1).soft_delete()

        # 查询所有未删除的记录
        Test.query.logic_all()
    """
    create_at = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间')
    delete_at = db.Column(db.DateTime, comment='删除时间')


def auto_model_jsonify(data, model: db.Model):
    """
    自动序列化模型数据为 JSON 格式，无需手动定义 Schema。

    示例：
        power_data = curd.auto_model_jsonify(model=Dept, data=dept)

    :param data: 需要序列化的 SQLAlchemy 查询结果。
    :param model: SQLAlchemy 模型类。
    :return: 返回序列化后的 JSON 数据。
    """
    def get_model():
        return model

    class AutoSchema(SQLAlchemyAutoSchema):
        class Meta(Schema):
            model = get_model()
            include_fk = True  # 包含外键
            include_relationships = True  # 包含关联关系
            load_instance = True  # 反序列化时加载为模型实例

    common_schema = AutoSchema(many=True)  # 支持序列化多个对象
    output = common_schema.dump(data)
    return output


def model_to_dicts(schema: ma.Schema, data):
    """
    使用指定的 Schema 序列化 SQLAlchemy 查询结果。

    :param schema: Marshmallow Schema 类。
    :param data: SQLAlchemy 查询结果。
    :return: 返回序列化后的数据，返回字典。
    """
    common_schema = schema(many=True)  # 支持序列化多个对象
    output = common_schema.dump(data)
    return output


def get_one_by_id(model: db.Model, id):
    """
    根据 ID 查询单个记录。

    :param model: SQLAlchemy 模型类。
    :param id: 记录的主键 ID。
    :return: 返回查询到的记录，如果未找到则返回 None。
    """
    return model.query.filter_by(id=id).first()


def delete_one_by_id(model: db.Model, id):
    """
    根据 ID 删除单个记录。

    :param model: SQLAlchemy 模型类。
    :param id: 记录的主键 ID。
    :return: 返回删除操作影响的行数。
    """
    r = model.query.filter_by(id=id).delete()
    db.session.commit()
    return r


def enable_status(model: db.Model, id):
    """
    启用指定 ID 的记录。

    :param model: SQLAlchemy 模型类。
    :param id: 记录的主键 ID。
    :return: 如果操作成功返回 True，否则返回 False。
    """
    enable = 1
    role = model.query.filter_by(id=id).update({"enable": enable})
    if role:
        db.session.commit()
        return True
    return False


def disable_status(model: db.Model, id):
    """
    停用指定 ID 的记录。

    :param model: SQLAlchemy 模型类。
    :param id: 记录的主键 ID。
    :return: 如果操作成功返回 True，否则返回 False。
    """
    enable = 0
    role = model.query.filter_by(id=id).update({"enable": enable})
    if role:
        db.session.commit()
        return True
    return False