from sqlalchemy import and_, func
from applications.extensions import db


class ModelFilter:
    """
    ORM 多条件查询构造器，支持多种查询条件组合，自动转义特殊字符防止SQL注入。

    示例：
        mf = ModelFilter()
        mf.exact('name', 'John')
        mf.vague('email', 'example.com')
        query = User.query.filter(mf.get_filter(User))
    """
    filter_field = {}  # 存储字段过滤条件
    filter_list = []  # 存储最终的过滤条件列表

    # 查询类型常量
    type_exact = "exact"  # 精确匹配
    type_neq = "neq"  # 不等于
    type_greater = "greater"  # 大于
    type_less = "less"  # 小于
    type_vague = "vague"  # 模糊匹配
    type_contains = "contains"  # 包含
    type_between = "between"  # 范围查询

    def __init__(self):
        """初始化过滤条件存储字典和列表。"""
        self.filter_field = {}
        self.filter_list = []

    @staticmethod
    def escape_like(value: str, escape_char: str = '\\') -> str:
        """
        转义LIKE查询中的特殊字符（%, _ 和转义字符本身）

        :param value: 需要转义的原始字符串
        :param escape_char: 转义字符（默认反斜杠）
        :return: 转义后的安全字符串
        """
        return (
            value.replace(escape_char, escape_char * 2)
            .replace('%', escape_char + '%')
            .replace('_', escape_char + '_')
        )

    def exact(self, field_name, value):
        """
        添加精确匹配条件（自动处理字符串类型参数）

        :param field_name: 模型字段名称
        :param value: 匹配的值（自动过滤空字符串）
        """
        if value is not None and value != '':
            # 字符串类型自动调用escape_like（防止特殊字符影响精确匹配）
            processed_value = self.escape_like(str(value)) if isinstance(value, str) else value
            self.filter_field[field_name] = {"data": processed_value, "type": self.type_exact}

    def neq(self, field_name, value):
        """
        添加不等于条件（自动处理字符串类型参数）

        :param field_name: 模型字段名称
        :param value: 不匹配的值（自动过滤空字符串）
        """
        if value is not None and value != '':
            # 字符串类型自动调用escape_like
            processed_value = self.escape_like(str(value)) if isinstance(value, str) else value
            self.filter_field[field_name] = {"data": processed_value, "type": self.type_neq}

    def greater(self, field_name, value):
        """
        添加大于条件（数值/日期比较）

        :param field_name: 模型字段名称
        :param value: 比较的数值/日期
        """
        if value is not None and value != '':
            self.filter_field[field_name] = {"data": value, "type": self.type_greater}

    def less(self, field_name, value):
        """
        添加小于条件（数值/日期比较）

        :param field_name: 模型字段名称
        :param value: 比较的数值/日期
        """
        if value is not None and value != '':
            self.filter_field[field_name] = {"data": value, "type": self.type_less}

    def vague(self, field_name, value: str):
        """
        添加安全模糊匹配（自动转义特殊字符，左右加%）

        :param field_name: 模型字段名称
        :param value: 需要模糊匹配的字符串（自动过滤空值）
        """
        if value and value != '':
            escaped_value = self.escape_like(value)
            self.filter_field[field_name] = {"data": f'%{escaped_value}%', "type": self.type_vague}

    def left_vague(self, field_name, value: str):
        """
        添加安全左模糊匹配（自动转义特殊字符，左侧加%）

        :param field_name: 模型字段名称
        :param value: 需要左模糊匹配的字符串
        """
        if value and value != '':
            escaped_value = self.escape_like(value)
            self.filter_field[field_name] = {"data": f'%{escaped_value}', "type": self.type_vague}

    def right_vague(self, field_name, value: str):
        """
        添加安全右模糊匹配（自动转义特殊字符，右侧加%）

        :param field_name: 模型字段名称
        :param value: 需要右模糊匹配的字符串
        """
        if value and value != '':
            escaped_value = self.escape_like(value)
            self.filter_field[field_name] = {"data": f'{escaped_value}%', "type": self.type_vague}

    def contains(self, field_name, value: str):
        """
        添加安全包含条件（自动转义特殊字符，等效于vague）

        :param field_name: 模型字段名称
        :param value: 需要包含的字符串
        """
        if value and value != '':
            escaped_value = self.escape_like(value)
            self.filter_field[field_name] = {"data": f'%{escaped_value}%', "type": self.type_contains}

    def between(self, field_name, value1, value2):
        """
        添加范围查询条件（自动过滤无效值）

        :param field_name: 模型字段名称
        :param value1: 范围起始值
        :param value2: 范围结束值
        """
        if all([v is not None and v != '' for v in [value1, value2]]):
            self.filter_field[field_name] = {"data": [value1, value2], "type": self.type_between}

    def get_filter(self, model: db.Model):
        """
        生成安全的SQLAlchemy过滤条件

        :param model: SQLAlchemy 模型类
        :return: 组合后的过滤条件（使用and_连接）
        """
        for k, v in self.filter_field.items():
            field = getattr(model, k)
            data = v.get("data")
            query_type = v.get("type")

            if query_type == self.type_vague:
                self.filter_list.append(field.like(data, escape='\\'))
            elif query_type == self.type_contains:
                self.filter_list.append(field.like(data, escape='\\'))
            elif query_type == self.type_exact:
                self.filter_list.append(field == data)
            elif query_type == self.type_neq:
                self.filter_list.append(field != data)
            elif query_type == self.type_greater:
                self.filter_list.append(field > data)
            elif query_type == self.type_less:
                self.filter_list.append(field < data)
            elif query_type == self.type_between:
                self.filter_list.append(field.between(data[0], data[1]))

        return and_(*self.filter_list)