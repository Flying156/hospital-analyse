from flask import g, Blueprint, render_template, jsonify
from flask_login import login_required
import json
from applications.extensions.init_redis import redis
from applications.common.utils.rights import authorize
from applications.extensions.init_hive import HiveConnection
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
from collections import Counter

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
        redis_key = 'hospital_predict_data'
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
            city,
            short_city
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
            province = row[6]  # 使用short_city作为province
            
            # 计算科室数量
            dept_count = len(departments.split('、')) if departments and departments != 'NULL' else 0
            
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
                'dept_count': dept_count,
                'city': city,
                'province': province,  # 使用short_city作为province
                'level_value': level_value,  # 添加数值化的等级
                'departments': departments if departments and departments != 'NULL' else ''
            })

        # 标准化特征
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # 执行聚类
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(features_scaled)

        # 为每个聚类添加标签
        cluster_labels = []
        for i in range(3):
            cluster_hospitals = [h for j, h in enumerate(hospitals) if clusters[j] == i]
            avg_dept = np.mean([h['dept_count'] for h in cluster_hospitals])
            avg_level = np.mean([h['level_value'] for h in cluster_hospitals])
            
            if avg_dept > 10 and avg_level > 2:
                label = "综合医院"
            elif avg_dept > 5 and avg_level > 1:
                label = "专科医院"
            else:
                label = "整形美容院"
            
            cluster_labels.append(label)

        # 将聚类标签添加到医院数据中
        for i, hospital in enumerate(hospitals):
            hospital['cluster_label'] = cluster_labels[clusters[i]]

        # 预测地区医疗资源发展
        region_development = predict_region_development(hospitals)
        
        # 预测医院未来重点科室
        future_departments = predict_future_departments(hospitals)

        response_data = {
            'code': 0,
            'msg': 'success',
            'data': hospitals,
            'region_development': region_development,
            'future_departments': future_departments
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

def predict_region_development(hospitals):
    """预测地区医疗资源发展趋势（结合人口数据）"""
    from applications.extensions.init_hive import HiveConnection

    # 1. 读取人口数据
    conn = HiveConnection.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT city, population FROM population_data")
    pop_results = cursor.fetchall()
    # 构建人口字典
    population_dict = {}
    for row in pop_results:
        province = row[0]
        try:
            population = float(row[1])
        except Exception:
            population = 0
        population_dict[province] = population

    # 2. 按省份分组
    province_groups = {}
    for hospital in hospitals:
        province = hospital.get('province', '').strip()
        if not province:
            continue
        province_groups.setdefault(province, []).append(hospital)

    # 3. 计算各省份医疗资源指标
    province_stats = {}
    for province, hospitals in province_groups.items():
        # 医院数量
        hospital_count = len(hospitals)
        # 三级医院比例
        level3_count = sum(1 for h in hospitals if h['level_value'] >= 2)
        level3_ratio = level3_count / hospital_count if hospital_count > 0 else 0
        # 平均科室数量
        avg_dept_count = np.mean([h['dept_count'] for h in hospitals])
        # 综合医院比例
        general_count = sum(1 for h in hospitals if h['hospital_type'] == '综合医院')
        general_ratio = general_count / hospital_count if hospital_count > 0 else 0
        # 专科医院比例
        specialty_count = sum(1 for h in hospitals if h['hospital_type'] == '专科医院')
        specialty_ratio = specialty_count / hospital_count if hospital_count > 0 else 0
        # 整形美容院比例
        cosmetic_count = sum(1 for h in hospitals if h['hospital_type'] == '整形美容院')
        cosmetic_ratio = cosmetic_count / hospital_count if hospital_count > 0 else 0
        # 人口数
        population = population_dict.get(province, 0)

        # 发展潜力指数（引入人口因素，人口越多，医疗资源需求越大）
        # 你可以根据实际情况调整权重
        pop_score = min(population / 10000000, 1)  # 假设1千万人口为满分1分
        development_index = (
            level3_ratio * 0.3 +
            avg_dept_count / 20 * 0.2 +
            general_ratio * 0.15 +
            specialty_ratio * 0.1 +
            pop_score * 0.25
        )

        province_stats[province] = {
            'hospital_count': hospital_count,
            'level3_ratio': level3_ratio,
            'avg_dept_count': avg_dept_count,
            'general_ratio': general_ratio,
            'specialty_ratio': specialty_ratio,
            'cosmetic_ratio': cosmetic_ratio,
            'population': population,
            'development_index': development_index
        }

    # 4. 预测未来发展趋势
    future_development = {}
    for province, stats in province_stats.items():
        if stats['development_index'] > 0.7:
            trend = "快速发展"
        elif stats['development_index'] > 0.5:
            trend = "稳定发展"
        elif stats['development_index'] > 0.3:
            trend = "缓慢发展"
        else:
            trend = "需要加强"

        growth_rate = min(0.3, stats['development_index'] * 0.4)
        future_hospital_count = int(stats['hospital_count'] * (1 + growth_rate))
        future_level3_ratio = min(0.8, stats['level3_ratio'] + 0.1)
        future_avg_dept_count = stats['avg_dept_count'] + 2

        future_development[province] = {
            'current_stats': stats,
            'trend': trend,
            'future_hospital_count': future_hospital_count,
            'future_level3_ratio': future_level3_ratio,
            'future_avg_dept_count': future_avg_dept_count,
            'growth_rate': growth_rate
        }

    # 关闭连接
    cursor.close()
    conn.close()
    return future_development

def predict_future_departments(hospitals):
    """预测医院未来可能出现的重点科室"""
    # 收集所有科室
    all_departments = []
    for hospital in hospitals:
        if hospital['departments']:
            dept_list = hospital['departments'].split('、')
            all_departments.extend(dept_list)
    
    # 统计科室频率
    dept_counter = Counter(all_departments)
    
    # 找出最常见的科室
    common_departments = dept_counter.most_common(10)
    
    # 按医院类型分组
    hospital_types = {}
    for hospital in hospitals:
        hospital_type = hospital['hospital_type']
        if hospital_type not in hospital_types:
            hospital_types[hospital_type] = []
        hospital_types[hospital_type].append(hospital)
    
    # 预测每种医院类型未来可能出现的重点科室
    future_departments = {}
    
    # 综合医院未来可能出现的重点科室
    if '综合医院' in hospital_types:
        general_hospitals = hospital_types['综合医院']
        general_depts = []
        for hospital in general_hospitals:
            if hospital['departments']:
                dept_list = hospital['departments'].split('、')
                general_depts.extend(dept_list)
        
        general_dept_counter = Counter(general_depts)
        common_general_depts = general_dept_counter.most_common(5)
        
        # 预测未来可能出现的重点科室
        future_general_depts = []
        for dept, count in common_general_depts:
            if count > 0:
                future_general_depts.append({
                    'name': dept,
                    'probability': min(1.0, count / len(general_hospitals) * 2),
                    'reason': '该科室在综合医院中较为常见，未来可能会成为更多综合医院的重点科室'
                })
        
        # 添加一些新兴科室
        
        future_departments['综合医院'] = future_general_depts
    
    # 专科医院未来可能出现的重点科室
    if '专科医院' in hospital_types:
        specialty_hospitals = hospital_types['专科医院']
        specialty_depts = []
        for hospital in specialty_hospitals:
            if hospital['departments']:
                dept_list = hospital['departments'].split('、')
                specialty_depts.extend(dept_list)
        
        specialty_dept_counter = Counter(specialty_depts)
        common_specialty_depts = specialty_dept_counter.most_common(5)
        
        # 预测未来可能出现的重点科室
        future_specialty_depts = []
        for dept, count in common_specialty_depts:
            if count > 0:
                future_specialty_depts.append({
                    'name': dept,
                    'probability': min(1.0, count / len(specialty_hospitals) * 2),
                    'reason': '该科室在专科医院中较为常见，未来可能会成为更多专科医院的重点科室'
                })
        
        
        future_departments['专科医院'] = future_specialty_depts
    
    # 整形美容院未来可能出现的重点科室
    if '整形美容院' in hospital_types:
        cosmetic_hospitals = hospital_types['整形美容院']
        cosmetic_depts = []
        for hospital in cosmetic_hospitals:
            if hospital['departments']:
                dept_list = hospital['departments'].split('、')
                cosmetic_depts.extend(dept_list)
        
        cosmetic_dept_counter = Counter(cosmetic_depts)
        common_cosmetic_depts = cosmetic_dept_counter.most_common(5)
        
        # 预测未来可能出现的重点科室
        future_cosmetic_depts = []
        for dept, count in common_cosmetic_depts:
            if count > 0:
                future_cosmetic_depts.append({
                    'name': dept,
                    'probability': min(1.0, count / len(cosmetic_hospitals) * 2),
                    'reason': '该科室在整形美容院中较为常见，未来可能会成为更多整形美容院的重点科室'
                })
        

        
        future_departments['整形美容院'] = future_cosmetic_depts
    
    return future_departments

@bp.route('/levelDepartCluster')
@login_required
def get_hospital_cluster123():
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
            if isinstance(departments, list):
                dept_list = departments
            elif departments and departments != 'NULL':
                dept_list = departments.split('、')
            else:
                dept_list = []
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
                'departments': dept_list,  # 始终为list
                'dept_count': dept_count,
                'city': city,
                'level_value': level_value
            })

        # 标准化特征
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # 执行聚类
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(features_scaled)

        # 为每个聚类添加标签
        cluster_labels = []
        for i in range(3):
            cluster_hospitals = [h for j, h in enumerate(hospitals) if clusters[j] == i]
            avg_dept = np.mean([h['dept_count'] for h in cluster_hospitals]) if cluster_hospitals else 0
            avg_level = np.mean([h['level_value'] for h in cluster_hospitals]) if cluster_hospitals else 0

            if avg_dept > 10 and avg_level > 2:
                label = "综合医院"
            elif avg_dept > 5 and avg_level > 1:
                label = "专科医院"
            else:
                label = "整形美容院"
            cluster_labels.append(label)

        # 将聚类标签添加到医院数据中
        for i, hospital in enumerate(hospitals):
            hospital['cluster_label'] = cluster_labels[clusters[i]]

        # 确保所有医院类型都被包含在聚类结果中
        all_types = ["综合医院", "专科医院", "整形美容院"]
        existing_labels = set(cluster_labels)
        for type_name in all_types:
            if type_name not in existing_labels:
                type_hospitals = [h for h in hospitals if type_name in h['hospital_type']]
                if type_hospitals:
                    for hospital in type_hospitals:
                        hospital['cluster_label'] = type_name

        # 统计每个聚类的统计信息
        cluster_stats = {}
        for label in all_types:
            cluster_hospitals = [h for h in hospitals if h['cluster_label'] == label]
            count = len(cluster_hospitals)
            if count == 0:
                continue
            avg_dept_count = np.mean([h['dept_count'] for h in cluster_hospitals])
            # 医院等级分布
            level_distribution = {}
            for h in cluster_hospitals:
                level = h['hospital_level']
                level_distribution[level] = level_distribution.get(level, 0) + 1
            # 统计常见重点科室
            dept_counter = {}
            for h in cluster_hospitals:
                for dept in h['departments']:
                    dept_counter[dept] = dept_counter.get(dept, 0) + 1
            # 取前5名
            common_depts = sorted(dept_counter.items(), key=lambda x: x[1], reverse=True)[:5]
            cluster_stats[label] = {
                'count': count,
                'avg_dept_count': float(avg_dept_count),
                'level_distribution': level_distribution,
                'common_depts': common_depts
            }

        response_data = {
            'code': 0,
            'msg': 'success',
            'data': {
                'hospitals': hospitals,
                'cluster_stats': cluster_stats
            }
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