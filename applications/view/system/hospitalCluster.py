from flask import g, Blueprint, render_template, jsonify
from flask_login import login_required
import json
from applications.extensions.init_redis import redis
from applications.common.utils.rights import authorize
from applications.extensions.init_hive import HiveConnection
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

bp = Blueprint('hospitalCluster', __name__, url_prefix='/hospitalCluster')

@bp.route('/')
@authorize("system:hospitalCluster:main")
def main():
    return render_template('analyze/hospitalCluster/main.html')

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
def get_hospital_cluster():
    try:
        redis_key = 'hospital_cluster_data'
        cached_data = redis.get(redis_key)

        if cached_data:
            return jsonify(json.loads(cached_data))

        # 查询医院数据
        query = """
        SELECT 
            hospital_name,
            hospital_level,
            hospital_type,
            ownership,
            departments,
            city
        FROM hospitals
        WHERE departments IS NOT NULL
        """

        g.cursor.execute(query)
        results = g.cursor.fetchall()

        # 准备数据
        hospitals = []
        features = []
        
        for row in results:
            hospital_name = row[0]
            hospital_level = row[1]
            hospital_type = row[2]
            ownership = row[3]
            departments = row[4]
            city = row[5]
            
            # 计算科室数量
            dept_count = len(departments.split('、')) if departments else 0
            
            # 医院等级转换为数值
            level_value = 0
            if '三级甲等' in hospital_level:
                level_value = 3
            elif '三级乙等' in hospital_level:
                level_value = 2.5
            elif '三级丙等' in hospital_level:
                level_value = 2
            elif '二级甲等' in hospital_level:
                level_value = 1.5
            elif '二级乙等' in hospital_level:
                level_value = 1
            elif '二级丙等' in hospital_level:
                level_value = 0.5
            elif '一级' in hospital_level:
                level_value = 0.2

            # 存储特征
            features.append([dept_count, level_value])
            
            # 存储医院信息
            hospitals.append({
                'hospital_name': hospital_name,
                'hospital_level': hospital_level,
                'hospital_type': hospital_type,
                'ownership': ownership,
                'dept_count': dept_count,
                'city': city,
                'level_value': level_value  # 添加数值化的等级
            })

        # 标准化特征
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # 执行聚类
        kmeans = KMeans(n_clusters=4, random_state=42)
        clusters = kmeans.fit_predict(features_scaled)

        # 为每个聚类添加标签
        cluster_labels = []
        for i in range(4):
            cluster_hospitals = [h for j, h in enumerate(hospitals) if clusters[j] == i]
            avg_dept = np.mean([h['dept_count'] for h in cluster_hospitals])
            avg_level = np.mean([h['level_value'] for h in cluster_hospitals])
            
            if avg_dept > 15 and avg_level > 2.5:
                label = "大型综合医院"
            elif avg_dept > 10 and avg_level > 2:
                label = "中型综合医院"
            elif avg_dept > 5 and avg_level > 1:
                label = "小型综合医院"
            else:
                label = "专科医院"
            
            cluster_labels.append(label)

        # 将聚类标签添加到医院数据中
        for i, hospital in enumerate(hospitals):
            hospital['cluster_label'] = cluster_labels[clusters[i]]

        response_data = {
            'code': 0,
            'msg': 'success',
            'data': hospitals
        }

        # 缓存数据到Redis，过期时间60秒
        redis.set(redis_key, json.dumps(response_data))
        return jsonify(response_data)

    except Exception as e:
        print("聚类分析错误:", str(e))
        return jsonify({
            'code': 1,
            'msg': str(e),
            'data': []
        }) 