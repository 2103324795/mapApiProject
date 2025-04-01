from flask import Flask, render_template, jsonify, request
import os
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建简化版的Flask应用 - 专为Vercel设计
app = Flask(__name__, static_folder='../static', template_folder='../templates')

# Vercel必须的配置
app.config['JSON_AS_ASCII'] = False

# 获取API密钥（Vercel环境变量）
AMAP_KEY = os.getenv('AMAP_KEY', '46f8aebbd7c81272533debc531a7bfbd')

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/search_poi', methods=['POST'])
def search_poi():
    """核心功能：POI搜索"""
    data = request.json
    keywords = data.get('keywords', '')
    location = data.get('location', '')
    
    # 调用高德API
    url = "https://restapi.amap.com/v3/place/around"
    params = {
        'key': AMAP_KEY,
        'keywords': keywords,
        'location': location,
        'radius': 3000,
        'output': 'json'
    }
    
    response = requests.get(url, params=params)
    return jsonify(response.json())

# Vercel需要的入口点
handler = app
