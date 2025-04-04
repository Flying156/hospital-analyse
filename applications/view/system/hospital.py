from flask import Flask, g
from flask import Blueprint, session, redirect, url_for, render_template, request
from flask_login import login_required

from applications.common.utils.http import table_api
from applications.common.utils.rights import authorize
from applications.common.utils.validate import str_escape
from applications.extensions.init_hive import HiveConnection

bp = Blueprint('hospital', __name__, url_prefix='/hospital')


@bp.get('/')
@authorize("system:hospital:main")
def main():
    return render_template('system/hospital/main.html')


# 在每个请求开始时创建连接
@bp.before_request
def before_request():
    g.conn = HiveConnection.get_connection()
    g.cursor = g.conn.cursor()

# 在请求结束时关闭连接
@bp.teardown_request
def teardown_request(exception):
    if hasattr(g, 'cursor'):
        g.cursor.close()
    if hasattr(g, 'conn'):
        g.conn.close()

@bp.route('/data', methods=['GET'])
@login_required
def get_hospitals():
    city = str_escape(request.args.get('city', ''))
    level = str_escape(request.args.get('level', ''))
    hospital_type = str_escape(request.args.get('hospital_type', ''))
    ownership = str_escape(request.args.get('ownership', ''))
    page = request.args.get('page', default=0, type=int)
    limit = request.args.get('limit', default=10, type=int)
    # 构建 SQL 语句
    query = """
        SELECT city, hospital_level, hospital_name, address, ownership, hospital_type, departments
        FROM hospitals WHERE 1=1
    """
    count_query = "SELECT COUNT(*) FROM hospitals WHERE 1=1"
    params = []
    count_params = []

    # 动态添加过滤条件
    if city:
        query += " AND city = %s"
        count_query += " AND city = %s"
        params.append(city)
        count_params.append(city)

    if level:
        query += " AND hospital_level = %s"
        count_query += " AND hospital_level = %s"
        params.append(level)
        count_params.append(level)

    if hospital_type:
        query += " AND hospital_type = %s"
        count_query += " AND hospital_type = %s"
        params.append(hospital_type)
        count_params.append(hospital_type)

    if ownership:
        query += " AND ownership = %s"
        count_query += " AND ownership = %s"
        params.append(ownership)
        count_params.append(ownership)

    # 先执行总数查询
    g.cursor.execute(count_query, count_params)
    total_count = g.cursor.fetchone()[0]  # 获取总数

    # 添加分页
    query += " LIMIT %s OFFSET %s"
    params.append(limit)
    params.append(page * limit)

    # 执行分页查询
    g.cursor.execute(query, params)
    columns = [desc[0] for desc in g.cursor.description]
    results = g.cursor.fetchall()
    hospitals = [dict(zip(columns, row)) for row in results]

    # 返回数据 + 总条数
    return table_api(
        data=hospitals,
        count=total_count
    )

    #
    # g.cursor.execute("SELECT city, hospital_level, hospital_name, address, ownership, hospital_type, departments FROM hospitals"
    #                  " where city "
    #                  " limit 10")
    #
    # # 获取列名
    # columns = [desc[0] for desc in g.cursor.description]
    #
    # # 获取查询结果并映射为字典
    # results = g.cursor.fetchall()
    # hospitals = [dict(zip(columns, row)) for row in results]
    # return table_api(
    #     data= hospitals,
    #     count=100)

