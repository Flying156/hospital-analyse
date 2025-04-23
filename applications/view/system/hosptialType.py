from flask import g, Blueprint, render_template, jsonify
from flask_login import login_required
import json
from applications.extensions.init_redis import redis  # 导入 redis 配置import json
from applications.common.utils.rights import authorize
from applications.extensions.init_hive import HiveConnection

bp = Blueprint('hospitalType', __name__, url_prefix='/hospitalType')

# 初始化 Redis
@bp.route('/')
@authorize("system:hospitalType:main")
def main():
    return render_template('analyze/hospitalType/main.html')

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

@bp.route('/data')
@login_required
def get_hospitalType():
    try:

        redis_key = 'hospital_type_data'
        cached_data = redis.get(redis_key)

        if cached_data:
            # 如果缓存中有数据，直接返回缓存数据
            return jsonify(json.loads(cached_data))
        # 查询医院类型和所有制分布
        query = """
        SELECT hospital_type, ownership, COUNT(*) AS count
        FROM hospitals
        WHERE hospital_type IS NOT NULL AND ownership IS NOT NULL
        GROUP BY hospital_type, ownership
        ORDER BY hospital_type, count DESC
        """
        
        g.cursor.execute(query)
        results = g.cursor.fetchall()
        
        # 处理数据
        data = {}
        for row in results:
            hospital_type = row[0]
            ownership = row[1]
            count = row[2]
            
            if hospital_type not in data:
                data[hospital_type] = []
            
            data[hospital_type].append({
                'name': ownership,
                'value': count
            })

        # 将查询结果缓存到 Redis，缓存时间为 60 秒
        redis.set(redis_key, json.dumps({
            'code': 0,
            'msg': 'success',
            'data': data
        }))

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': data
        })
        
    except Exception as e:
        return jsonify({
            'code': 1,
            'msg': str(e),
            'data': {}
        })
