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
    """预测地区医疗资源发展趋势"""
    # 按省份分组
    province_groups = {}
    for hospital in hospitals:
        province = hospital['province']
        if province not in province_groups:
            province_groups[province] = []
        province_groups[province].append(hospital)
    
    # 计算各省份医疗资源指标
    province_stats = {}
    for province, hospitals in province_groups.items():
        # 计算医院数量
        hospital_count = len(hospitals)
        
        # 计算三级医院比例
        level3_count = sum(1 for h in hospitals if h['level_value'] >= 2)
        level3_ratio = level3_count / hospital_count if hospital_count > 0 else 0
        
        # 计算平均科室数量
        avg_dept_count = np.mean([h['dept_count'] for h in hospitals])
        
        # 计算综合医院比例
        general_count = sum(1 for h in hospitals if h['hospital_type'] == '综合医院')
        general_ratio = general_count / hospital_count if hospital_count > 0 else 0
        
        # 计算专科医院比例
        specialty_count = sum(1 for h in hospitals if h['hospital_type'] == '专科医院')
        specialty_ratio = specialty_count / hospital_count if hospital_count > 0 else 0
        
        # 计算整形美容院比例
        cosmetic_count = sum(1 for h in hospitals if h['hospital_type'] == '整形美容院')
        cosmetic_ratio = cosmetic_count / hospital_count if hospital_count > 0 else 0
        
        # 计算发展潜力指数 (简单加权平均)
        development_index = (level3_ratio * 0.4 + 
                            avg_dept_count / 20 * 0.3 + 
                            general_ratio * 0.2 + 
                            specialty_ratio * 0.1)
        
        province_stats[province] = {
            'hospital_count': hospital_count,
            'level3_ratio': level3_ratio,
            'avg_dept_count': avg_dept_count,
            'general_ratio': general_ratio,
            'specialty_ratio': specialty_ratio,
            'cosmetic_ratio': cosmetic_ratio,
            'development_index': development_index
        }
    
    # 预测未来发展趋势
    future_development = {}
    for province, stats in province_stats.items():
        # 基于当前指标预测未来发展趋势
        if stats['development_index'] > 0.7:
            trend = "快速发展"
        elif stats['development_index'] > 0.5:
            trend = "稳定发展"
        elif stats['development_index'] > 0.3:
            trend = "缓慢发展"
        else:
            trend = "需要加强"
        
        # 预测未来5年医院数量增长
        growth_rate = min(0.3, stats['development_index'] * 0.4)  # 最大增长30%
        future_hospital_count = int(stats['hospital_count'] * (1 + growth_rate))
        
        # 预测未来5年三级医院比例变化
        future_level3_ratio = min(0.8, stats['level3_ratio'] + 0.1)  # 最大比例80%
        
        # 预测未来5年平均科室数量变化
        future_avg_dept_count = stats['avg_dept_count'] + 2  # 平均增加2个科室
        
        future_development[province] = {
            'current_stats': stats,
            'trend': trend,
            'future_hospital_count': future_hospital_count,
            'future_level3_ratio': future_level3_ratio,
            'future_avg_dept_count': future_avg_dept_count,
            'growth_rate': growth_rate
        }
    
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
        emerging_depts = ['人工智能医疗中心', '精准医疗中心', '干细胞治疗中心', '基因治疗中心', '远程医疗中心']
        for dept in emerging_depts:
            if dept not in [d['name'] for d in future_general_depts]:
                future_general_depts.append({
                    'name': dept,
                    'probability': 0.6,
                    'reason': '随着医疗技术进步，该科室可能会成为综合医院的新兴重点科室'
                })
        
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
        
        # 添加一些新兴科室
        emerging_depts = ['精准治疗中心', '微创治疗中心', '康复治疗中心', '疼痛治疗中心', '心理治疗中心']
        for dept in emerging_depts:
            if dept not in [d['name'] for d in future_specialty_depts]:
                future_specialty_depts.append({
                    'name': dept,
                    'probability': 0.5,
                    'reason': '随着专科医疗技术发展，该科室可能会成为专科医院的新兴重点科室'
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
        
        # 添加一些新兴科室
        emerging_depts = ['微整形中心', '皮肤管理中心', '抗衰老中心', '形体雕塑中心', '毛发移植中心']
        for dept in emerging_depts:
            if dept not in [d['name'] for d in future_cosmetic_depts]:
                future_cosmetic_depts.append({
                    'name': dept,
                    'probability': 0.7,
                    'reason': '随着美容技术发展，该科室可能会成为整形美容院的新兴重点科室'
                })
        
        future_departments['整形美容院'] = future_cosmetic_depts
    
    return future_departments

@bp.route('/levelDepartCluster')
@login_required
def get_hospital_level_depart_cluster():

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


@bp.route('/levelDepartCluster')
@login_required
def get_hospital_cluster12():
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