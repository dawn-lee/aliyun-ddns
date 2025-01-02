import base64
import os

def create_icon():
    """创建一个简单的纯色图标"""
    from PIL import Image, ImageDraw
    
    # 创建一个 256x256 的图像
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制圆形背景
    draw.ellipse([10, 10, size-10, size-10], fill='#1890ff')
    
    # 确保 resources 目录存在
    os.makedirs('resources', exist_ok=True)
    
    # 保存图标
    img.save('resources/icon.png')
    print("图标文件已创建: resources/icon.png")

if __name__ == '__main__':
    create_icon() 