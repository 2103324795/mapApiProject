# 纯净的Vercel函数 - 不依赖Flask
import json

def handler(event, context):
    """处理Vercel的请求的函数"""
    # 返回内容
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html"
        },
        "body": """
        <!DOCTYPE html>
        <html>
        <head>
            <title>高德地图测试</title>
            <meta charset="UTF-8">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center;
                    margin: 0;
                    padding: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    color: white;
                }
                h1 { 
                    font-size: 2.5rem; 
                    margin-bottom: 1rem;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }
                p { 
                    font-size: 1.2rem; 
                    margin-bottom: 2rem;
                }
                .success {
                    background-color: rgba(255, 255, 255, 0.2);
                    padding: 20px;
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <h1>部署成功！</h1>
            <div class="success">
                <p>恭喜，你的Vercel函数已经成功部署！</p>
                <p>这是一个极简版本，用于测试Vercel能否正常工作。</p>
                <p>下一步，我们可以逐步添加地图功能。</p>
            </div>
        </body>
        </html>
        """
    }
