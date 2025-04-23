from flask import Flask, g
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from applications.extensions.init_redis import redis  # 导入 redis 配置import json
import json
from applications.common.utils.rights import authorize
from applications.extensions.init_hive import HiveConnection

bp = Blueprint('department', __name__, url_prefix='/department')


@bp.get('/')
@authorize("system:department:main")
def main():
    return render_template('analyze/department/main.html')

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

@bp.get('/data')
@login_required
def get_department_data():
    try:

        # 查询Redis缓存中的科室数据
        redis_key = 'department_data'
        cached_data = redis.get(redis_key)

        if cached_data:
            # 如果Redis缓存中有数据，直接返回缓存
            return jsonify(json.loads(cached_data))
        # 查询所有科室数据
        department_query = """
        SELECT departments
        FROM hospitals
        WHERE departments != 'NULL'
        """

        try:
            g.cursor.execute(department_query)
            department_results = g.cursor.fetchall()
        except Exception as e:
            print("科室查询失败:", str(e))
            department_results = []

        # 使用字典统计科室数量
        department_count = {}
        for row in department_results:
            try:
                if row[0]:  # 确保不是 NULL
                    # 按顿号分割科室
                    departments = row[0].split('、')
                    for dept in departments:
                        dept = dept.strip()  # 去除空格
                        if dept:  # 确保不是空字符串
                            department_count[dept] = department_count.get(dept, 0) + 1
            except Exception as e:
                print("处理科室数据失败:", str(e))
                continue

        # 转换为前端需要的格式，只返回出现次数大于1的科室
        department_data = [
            {
                'name': dept,
                'value': count
            }
            for dept, count in sorted(department_count.items(), key=lambda x: x[1], reverse=True)
            if count > 1  # 只保留出现次数大于1的科室
        ]

        response_data = {
            'code': 0,
            'msg': 'success',
            'data': department_data
        }

        # 缓存数据到Redis，过期时间60秒
        redis.set(redis_key, json.dumps(response_data))
        return jsonify(response_data)

    except Exception as e:
        print("发生错误:", str(e))
        return jsonify({
            'code': 1,
            'msg': str(e),
            'data': []
        })


