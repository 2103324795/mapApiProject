from flask import Flask, request, render_template, jsonify
import os
import requests
from dotenv import load_dotenv
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for

# 加载环境变量
load_dotenv()

# 创建Flask应用，指定静态文件目录
app = Flask(__name__, static_folder='static', static_url_path='/static')

# 获取高德地图API密钥
AMAP_KEY = os.getenv('AMAP_KEY')

# 如果没有设置API密钥，使用默认值（实际使用时请替换为你的密钥）
if not AMAP_KEY:
    AMAP_KEY = "请替换为你的高德地图API密钥"

@app.route('/')
def index():
    """首页，提供一个简单的表单来输入两个地点和场所类型"""
    return render_template('index.html')

@app.route('/search_between_locations')
def search_between_locations():
    """
    查询两个地点之间的特定场所
    
    参数:
        location1: 第一个地点名称（如"北京西站"）
        location2: 第二个地点名称（如"天安门"）
        poi_type: 要查询的场所类型（如"书店"、"咖啡馆"、"商场"等）
    
    返回:
        HTML页面，展示两个地点之间的指定类型场所
    """
    # 获取请求参数
    location1 = request.args.get('location1', '')
    location2 = request.args.get('location2', '')
    poi_type = request.args.get('poi_type', '')
    
    # 参数验证
    if not location1 or not location2 or not poi_type:
        return render_template('error.html', message="请提供两个地点和场所类型")
    
    try:
        # 1. 获取两个地点的地理坐标
        location1_geo = get_location_geo(location1)
        location2_geo = get_location_geo(location2)
        
        if not location1_geo or not location2_geo:
            return render_template('error.html', message="无法获取地点的地理坐标，请检查地点名称是否正确")
        
        # 2. 计算两点之间的中心点
        center_point = calculate_center_point(location1_geo, location2_geo)
        
        # 3. 计算两点之间的距离（单位：米）
        distance = calculate_distance(location1_geo, location2_geo)
        
        # 4. 根据距离确定搜索半径（最大为距离的一半，最小为500米，最大为5000米）
        search_radius = min(max(distance / 2, 500), 5000)
        
        # 5. 在中心点附近搜索指定类型的场所
        pois = search_pois_around(center_point, poi_type, search_radius)
        
        # 6. 计算每个POI到起点和终点的距离和时间
        for poi in pois:
            poi_location = poi["location"].split(",")
            poi_geo = {"longitude": poi_location[0], "latitude": poi_location[1]}
            
            # 计算到起点的距离
            distance_to_location1 = calculate_distance(poi_geo, location1_geo)
            # 安全地转换成整数
            poi["distance_to_location1"] = safe_int(distance_to_location1, 0)
            
            # 计算到终点的距离
            distance_to_location2 = calculate_distance(poi_geo, location2_geo)
            # 安全地转换成整数
            poi["distance_to_location2"] = safe_int(distance_to_location2, 0)
            
            # 计算从起点到POI的公交/地铁时间(分钟)
            time_to_location1 = calculate_transit_time(location1_geo, poi_geo)
            poi["time_to_location1"] = time_to_location1
            
            # 计算从终点到POI的公交/地铁时间(分钟)
            time_to_location2 = calculate_transit_time(location2_geo, poi_geo)
            poi["time_to_location2"] = time_to_location2
        
        # 6. 渲染结果页面
        return render_template('result.html', 
                              location1=location1,
                              location2=location2,
                              poi_type=poi_type,
                              location1_geo=location1_geo,
                              location2_geo=location2_geo,
                              pois=pois,
                              amap_key=AMAP_KEY)
    
    except Exception as e:
        return render_template('error.html', message=f"查询出错: {str(e)}")

def get_location_geo(location_name):
    """
    获取地点的地理坐标
    
    参数:
        location_name: 地点名称
    
    返回:
        字典，包含经度和纬度，格式为 {"longitude": 经度, "latitude": 纬度}
    """
    url = f"https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": AMAP_KEY,
        "address": location_name
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("status") == "1" and data.get("geocodes") and len(data["geocodes"]) > 0:
        location = data["geocodes"][0]["location"]
        longitude, latitude = location.split(",")
        return {"longitude": longitude, "latitude": latitude}
    
    return None

