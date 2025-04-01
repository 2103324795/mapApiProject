# 地点间POI查询API

## 项目介绍
这个API可以查询两个地点之间的特定场所（如书店、咖啡馆、商场等）。用户提供两个地点（如某某高铁站、某某地铁站等）和想要查找的场所类型，API会返回一个HTML页面，展示这两个地点之间的相关场所。

## 功能特点
- 支持任意两个地点之间的POI查询
- 支持多种场所类型（书店、咖啡馆、商场等）
- 直观的HTML页面展示查询结果
- 集成高德地图API，提供准确的地理位置信息

## 使用方法
### API接口
```
GET /search_between_locations
```

### 请求参数
- `location1`: 第一个地点名称（如"北京西站"）
- `location2`: 第二个地点名称（如"天安门"）
- `poi_type`: 要查询的场所类型（如"书店"、"咖啡馆"、"商场"等）

### 示例请求
```
GET /search_between_locations?location1=北京西站&location2=天安门&poi_type=咖啡馆
```

### 返回结果
返回一个HTML页面，展示两个地点之间的指定类型场所，包括：
- 地图显示两个地点及中间的场所
- 场所列表，包含名称、地址、电话等信息
- 到两个地点的距离信息

## 技术实现
- 后端：Python + Flask
- 地图服务：高德地图API
- 前端：HTML + CSS + JavaScript

## 安装与运行
1. 安装依赖：
```
pip install -r requirements.txt
```

2. 运行应用：
```
python app.py
```

3. 访问API：
在浏览器中访问 `http://localhost:5000`

## 注意事项
- 使用前需要配置高德地图API密钥
- 查询结果的准确性依赖于高德地图API的数据
