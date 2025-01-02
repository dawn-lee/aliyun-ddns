import PyInstaller.__main__
import os
import shutil

def build_app():
    """打包应用为可执行文件"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 清理之前的构建文件
    dist_dir = os.path.join(project_root, 'dist')
    build_dir = os.path.join(project_root, 'build')
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
        
    # 准备资源文件
    resources_dir = os.path.join(project_root, 'resources')
    if not os.path.exists(resources_dir):
        os.makedirs(resources_dir)
        
    # PyInstaller 参数
    params = [
        'main.py',  # 主程序入口
        '--name=AliyunDDNS',  # 可执行文件名
        '--windowed',  # 无控制台窗口
        '--icon=resources/icon.png',  # 应用图标
        '--add-data=resources/icon.png;resources',  # 添加资源文件
        '--noconfirm',  # 覆盖现有文件
        '--clean',  # 清理临时文件
        '--onefile',  # 打包成单个文件
        # 添加隐式导入
        '--hidden-import=PyQt5.sip',
        '--hidden-import=aliyunsdkcore',
        '--hidden-import=aliyunsdkalidns',
    ]
    
    # 运行 PyInstaller
    PyInstaller.__main__.run(params)
    
    print("打包完成！可执行文件位于 dist 目录")

if __name__ == '__main__':
    build_app() 