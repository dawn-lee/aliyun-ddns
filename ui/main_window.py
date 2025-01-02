from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                           QHeaderView, QApplication, QSystemTrayIcon, QMenu,
                           QAction, QStyle)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor, QIcon, QScreen
from datetime import datetime, timedelta
import os
import sys
import winreg
from .config_dialog import ConfigDialog
import ctypes

class MainWindow(QMainWindow):
    def __init__(self, config_manager, dns_updater):
        super().__init__()
        self.setWindowIcon(QIcon("resources/icon.png"))
        # 设置高DPI缩放
        self.setup_high_dpi()
        
        # 获取合适尺寸的图标
        icon = self.get_appropriate_icon()
        
        self.config = config_manager
        self.dns_updater = dns_updater
        # 先创建托盘图标，确保它在窗口关闭时仍然存在
        self.setup_tray(icon)
        self.setup_ui()
        self.last_update_time = None
        
        # 检查自启动状态
        self.check_autostart()
        
        # 设置窗口标题和图标
        self.setWindowTitle("阿里云DNS解析客户端")
        self.setWindowIcon(icon)
        
        # 使用定时器延迟初始化
        QTimer.singleShot(1000, self.delayed_init)

    def setup_high_dpi(self):
        """设置高DPI支持"""
        # Windows 系统高DPI支持
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except:
            pass
            
        # 获取主屏幕
        screen = QApplication.primaryScreen()
        if screen:
            dpi = screen.logicalDotsPerInch()
            scale_factor = dpi / 96.0  # 96 DPI is the standard resolution
        else:
            scale_factor = 1.0
            
        # 设置基础字体大小
        base_font_size = 9  # Windows 默认字体大小
        scaled_font_size = int(base_font_size * scale_factor)
        
        # 设置全局样式
        self.setStyleSheet(f"""
            QLabel {{
                font-size: {scaled_font_size + 3}pt;
                color: #333333;
                margin: 5px 0;
            }}
            QPushButton {{
                font-size: {scaled_font_size + 1}pt;
                padding: {8 * scale_factor}px {16 * scale_factor}px;
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: {4 * scale_factor}px;
                min-width: {80 * scale_factor}px;
            }}
            QPushButton:hover {{
                background-color: #40a9ff;
            }}
            QTableWidget {{
                font-size: {scaled_font_size}pt;
                border: 1px solid #e8e8e8;
                border-radius: {4 * scale_factor}px;
            }}
            QHeaderView::section {{
                font-size: {scaled_font_size}pt;
                background-color: #fafafa;
                padding: {8 * scale_factor}px;
                border: none;
                border-bottom: 1px solid #e8e8e8;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: {8 * scale_factor}px;
            }}
            QMenu {{
                font-size: {scaled_font_size}pt;
                padding: 4px;
            }}
            QMenu::item {{
                padding: {6 * scale_factor}px {20 * scale_factor}px;
            }}
            QMenu::item:selected {{
                background-color: #f0f0f0;
            }}
        """)
        
        # 设置窗口基础大小
        base_width = 800
        base_height = 600
        self.setMinimumSize(
            int(base_width * scale_factor),
            int(base_height * scale_factor)
        )

    def delayed_init(self):
        """延迟初始化，在窗口显示后执行"""
        print("开始初始化定时更新...")  # 调试信息
        self.setup_timer()
        
        # 初始化 last_update_time
        self.last_update_time = None
        self.next_update_label.setText("下次更新: 等待首次更新")
        
        # 如果配置了账号，执行首次更新
        if (self.config.config.get("access_key_id") and 
            self.config.config.get("access_key_secret")):
            print("检测到已配置账号，准备执行首次更新...")  # 调试信息
            QTimer.singleShot(2000, self.first_update)

    def first_update(self):
        """首次更新"""
        print("执行首次更新...")  # 调试信息
        try:
            self.check_and_update()
            self.status_label.setText("状态: 初始化完成")
        except Exception as e:
            self.status_label.setText(f"状态: 初始化失败 - {str(e)}")
            print(f"首次更新失败: {str(e)}")  # 调试信息

    def setup_tray(self, icon):
        """设置系统托盘"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 使用相对路径和绝对路径都尝试加载图标
        icon_paths = [
            "resources/icon.png",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources/icon.png"),
            os.path.join(os.path.dirname(sys.executable), "resources/icon.png")
        ]
        
        icon_loaded = False
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
                icon_loaded = True
                break
                
        if not icon_loaded:
            print("警告: 未能找到图标文件")
            # 使用系统默认图标
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 显示/隐藏窗口动作
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_main_window)
        tray_menu.addAction(show_action)
        
        # 自启动选项
        self.autostart_action = QAction("开机自启动", self)
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(self.is_autostart_enabled())
        self.autostart_action.triggered.connect(self.toggle_autostart)
        tray_menu.addAction(self.autostart_action)
        
        # 添加分隔线
        tray_menu.addSeparator()
        
        # 退出动作
        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 显示托盘图标
        self.tray_icon.show()
        
        # 连接托盘图标的信号
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def show_main_window(self):
        """显示主窗口"""
        self.show()
        self.activateWindow()  # 激活窗口
        self.raise_()  # 将窗口提升到最前

    def tray_icon_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()
        elif reason == QSystemTrayIcon.Context:
            # 确保右键菜单正确显示
            self.tray_icon.contextMenu().show()

    def closeEvent(self, event):
        """重写关闭事件"""
        if self.tray_icon.isVisible():
            event.ignore()  # 忽略关闭事件
            self.hide()     # 隐藏窗口
            
            # 显示托盘提示
            self.tray_icon.showMessage(
                "阿里云DNS解析客户端",
                "程序已最小化到系统托盘运行，双击图标可以重新打开窗口",
                QSystemTrayIcon.Information,
                3000  # 显示3秒
            )
        else:
            event.accept()  # 如果托盘图标不可见，则正常关闭

    def quit_application(self):
        """退出应用程序"""
        # 保存配置
        self.config.save_config()
        
        # 隐藏托盘图标
        self.tray_icon.hide()
        
        # 退出应用
        QApplication.quit()

    def get_startup_path(self):
        """获取应用程序路径"""
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后的路径
            return sys.executable
        else:
            # 开发环境下的路径
            return os.path.abspath(sys.argv[0])

    def is_autostart_enabled(self):
        """检查是否启用了自启动"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, "AliyunDDNS")
                return True
            except WindowsError:
                return False
            finally:
                winreg.CloseKey(key)
        except WindowsError:
            return False

    def check_autostart(self):
        """检查并更新自启动状态"""
        if hasattr(self, 'autostart_action'):
            self.autostart_action.setChecked(self.is_autostart_enabled())

    def toggle_autostart(self, state):
        """切换自启动状态"""
        key = None
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_READ
            )
            
            if state:
                # 启用自启动
                app_path = self.get_startup_path()
                winreg.SetValueEx(
                    key,
                    "AliyunDDNS",
                    0,
                    winreg.REG_SZ,
                    f'"{app_path}"'
                )
                self.tray_icon.showMessage(
                    "自启动已启用",
                    "程序将在系统启动时自动运行",
                    QSystemTrayIcon.Information,
                    2000
                )
            else:
                # 禁用自启动
                try:
                    winreg.DeleteValue(key, "AliyunDDNS")
                    self.tray_icon.showMessage(
                        "自启动已禁用",
                        "程序将不会在系统启动时自动运行",
                        QSystemTrayIcon.Information,
                        2000
                    )
                except WindowsError:
                    pass
        except Exception as e:
            self.tray_icon.showMessage(
                "错误",
                f"设置自启动失败: {str(e)}",
                QSystemTrayIcon.Warning,
                2000
            )
            # 恢复复选框状态
            self.autostart_action.setChecked(not state)
        finally:
            if key:
                winreg.CloseKey(key)

    def setup_timer(self):
        """设置定时器，每5分钟执行一次更新"""
        print("设置定时更新...")  # 调试信息
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_and_update)
        self.update_timer.start(5 * 60 * 1000)  # 5分钟 = 5 * 60 * 1000毫秒
        
        # 更新倒计时的定时器
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # 每秒更新一次倒计时

    def update_countdown(self):
        """更新倒计时显示"""
        if not hasattr(self, 'last_update_time') or self.last_update_time is None:
            self.next_update_label.setText("下次更新: 等待首次更新")
            return
            
        now = datetime.now()
        next_update = self.last_update_time + timedelta(minutes=5)
        
        if now >= next_update:
            self.next_update_label.setText("下次更新: 即将进行")
            return
            
        remaining = next_update - now
        minutes = remaining.seconds // 60
        seconds = remaining.seconds % 60
        self.next_update_label.setText(f"下次更新: {minutes:02d}:{seconds:02d}")

    def setup_ui(self):
        """设置UI"""
        # 获取缩放因子
        screen = QApplication.primaryScreen()
        if screen:
            dpi = screen.logicalDotsPerInch()
            scale_factor = dpi / 96.0
        else:
            scale_factor = 1.0
            
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态面板
        status_panel = QWidget()
        status_layout = QHBoxLayout(status_panel)
        
        # 状态信息
        status_info = QWidget()
        status_info_layout = QVBoxLayout(status_info)
        self.status_label = QLabel("当前状态: 未运行")
        self.ip_label = QLabel("当前IP: 未检测")
        self.next_update_label = QLabel("下次更新: --:--")
        self.last_update_label = QLabel("上次更新: 未更新")
        
        status_info_layout.addWidget(self.status_label)
        status_info_layout.addWidget(self.ip_label)
        status_info_layout.addWidget(self.next_update_label)
        status_info_layout.addWidget(self.last_update_label)
        
        # 按钮面板
        button_panel = QWidget()
        button_layout = QVBoxLayout(button_panel)
        self.config_btn = QPushButton("配置账号")
        self.refresh_btn = QPushButton("立即刷新")
        
        # 设置按钮固定宽度（考虑缩放）
        button_width = int(100 * scale_factor)
        self.config_btn.setFixedWidth(button_width)
        self.refresh_btn.setFixedWidth(button_width)
        
        button_layout.addWidget(self.config_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        
        status_layout.addWidget(status_info)
        status_layout.addWidget(button_panel)
        
        # 记录表格
        self.records_table = QTableWidget()
        self.records_table.setColumnCount(3)
        self.records_table.setHorizontalHeaderLabels(['域名记录', '状态', '消息'])
        
        # 设置表格列宽比例（考虑缩放）
        header = self.records_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        # 设置固定列宽（考虑缩放）
        self.records_table.setColumnWidth(0, int(200 * scale_factor))
        self.records_table.setColumnWidth(1, int(80 * scale_factor))
        
        # 设置表格行高（考虑缩放）
        self.records_table.verticalHeader().setDefaultSectionSize(int(40 * scale_factor))
        
        # 添加到主布局
        layout.addWidget(status_panel)
        layout.addWidget(self.records_table)
        
        # 绑定事件
        self.config_btn.clicked.connect(self.show_config_dialog)
        self.refresh_btn.clicked.connect(self.manual_refresh)

    def show_config_dialog(self):
        dialog = ConfigDialog(self.config, self.dns_updater, self)
        if dialog.exec_():
            self.check_and_update()

    def manual_refresh(self):
        """手动刷新"""
        self.status_label.setText("状态: 手动刷新中...")
        # 立即更新界面
        QApplication.processEvents()
        
        try:
            self.check_and_update()
            # 重置定时器
            self.reset_timer()
        except Exception as e:
            self.status_label.setText(f"状态: 刷新失败 - {str(e)}")
            return
            
        self.status_label.setText("状态: 运行中")

    def reset_timer(self):
        """重置更新定时器"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
            self.update_timer.start(5 * 60 * 1000)  # 重新开始5分钟计时
            print("定时器已重置，下次更新将在5分钟后进行")  # 调试信息
            
        # 更新下次更新时间显示
        next_update = datetime.now() + timedelta(minutes=5)
        self.next_update_label.setText(
            f"下次更新: {next_update.strftime('%H:%M:%S')}"
        )

    def check_and_update(self):
        """检查并更新DNS记录"""
        if not self.config.config.get("sync_records"):
            print("没有需要同步的记录")  # 调试信息
            self.status_label.setText("状态: 未配置同步记录")
            return
            
        print("开始检查和更新DNS记录...")  # 调试信息
        try:
            # 获取当前IP地址（只获取一次）
            current_ips = self.dns_updater.get_current_ips()
            
            # 更新IP显示
            ip_text = []
            if current_ips["ipv4"]:
                ip_text.append(f"IPv4: {current_ips['ipv4']}")
            if current_ips["ipv6"]:
                ip_text.append(f"IPv6: {current_ips['ipv6']}")
            
            self.ip_label.setText(" | ".join(ip_text) if ip_text else "未能获取IP地址")
            
            # 同步记录（传入已获取的IP）
            results = self.dns_updater.sync_records(current_ips)
            self.update_sync_status(results)
            
            # 更新时间
            self.last_update_time = datetime.now()
            self.last_update_label.setText(
                f"上次更新: {self.last_update_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
        except Exception as e:
            error_msg = str(e)
            print(f"更新失败: {error_msg}")  # 调试信息
            self.status_label.setText(f"状态: 更新失败 - {error_msg}")

    def update_sync_status(self, results):
        """更新同步状态到表格"""
        self.records_table.setRowCount(0)
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for result in results:
            row = self.records_table.rowCount()
            self.records_table.insertRow(row)
            
            domain_text = f"{result['rr']}.{result['domain']}"
            if result['rr'] == '@':
                domain_text = result['domain']
                
            self.records_table.setItem(row, 0, QTableWidgetItem(domain_text))
            self.records_table.setItem(row, 1, QTableWidgetItem(result['status']))
            self.records_table.setItem(row, 2, QTableWidgetItem(result['message']))
            
            # 设置状态列的颜色和计数
            if result['status'] == 'success':
                self.records_table.item(row, 1).setBackground(QColor('#e6f7ff'))
                success_count += 1
            elif result['status'] == 'error':
                self.records_table.item(row, 1).setBackground(QColor('#fff1f0'))
                error_count += 1
            else:  # skipped
                self.records_table.item(row, 1).setBackground(QColor('#f6ffed'))
                skipped_count += 1
        
        # 更新状态栏显示结果统计
        status_text = f"状态: 更新完成 ("
        if success_count > 0:
            status_text += f"成功: {success_count} "
        if error_count > 0:
            status_text += f"失败: {error_count} "
        if skipped_count > 0:
            status_text += f"跳过: {skipped_count} "
        status_text += ")"
        
        self.status_label.setText(status_text)

    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        print("主窗口显示")  # 调试信息
        self.status_label.setText("状态: 正在初始化...")

    def get_appropriate_icon(self):
        """根据屏幕 DPI 获取合适尺寸的图标"""
        screen = QApplication.primaryScreen()
        if screen:
            dpi = screen.logicalDotsPerInch()
            scale_factor = dpi / 96.0
        else:
            scale_factor = 1.0
            
        # 选择合适的图标尺寸
        if scale_factor <= 1:
            size = 32
        elif scale_factor <= 1.5:
            size = 48
        elif scale_factor <= 2:
            size = 64
        else:
            size = 128
            
        icon_path = f"resources/icon_{size}x{size}.png"
        return QIcon(icon_path)