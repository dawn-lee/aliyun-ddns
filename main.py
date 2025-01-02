import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow
from core.config_manager import ConfigManager
from core.dns_updater import DNSUpdater

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的路径
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def main():
    # 启用高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("AliyunDDNS")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("YourOrganization")
    app.setOrganizationDomain("your-domain.com")
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 初始化DNS更新器
    dns_updater = DNSUpdater(config_manager)
    
    # 创建主窗口
    window = MainWindow(config_manager, dns_updater)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 