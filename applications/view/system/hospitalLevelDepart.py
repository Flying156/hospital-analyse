from flask import g, Blueprint, render_template, jsonify
from flask_login import login_required
import json
from applications.extensions.init_redis import redis  # 导入 redis 配置import json
from applications.common.utils.rights import authorize
from applications.extensions.init_hive import HiveConnection
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

bp = Blueprint('hospitalLevelDepart', __name__, url_prefix='/hospitalLevelDepart')

@bp.route('/')
@authorize("system:hospitalLevelDepart:main")
def main():
    return render_template('analyze/hospitalLevelDepart/main.html')


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
def get_hospital_level_depart():
    try:

        redis_key = 'hospital_level_depart_data'
        cached_data = redis.get(redis_key)

        if cached_data:
            # 如果缓存中有数据，直接返回缓存数据
            return jsonify(json.loads(cached_data))
        # 查询医院等级和重点科室数据
        query = """
        SELECT 
            hospital_level,
            departments
        FROM hospitals
        WHERE departments != 'NULL'
        """

        g.cursor.execute(query)
        results = g.cursor.fetchall()
        print(results)
        # 处理数据
        departments_count = {}
        level_counts = {'三级甲等': 0, '三级乙等': 0, '三级丙等': 0,
                       '二级甲等': 0, '二级乙等': 0, '二级丙等': 0,
                       '一级甲等': 0, '一级乙等': 0, '一级丙等': 0
                    }

        for row in results:
            level = row[0]
            departments = row[1].split('、') if row[1] else []
            
            for dept in departments:
                if dept not in departments_count:
                    departments_count[dept] = {
                        '三级甲等': 0, '三级乙等': 0, '三级丙等': 0,
                        '二级甲等': 0, '二级乙等': 0, '二级丙等': 0,
                        '一级甲等': 0, '一级乙等': 0, '一级丙等': 0
                    }
                
                level_matched = False
                for known_level in departments_count[dept].keys():
                    if known_level in level:
                        departments_count[dept][known_level] += 1
                        level_matched = True
                        break

        print("医院等级统计:", level_counts)
        print("科室数量:", len(departments_count))

        # 转换为前端需要的格式
        departments = list(departments_count.keys())
        
        # 计算每个科室的总医院数并排序
        department_totals = []
        for dept in departments:
            total = sum(departments_count[dept].values())
            department_totals.append((dept, total))
        
        # 按总医院数降序排序
        department_totals.sort(key=lambda x: x[1], reverse=True)
        
        # 获取排序后的科室列表
        sorted_departments = [item[0] for item in department_totals]
        
        # 根据排序后的科室顺序获取数据
        level3a_data = [departments_count[dept]['三级甲等'] for dept in sorted_departments]
        level3b_data = [departments_count[dept]['三级乙等'] for dept in sorted_departments]
        level3c_data = [departments_count[dept]['三级丙等'] for dept in sorted_departments]
        level2a_data = [departments_count[dept]['二级甲等'] for dept in sorted_departments]
        level2b_data = [departments_count[dept]['二级乙等'] for dept in sorted_departments]
        level2c_data = [departments_count[dept]['二级丙等'] for dept in sorted_departments]
        level1a_data = [departments_count[dept]['一级甲等'] for dept in sorted_departments]
        level1b_data = [departments_count[dept]['一级乙等'] for dept in sorted_departments]
        level1c_data = [departments_count[dept]['一级丙等'] for dept in sorted_departments]

        response_data = {
            'code': 0,
            'msg': 'success',
            'data': {
                'departments': sorted_departments,
                'level3a_data': level3a_data,
                'level3b_data': level3b_data,
                'level3c_data': level3c_data,
                'level2a_data': level2a_data,
                'level2b_data': level2b_data,
                'level2c_data': level2c_data,
                'level1a_data': level1a_data,
                'level1b_data': level1b_data,
                'level1c_data': level1c_data
            }
        }

        # 将查询结果缓存到 Redis，缓存时间为 60 秒
        redis.set(redis_key, json.dumps(response_data))

        return jsonify(response_data)

    except Exception as e:
        print("错误详情:", str(e))
        return jsonify({
            'code': 1,
            'msg': str(e),
            'data': {}
        })
