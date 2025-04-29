from concurrent.futures import ThreadPoolExecutor, as_completed
import requests, re, datetime
from bs4 import BeautifulSoup #解析网页数据
import xlwt  # 写入excle
import random, os, csv
import xlrd
import xlwings as xw
import pandas as pd 

# 初始化
def init():
    global url, province_name, headers, levels, base_path
    # 爬取文件地址
    url = 'https://www.yixue.com/'
    base_path = '/home/mike/Downloads/' 
    #  存储各省名称
    province_name = [
        '北京市', '天津市', '河北省', '山西省', '辽宁省', '吉林省', '黑龙江省', '上海市',
        '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省', '河南省', '湖北省',
        '湖南省', '广东省', '内蒙古自治区', '广西壮族自治区', '海南省', '重庆市', '四川省', '贵州省',
        '云南省', '西藏自治区', '陕西省', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区'
    ]

    levels =["三级甲等","三级乙等","三级丙等","二级甲等","二级乙等","二级丙等","一级甲等","一级乙等","一级丙等"]

    headers = {
        "user-agent": random_user_agent(),
        "Referer": "https://www.yixue.com/",
        "cookie": "newstatisticUUID=1651282597_602532090; _csrfToken=rmG7zCbbkD7QK34BymosH69Xve6eibDLGzeI2q8q; pageOps=1; fu=1403875312; qdrs=0|3|0|0|1; showSectionCommentGuide=1; qdgd=1; lrbc=1033272309|702228691|0; rcr=1033272309; bc=1033272309; _gid=GA1.2.364214729.1651282600; readadclose=1; _gat_gtag_UA_199934072_2=1; _ga_FZMMH98S83=GS1.1.1651282598.1.1.1651282753.0; _ga_PFYW0QLV3P=GS1.1.1651282598.1.1.1651282753.0; _ga=GA1.2.279552178.1651282599"
    }

#随机取数
def random_user_agent():
    ulist =["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36","Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32"]
    return ulist[random.randint(0,len(ulist)-1)]

def save_message(message, province_now, level):
    # 创建文件夹如果它不存在
    directory = base_path
    if not os.path.exists(directory):
        os.makedirs(directory)  # 创建目录

    # 创建 CSV 文件
    name = "医院列表.csv"
    filepath = os.path.join(directory, name)

    # 设置表头
    value = ["省份", "医院级别", "医院名称", "医院地址", "经营方式", "医院类型", "重点科室"]

    # 写入 CSV 文件
    with open(filepath, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter='|')
        # if not os.path.exists(filepath):
        #     writer.writerow(value)  # 写入表头

        i = 0
        for data in message[5]:
            # 判断是否缺少医院信息
            if len(data) <= 1:
                continue
            else:
                try:
                    row = [province_now, level]  # 先存省份和医院级别
                    hospital_info = ["", "", "", "", ""]  # 医院信息                  
                    hospital_info[0] = data.b.a.text # 写入医院名称
                    # 加载医院类型
                    r = requests.get(url + hospital_info[0].split('(')[0], headers=headers, timeout=10)
                    soup = BeautifulSoup(r.text, "lxml")
                    w = soup.find_all('ul')
                    for data_1 in w[4]:
                        now_mess = data_1.text.replace('\n', '')
                        now_data = now_mess.split('：')
                        if len(now_data) > 1:
                            key, value = now_data[0], now_data[1]
                            if key == '医院类型':
                                hospital_info[3] = value
                                break


                    for data_1 in data.ul:
                        now_mess = data_1.text.replace('\n', '')
                        now_data = now_mess.split('：')
                        if len(now_data) > 1:
                            key, value = now_data[0], now_data[1]
                            if key == "医院地址":
                                hospital_info[1] = value
                            elif key == "经营方式":
                                hospital_info[2] = value
                            elif key == "重点科室":
                                hospital_info[4] = value
                    if hospital_info[4] == "":
                        hospital_info[4] = "NULL"
                            # 填入数据
                    row.extend(hospital_info)
                    # 写入当前医院信息
                    writer.writerow(row)
                except Exception as e:
                    print(data.b.text + "这家医院爬取失败")

    print(f"Data saved to {filepath}")




# 获取当前省数据
def get_province_hospital(province_now, level):
    # 访问链接
    r = requests.get(url + province_now + level + '医院列表', headers=headers, timeout=10)
    # 加载  设置解析器
    soup = BeautifulSoup(r.text, "lxml")
    # 获取页面内容
    message = soup.find_all('ul')
    # print(ul_content)

    save_message(message, province_now, level)


#主函数
if __name__ == '__main__':
    init()
    with ThreadPoolExecutor(max_workers=5) as executor:  # 限制最大线程数
        futures = []
        for province in province_name:
            for level in levels:
                futures.append(executor.submit(get_province_hospital, province, level))

        # 等待所有任务完成
        for future in as_completed(futures):
            try:
                future.result()  # 捕获异常
            except Exception as e:
                print(f"爬取失败: {e}")
