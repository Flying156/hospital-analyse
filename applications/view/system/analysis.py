from flask import g, Blueprint, render_template, jsonify
from applications.extensions.init_hive import HiveConnection

bp = Blueprint('analysis', __name__, url_prefix='/analysis')


@bp.route('/main')
def main():
    return render_template('system/analysis/main.html')

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
def get_hospital_data():
    try:
        # 查询各等级医院总数（只统计三级、二级、一级的总数）
        total_query = """
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN hospital_level LIKE '三级%' THEN 1 ELSE 0 END) as level3_count,
            SUM(CASE WHEN hospital_level LIKE '二级%' THEN 1 ELSE 0 END) as level2_count,
            SUM(CASE WHEN hospital_level LIKE '一级%' THEN 1 ELSE 0 END) as level1_count
        FROM hospitals
        """
        
        # 查询各省份医院数量（包含详细等级）
        province_query = """
        SELECT 
            short_city,
            SUM(CASE WHEN hospital_level LIKE '三级甲等%' THEN 1 ELSE 0 END) as level3_a_count,
            SUM(CASE WHEN hospital_level LIKE '三级乙等%' THEN 1 ELSE 0 END) as level3_b_count,
            SUM(CASE WHEN hospital_level LIKE '三级丙等%' THEN 1 ELSE 0 END) as level3_c_count,
            SUM(CASE WHEN hospital_level LIKE '二级甲等%' THEN 1 ELSE 0 END) as level2_a_count,
            SUM(CASE WHEN hospital_level LIKE '二级乙等%' THEN 1 ELSE 0 END) as level2_b_count,
            SUM(CASE WHEN hospital_level LIKE '二级丙等%' THEN 1 ELSE 0 END) as level2_c_count,
            SUM(CASE WHEN hospital_level LIKE '一级甲等%' THEN 1 ELSE 0 END) as level1_a_count,
            SUM(CASE WHEN hospital_level LIKE '一级乙等%' THEN 1 ELSE 0 END) as level1_b_count,
            SUM(CASE WHEN hospital_level LIKE '一级丙等%' THEN 1 ELSE 0 END) as level1_c_count
        FROM hospitals
        GROUP BY short_city
        """

        # 执行查询

        g.cursor.execute(total_query)
        total_result = g.cursor.fetchone()



        g.cursor.execute(province_query)
        province_results = g.cursor.fetchall()


        province_data = []
        for row in province_results:
            try:
                # 计算各等级总数
                level3_total = row[1] + row[2] + row[3]  # 三级甲等 + 三级乙等 + 三级丙等
                level2_total = row[4] + row[5] + row[6]  # 二级甲等 + 二级乙等 + 二级丙等
                level1_total = row[7] + row[8] + row[9]  # 一级甲等 + 一级乙等 + 一级丙等
                total = level3_total + level2_total + level1_total
                
                province_data.append({
                    'name': row[0],  # 省份名称
                    'value': total,  # 总医院数
                    'level3_a': row[1],  # 三级甲等
                    'level3_b': row[2],  # 三级乙等
                    'level3_c': row[3],  # 三级丙等
                    'level2_a': row[4],  # 二级甲等
                    'level2_b': row[5],  # 二级乙等
                    'level2_c': row[6],  # 二级丙等
                    'level1_a': row[7],  # 一级甲等
                    'level1_b': row[8],  # 一级乙等
                    'level1_c': row[9]   # 一级丙等
                })
            except Exception as e:
                print("处理省份数据失败:", str(e))
                continue
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'level3_count': total_result[1] if total_result else 0,
                'level2_count': total_result[2] if total_result else 0,
                'level1_count': total_result[3] if total_result else 0,
                'hospital_sum': total_result[0] if total_result else 0,
                'province_data': province_data
            }
        })
        
    except Exception as e:
        print("发生错误:", str(e))
        return jsonify({
            'code': 1,
            'msg': str(e),
            'data': {
                'level3_count': 0,
                'level2_count': 0,
                'level1_count': 0,
                'hospital_sum': 0,
                'province_data': []
            }
        })
