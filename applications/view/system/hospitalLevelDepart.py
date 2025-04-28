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

@bp.route('/levelDepartCluster')
@login_required
def get_hospital_cluster():
    try:
        redis_key = 'hospital_cluster_data'
        cached_data = redis.get(redis_key)

        if cached_data:
            return jsonify(json.loads(cached_data))

        # 查询所有医院数据，包括医院类型
        query = """
        SELECT 
            hospital_name,
            hospital_level,
            hospital_type,
            ownership,
            departments,
            city
        FROM hospitals
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
            
            # 计算重点科室数量，处理NULL或空值的情况
            dept_list = departments.split('、') if departments and departments != 'NULL' else []
            dept_count = len(dept_list)
            
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
            elif '一级甲等' in hospital_level:
                level_value = 0.3
            elif '一级乙等' in hospital_level:
                level_value = 0.2
            elif '一级丙等' in hospital_level:
                level_value = 0.1

            # 存储特征
            features.append([dept_count, level_value])
            
            # 存储医院信息
            hospitals.append({
                'hospital_name': hospital_name,
                'hospital_level': hospital_level,
                'hospital_type': hospital_type,
                'ownership': ownership,
                'departments': dept_list,
                'dept_count': dept_count,
                'city': city,
                'level_value': level_value  # 添加数值化的等级
            })

        # 标准化特征
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # 执行聚类
        kmeans = KMeans(n_clusters=3, random_state=42)  # 修改为3个聚类
        clusters = kmeans.fit_predict(features_scaled)

        # 为每个聚类添加标签
        cluster_labels = []
        for i in range(3):  # 修改为3个聚类
            cluster_hospitals = [h for j, h in enumerate(hospitals) if clusters[j] == i]
            
            # 统计医院类型
            type_counts = {}
            for hospital in cluster_hospitals:
                hospital_type = hospital['hospital_type']
                if hospital_type in type_counts:
                    type_counts[hospital_type] += 1
                else:
                    type_counts[hospital_type] = 1
            
            # 找出最常见的医院类型
            most_common_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "未知"
            
            # 根据医院类型确定标签
            if "综合" in most_common_type:
                label = "综合医院"
            elif "整形" in most_common_type:
                label = "整形美容院"
            else:
                label = "专科医院"
            
            cluster_labels.append(label)

        # 将聚类标签添加到医院数据中
        for i, hospital in enumerate(hospitals):
            hospital['cluster_label'] = cluster_labels[clusters[i]]

        # 确保所有医院类型都被包含在聚类结果中
        # 如果某个医院类型没有被包含在聚类结果中，我们手动添加一个聚类
        all_types = ["综合医院", "专科医院", "整形美容院"]
        existing_labels = set(cluster_labels)
        
        # 如果某个医院类型没有被包含在聚类结果中，我们手动添加一个聚类
        for type_name in all_types:
            if type_name not in existing_labels:
                # 找出属于该类型的医院
                type_hospitals = [h for h in hospitals if type_name in h['hospital_type']]
                if type_hospitals:
                    # 将这些医院添加到聚类结果中
                    for hospital in type_hospitals:
                        hospital['cluster_label'] = type_name

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