def calculate_center_point(point1, point2):
    """
    计算两点之间的中心点
    
    参数:
        point1: 第一个点的坐标，格式为 {"longitude": 经度, "latitude": 纬度}
        point2: 第二个点的坐标，格式为 {"longitude": 经度, "latitude": 纬度}
    
    返回:
        字典，包含中心点的经度和纬度，格式为 {"longitude": 经度, "latitude": 纬度}
    """
    longitude = (float(point1["longitude"]) + float(point2["longitude"])) / 2
    latitude = (float(point1["latitude"]) + float(point2["latitude"])) / 2
    
    return {"longitude": str(longitude), "latitude": str(latitude)}

def safe_float(value, default=0.0):
    """安全地将任何值转换为浮点数，如果转换失败则返回默认值"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        # 尝试清理字符串，移除非数字字符
        if isinstance(value, str):
            clean_value = ''.join(c for c in value if c.isdigit() or c == '.' or c == '-')
            try:
                return float(clean_value) if clean_value else default
            except (ValueError, TypeError):
                return default
        return default

def safe_int(value, default=0):
    """安全地将任何值转换为整数，如果转换失败则返回默认值"""
    return int(safe_float(value, default))

def calculate_distance(point1, point2):
    """
    计算两点之间的距离（使用高德地图API的距离计算接口）
    
    参数:
        point1: 第一个点的坐标，格式为 {"longitude": 经度, "latitude": 纬度}
        point2: 第二个点的坐标，格式为 {"longitude": 经度, "latitude": 纬度}
    
    返回:
        距离，单位为米
    """
    url = f"https://restapi.amap.com/v3/distance"
    params = {
        "key": AMAP_KEY,
        "origins": f"{point1['longitude']},{point1['latitude']}",
        "destination": f"{point2['longitude']},{point2['latitude']}",
        "type": "1"  # 1表示直线距离
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("status") == "1" and data.get("results") and len(data["results"]) > 0:
        # 安全地转换距离值
        return safe_float(data["results"][0]["distance"], 0)
    
    # 如果API调用失败，使用简单的球面距离计算（不够精确，但可作为备选）
    import math
    
    # 将经纬度转换为弧度
    lon1 = safe_float(point1["longitude"], 0) * math.pi / 180
    lat1 = safe_float(point1["latitude"], 0) * math.pi / 180
    lon2 = safe_float(point2["longitude"], 0) * math.pi / 180
    lat2 = safe_float(point2["latitude"], 0) * math.pi / 180
    
    # 地球半径（单位：米）
    earth_radius = 6371000
    
    # 使用Haversine公式计算球面距离
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = earth_radius * c
    
    return distance


def calculate_driving_time(point1, point2):
    """
    计算从一个点到另一个点的驾车时间
    
    参数:
        point1: 起点坐标，格式为 {"longitude": 经度, "latitude": 纬度}
        point2: 终点坐标，格式为 {"longitude": 经度, "latitude": 纬度}
    
    返回:
        驾车时间，单位为分钟
    """
    # 调用高德地图路径规划API计算时间
    url = "https://restapi.amap.com/v3/direction/driving"
    params = {
        "key": AMAP_KEY,
        "origin": f"{point1['longitude']},{point1['latitude']}",
        "destination": f"{point2['longitude']},{point2['latitude']}",
        "extensions": "base",
        "strategy": 0  # 默认策略，速度优先
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data["status"] == "1" and "route" in data and "paths" in data["route"] and len(data["route"]["paths"]) > 0:
            # 获取时间，单位为秒，转换为分钟
            duration_seconds = safe_float(data["route"]["paths"][0]["duration"], 0)
            return round(duration_seconds / 60)  # 转换为分钟并四舍五入
        else:
            # 如果API调用失败，使用距离附加平均速度计算
            distance = calculate_distance(point1, point2)
            avg_speed = 500  # 假设平均速度为500米/分钟（即30km/h）
            return round(distance / avg_speed)
    except Exception as e:
        print(f"API 调用出错: {str(e)}")
        # 如果发生错误，使用距离附加平均速度计算
        distance = calculate_distance(point1, point2)
        avg_speed = 500  # 假设平均速度为500米/分钟
        return round(distance / avg_speed)


def calculate_transit_time(point1, point2):
    """
    计算从一个点到另一个点的公交/地铁时间
    
    参数:
        point1: 起点坐标，格式为 {"longitude": 经度, "latitude": 纬度}
        point2: 终点坐标，格式为 {"longitude": 经度, "latitude": 纬度}
    
    返回:
        乘坐公交/地铁的时间，单位为分钟
    """
    # 调用高德地图公交路径规划API计算时间
    url = "https://restapi.amap.com/v3/direction/transit/integrated"
    params = {
        "key": AMAP_KEY,
        "origin": f"{point1['longitude']},{point1['latitude']}",
        "destination": f"{point2['longitude']},{point2['latitude']}",
        "extensions": "base",
        "strategy": 0,  # 最快捷模式
        "city": "北京",  # 默认城市，实际运行时可能需要根据坐标获取城市编码
        "cityd": "北京"   # 目的地城市
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data["status"] == "1" and "route" in data and "transits" in data["route"] and len(data["route"]["transits"]) > 0:
            # 获取第一条路线的时间，单位为分钟
            duration_seconds = safe_float(data["route"]["transits"][0]["duration"], 0)
            return round(duration_seconds / 60)  # 转换为分钟并四舍五入
        else:
            # 如果查询不到公交路线，则使用步行时间+倍率计算估计值
            distance = calculate_distance(point1, point2)
            # 假设平均速度为200米/分钟，比步行稍快一些（地铁快但有等待和换乘时间）
            avg_speed = 200
            return round(distance / avg_speed)
    except Exception as e:
        print(f"公交路线API调用出错: {str(e)}")
        # 如果发生错误，使用距离附加平均速度计算
        distance = calculate_distance(point1, point2)
        avg_speed = 200  # 假设平均速度为200米/分钟
        return round(distance / avg_speed)

def search_pois_around(center_point, poi_type, radius):
    """
    在指定中心点附近搜索特定类型的场所
    
    参数:
        center_point: 中心点坐标，格式为 {"longitude": 经度, "latitude": 纬度}
        poi_type: 场所类型，如"书店"、"咖啡馆"、"商场"等
        radius: 搜索半径，单位为米
    
    返回:
        列表，包含搜索到的场所信息
    """
    # 如果是咖啡馆，只返回知名的、人气高的品牌
    if poi_type == "咖啡馆":
        # 扫除社区店和不知名的小店，只保留知名连锁品牌
        famous_brands = ["星巴克", "Starbucks", "Costa", "科斯塔", "太平洋咖啡", "耐克", "COSTA",
                       "上峰", "醇品", "luckin", "瑞幅", "M Stand", "包图", "Peet's", "小瓷咖啡",
                       "Tim Hortons", "安罗咖啡", "Blue Bottle", "蒸汽工场", "一半一半", "衣服馆",
                       "罗森茶", "包图", "南竹竹", "小哪家"]
        
        # 优先搜索知名品牌
        all_pois = []
        for brand in famous_brands[:5]:  # 只取前5个品牌查询，防止请求过多
            brand_pois = search_specific_pois(center_point, brand, radius, page_size=5)
            all_pois.extend(brand_pois)
        
        # 但也搜索一般的咖啡馆，可能有小贗子裡的特色店
        general_pois = search_specific_pois(center_point, poi_type, radius, page_size=10)
        
        # 想法：筛除掉带有社区、公寓、小区等关键词的咖啡店
        filtered_pois = []
        exclude_keywords = ["社区", "小区", "公寓", "住宅", "派出", "分店", "火车站", "地铁站"]
        
        for poi in general_pois:
            exclude = False
            for keyword in exclude_keywords:
                if keyword in poi["name"]:
                    exclude = True
                    break
            if not exclude:
                filtered_pois.append(poi)
        
        # 合并结果并按评分排序
        all_pois.extend(filtered_pois)
        
        # 按照收藏人数排序，取得最佳结果
        all_pois.sort(key=lambda x: safe_float(x.get("biz_ext", {}).get("rating", "0") or "0"), reverse=True)
        
        # 只返回前5个结果
        return all_pois[:5] if len(all_pois) > 5 else all_pois
    else:
        # 其他类型的POI正常搜索
        main_pois = search_specific_pois(center_point, poi_type, radius)
        
        # 如果是餐厅类型，也进行筛选
        if poi_type in ["餐厅", "餐馆", "美食"]:
            filtered_pois = []
            exclude_keywords = ["社区", "小区", "公寓", "住宅", "派出", "分店"]
            
            for poi in main_pois:
                exclude = False
                for keyword in exclude_keywords:
                    if keyword in poi["name"]:
                        exclude = True
                        break
                if not exclude:
                    filtered_pois.append(poi)
            
            # 按照评分排序
            filtered_pois.sort(key=lambda x: safe_float(x.get("biz_ext", {}).get("rating", "0") or "0"), reverse=True)
            main_pois = filtered_pois[:10] if len(filtered_pois) > 10 else filtered_pois
        
        return main_pois

def search_specific_pois(center_point, poi_type, radius, page_size=20):
    """搜索特定类型的POI"""
    url = f"https://restapi.amap.com/v3/place/around"
    params = {
        "key": AMAP_KEY,
        "location": f"{center_point['longitude']},{center_point['latitude']}",
        "keywords": poi_type,
        "radius": radius,
        "offset": page_size,  # 每页记录数
        "page": 1,     # 页码
        "extensions": "all",  # 返回详细信息
        "sortrule": "distance",  # 按距离排序
        "show_fields": "photos,business,rating"  # 额外返回照片、营业时间和评分
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("status") == "1" and data.get("pois"):
        pois = data["pois"]
        # 为每个POI添加图片URL
        for poi in pois:
            # 添加商家图片URL
            if "photos" in poi and poi.get("photos") and len(poi["photos"]) > 0:
                poi["photo_url"] = poi["photos"][0]["url"]
            else:
                # 如果没有图片，使用默认图片
                default_images = {
                    "超市": "https://store.is.autonavi.com/showpic/656b5454a3103605bc10baaa",
                    "咖啡馆": "https://store.is.autonavi.com/showpic/756a2f6a86f7c83d62dcdb86",
                    "餐厅": "https://store.is.autonavi.com/showpic/333a5487c131fb9f12b8b1ae",
                    "银行": "https://store.is.autonavi.com/showpic/b5b277e0abd9b7f6605e901d"
                }
                poi["photo_url"] = default_images.get(poi_type, "https://store.is.autonavi.com/showpic/322339aeaa96937e286c6aeb")
            
            # 处理营业时间
            if "business" in poi and poi.get("business") and poi["business"].strip():
                poi["business_hours"] = poi["business"]
            else:
                poi["business_hours"] = "暂无营业时间信息"
                
            # 处理评分
            if "biz_ext" in poi and poi["biz_ext"].get("rating") and poi["biz_ext"]["rating"].strip():
                poi["rating"] = poi["biz_ext"]["rating"]
                poi["review_count"] = poi["biz_ext"].get("cost", "0") # 这里用cost字段代替评论数
            else:
                poi["rating"] = "暂无评分"
                poi["review_count"] = "0"
        
        return pois
    
    return []

# 添加直接调用高德API的接口，加速数据获取
@app.route('/api/poi', methods=['POST'])
def direct_poi_search():
    data = request.get_json()
    center = data.get('center')
    keywords = data.get('keywords')
    radius = data.get('radius', 3000)
    
    if not center or not keywords:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # 直接调用高德API，跳过中间层处理，加速数据传输
    url = "https://restapi.amap.com/v3/place/around"
    params = {
        "key": AMAP_KEY,
        "location": center,
        "keywords": keywords,
        "radius": radius,
        "offset": 50,  # 获取更多POI
        "page": 1,
        "extensions": "all",
        "sortrule": "distance"
    }
    
    response = requests.get(url, params=params)
    return jsonify(response.json())

# 添加直接调用高德路线规划API的接口
@app.route('/api/route', methods=['POST'])
def direct_route_planning():
    data = request.get_json()
    origin = data.get('origin')
    destination = data.get('destination')
    mode = data.get('mode', 'driving')  # 默认驾车模式
    
    if not origin or not destination:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # 选择合适的路线规划API
    if mode == 'driving':
        url = "https://restapi.amap.com/v3/direction/driving"
    elif mode == 'walking':
        url = "https://restapi.amap.com/v3/direction/walking"
    elif mode == 'bicycling':
        url = "https://restapi.amap.com/v4/direction/bicycling"
    else:
        return jsonify({'error': 'Invalid mode'}), 400
    
    # 直接调用高德API获取路线数据
    params = {
        "key": AMAP_KEY,
        "origin": origin,
        "destination": destination,
        "extensions": "all"
    }
    
    response = requests.get(url, params=params)
    return jsonify(response.json())

# 添加直接调用高德路线规划API的接口
@app.route('/api/weather', methods=['GET'])
def direct_weather():
    city = request.args.get('city', '北京')
    
    # 直接调用高德天气API
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "key": AMAP_KEY,
        "city": city,
        "extensions": "all"
    }
    
    response = requests.get(url, params=params)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True)
