from flask import g, Blueprint, render_template, jsonify
from flask_login import login_required

from applications.common.utils.rights import authorize
from applications.extensions.init_hive import HiveConnection

bp = Blueprint('hospitalAverage', __name__, url_prefix='/hospitalAverage')


@bp.route('/')
@authorize("system:hospitalAverage:main")
def main():
    return render_template('analyze/hospitalAverage/main.html')

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
def get_hospital_average():
    try:
        # 查询医院等级和人口数据
        query = """
        SELECT 
            h.short_city,
            p.population,
            COUNT(CASE WHEN h.hospital_level LIKE '三级%' THEN 1 END) as level3_count,
            COUNT(CASE WHEN h.hospital_level LIKE '二级%' THEN 1 END) as level2_count,
            COUNT(CASE WHEN h.hospital_level LIKE '一级%' THEN 1 END) as level1_count,
            COUNT(*) as total_hospitals
        FROM hospitals h
        JOIN population_data p ON h.short_city = p.city
        WHERE h.short_city IS NOT NULL AND p.population IS NOT NULL
        GROUP BY h.short_city, p.population
        ORDER BY p.population DESC
        """
        
        g.cursor.execute(query)
        results = g.cursor.fetchall()
        
        # 处理数据
        cities = []
        population = []
        level3_data = []
        level2_data = []
        level1_data = []
        total_data = []
        
        for row in results:
            cities.append(row[0])
            population.append(row[1])
            level3_data.append(row[2])
            level2_data.append(row[3])
            level1_data.append(row[4])
            total_data.append(row[5])
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'cities': cities,
                'population': population,
                'level3_data': level3_data,
                'level2_data': level2_data,
                'level1_data': level1_data,
                'total_data': total_data
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 1,
            'msg': str(e),
            'data': {}
        })