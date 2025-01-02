from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QTableWidget,
                           QTableWidgetItem, QCheckBox, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QScreen, QColor
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest

class ConfigDialog(QDialog):
    def __init__(self, config_manager, dns_updater, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.dns_updater = dns_updater
        self.domain_records = []
        
        # 获取缩放因子
        screen = self.screen()
        if screen:
            dpi = screen.logicalDotsPerInch()
            self.scale_factor = dpi / 96.0
        else:
            self.scale_factor = 1.0
        
        self.setup_ui()
        
        # 如果已经配置了AccessKey，直接加载域名记录
        if (self.config.config.get("access_key_id") and 
            self.config.config.get("access_key_secret")):
            self.load_domain_records()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("账号配置")
        # 设置窗口大小，增加基础宽度
        base_width = 700  # 从600增加到700
        base_height = 450  # 保持高度不变
        self.setFixedSize(
            int(base_width * self.scale_factor),
            int(base_height * self.scale_factor)
        )
        
        layout = QVBoxLayout(self)
        
        # 设置布局间距
        layout.setSpacing(int(8 * self.scale_factor))
        layout.setContentsMargins(
            int(16 * self.scale_factor),
            int(16 * self.scale_factor),
            int(16 * self.scale_factor),
            int(16 * self.scale_factor)
        )
        
        # AccessKey配置区域
        credentials_group = QVBoxLayout()
        credentials_group.setSpacing(int(8 * self.scale_factor))
        
        # AccessKey ID
        ak_id_label = QLabel("AccessKey ID:")
        self.ak_id_input = QLineEdit()
        self.ak_id_input.setText(self.config.config.get("access_key_id", ""))
        credentials_group.addWidget(ak_id_label)
        credentials_group.addWidget(self.ak_id_input)
        
        # AccessKey Secret
        ak_secret_label = QLabel("AccessKey Secret:")
        self.ak_secret_input = QLineEdit()
        self.ak_secret_input.setText(self.config.config.get("access_key_secret", ""))
        self.ak_secret_input.setEchoMode(QLineEdit.Password)
        credentials_group.addWidget(ak_secret_label)
        credentials_group.addWidget(self.ak_secret_input)
        
        # 测试连接按钮
        test_btn = QPushButton("测试连接并获取域名记录")
        test_btn.clicked.connect(self.test_connection)
        credentials_group.addWidget(test_btn)
        
        layout.addLayout(credentials_group)
        
        # 域名记录表格
        records_label = QLabel("域名记录列表:")
        layout.addWidget(records_label)
        
        self.records_table = QTableWidget()
        self.records_table.setColumnCount(5)
        self.records_table.setHorizontalHeaderLabels(['选择', '完整域名', '主机记录', '记录类型', '记录值'])
        
        # 设置表格样式
        header = self.records_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 复选框列
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # 完整域名
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 主机记录
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 记录类型
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 记录值
        
        # 设置列宽
        self.records_table.setColumnWidth(0, int(40 * self.scale_factor))  # 复选框列
        self.records_table.setColumnWidth(1, int(120 * self.scale_factor))  # 完整域名列
        
        # 确保记录值列有足够空间显示IPv6地址
        min_value_column_width = int(280 * self.scale_factor)
        self.records_table.setColumnWidth(4, min_value_column_width)
        
        # 设置表格高度
        self.records_table.setMinimumHeight(int(200 * self.scale_factor))
        layout.addWidget(self.records_table)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        
        # 设置按钮大小
        btn_width = int(80 * self.scale_factor)
        btn_height = int(28 * self.scale_factor)
        save_btn.setFixedSize(btn_width, btn_height)
        cancel_btn.setFixedSize(btn_width, btn_height)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        save_btn.clicked.connect(self.save_config)
        cancel_btn.clicked.connect(self.reject)
        
        # 设置整体样式
        base_font_size = 9  # 基础字体大小
        scaled_font_size = int(base_font_size * self.scale_factor)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: white;
            }}
            QLabel {{
                font-size: {scaled_font_size}pt;
                color: #333333;
                margin-top: {int(4 * self.scale_factor)}px;
            }}
            QPushButton {{
                font-size: {scaled_font_size}pt;
                padding: {int(6 * self.scale_factor)}px {int(12 * self.scale_factor)}px;
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: {int(4 * self.scale_factor)}px;
            }}
            QPushButton:hover {{
                background-color: #40a9ff;
            }}
            QLineEdit {{
                font-size: {scaled_font_size}pt;
                padding: {int(6 * self.scale_factor)}px;
                border: 1px solid #d9d9d9;
                border-radius: {int(4 * self.scale_factor)}px;
                min-height: {int(28 * self.scale_factor)}px;
            }}
            QLineEdit:focus {{
                border-color: #40a9ff;
            }}
            QTableWidget {{
                font-size: {scaled_font_size}pt;
                border: 1px solid #e8e8e8;
                border-radius: {int(4 * self.scale_factor)}px;
                gridline-color: #f0f0f0;
            }}
            QHeaderView::section {{
                font-size: {scaled_font_size}pt;
                background-color: #fafafa;
                padding: {int(6 * self.scale_factor)}px;
                border: none;
                border-bottom: 1px solid #e8e8e8;
            }}
            QTableWidget::item {{
                padding: {int(6 * self.scale_factor)}px;
            }}
            QCheckBox {{
                font-size: {scaled_font_size}pt;
            }}
        """)

    def load_domain_records(self):
        """加载域名记录"""
        try:
            self.domain_records = self.dns_updater.get_all_domain_records()
            print(f"加载到 {len(self.domain_records)} 条记录")  # 调试信息
            self.update_records_table()
        except Exception as e:
            print(f"加载域名记录失败: {str(e)}")  # 调试信息
            QMessageBox.warning(self, "警告", f"加载域名记录失败: {str(e)}")

    def test_connection(self):
        """测试连接并获取域名记录"""
        # 临时保存当前输入的 AccessKey
        temp_ak_id = self.ak_id_input.text().strip()
        temp_ak_secret = self.ak_secret_input.text().strip()
        
        if not temp_ak_id or not temp_ak_secret:
            QMessageBox.warning(self, "错误", "请输入 AccessKey ID 和 Secret")
            return
            
        try:
            # 临时更新 DNS 更新器的配置
            self.dns_updater.update_config({
                "access_key_id": temp_ak_id,
                "access_key_secret": temp_ak_secret
            })
            
            # 获取所有域名记录
            self.domain_records = self.dns_updater.get_all_domain_records()
            print(f"获取到 {len(self.domain_records)} 条记录")  # 调试信息
            
            if not self.domain_records:
                QMessageBox.warning(self, "提示", "未获取到任何域名记录")
                return
                
            # 更新表格显示
            self.update_records_table()
            
            QMessageBox.information(self, "成功", f"连接成功，已获取 {len(self.domain_records)} 条记录")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接失败: {str(e)}")
            self.domain_records = []
            self.records_table.setRowCount(0)

    def update_records_table(self):
        """更新记录表格显示"""
        self.records_table.setRowCount(0)
        print(f"准备显示 {len(self.domain_records)} 条记录")  # 调试信息
        
        # 获取已选择的记录列表
        selected_records = self.config.config.get("sync_records", [])
        print(f"已选择的记录数: {len(selected_records)}")  # 调试信息
        
        # 打印已选择的记录信息用于调试
        for selected in selected_records:
            print(f"已选择记录: {selected.get('RR', '')}.{selected.get('DomainName', '')} "
                  f"(RecordId: {selected.get('RecordId', '')})")
        
        for record in self.domain_records:
            # 显示 A 和 AAAA 记录
            if record["Type"] not in ["A", "AAAA"]:
                print(f"跳过非DNS记录: {record['RR']}.{record['DomainName']} ({record['Type']})")  # 调试信息
                continue
                
            row = self.records_table.rowCount()
            self.records_table.insertRow(row)
            
            # 添加复选框
            checkbox = QCheckBox()
            # 检查记录是否在已选择列表中
            is_selected = any(
                selected["RecordId"] == record["RecordId"] 
                for selected in selected_records
            )
            print(f"记录 {record['RR']}.{record['DomainName']} "
                  f"(RecordId: {record['RecordId']}) 选中状态: {is_selected}")  # 调试信息
            checkbox.setChecked(is_selected)
            self.records_table.setCellWidget(row, 0, checkbox)
            
            # 添加记录信息
            domain_text = f"{record['RR']}.{record['DomainName']}"
            if record['RR'] == '@':
                domain_text = record['DomainName']
                
            self.records_table.setItem(row, 1, QTableWidgetItem(domain_text))
            self.records_table.setItem(row, 2, QTableWidgetItem(record["RR"]))
            self.records_table.setItem(row, 3, QTableWidgetItem(record["Type"]))
            self.records_table.setItem(row, 4, QTableWidgetItem(record["Value"]))
            
            print(f"添加记录到表格: {domain_text}")  # 调试信息

    def save_config(self):
        """保存配置"""
        # 保存 AccessKey 配置
        self.config.config["access_key_id"] = self.ak_id_input.text().strip()
        self.config.config["access_key_secret"] = self.ak_secret_input.text().strip()
        
        # 保存选中的记录
        selected_records = []
        for row in range(self.records_table.rowCount()):
            checkbox = self.records_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                record_id = self.domain_records[row]["RecordId"]
                # 查找完整的记录信息
                record = next(
                    (r for r in self.domain_records if r["RecordId"] == record_id),
                    None
                )
                if record:
                    selected_records.append(record)
                    print(f"保存选中记录: {record['RR']}.{record['DomainName']}")  # 调试信息
        
        self.config.config["sync_records"] = selected_records
        print(f"保存的记录数: {len(selected_records)}")  # 调试信息
        
        # 保存配置文件
        self.config.save_config()
        
        # 更新 DNS 更新器的配置
        self.dns_updater.update_config(self.config)
        
        self.accept() 