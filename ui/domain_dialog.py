from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QComboBox, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt

class DomainRecordDialog(QDialog):
    def __init__(self, config_manager, dns_updater, parent=None, record=None):
        super().__init__(parent)
        self.config = config_manager
        self.dns_updater = dns_updater
        self.record = record
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("域名记录管理")
        self.setFixedWidth(400)
        layout = QVBoxLayout(self)
        
        # 表单样式
        form_style = """
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #40a9ff;
                outline: none;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
        """
        self.setStyleSheet(form_style)
        
        # 域名
        layout.addWidget(QLabel("域名:"))
        self.domain_input = QLineEdit()
        layout.addWidget(self.domain_input)
        
        # 主机记录
        layout.addWidget(QLabel("主机记录:"))
        self.rr_input = QLineEdit()
        layout.addWidget(self.rr_input)
        
        # 记录类型
        layout.addWidget(QLabel("记录类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(['A', 'AAAA', 'CNAME', 'MX', 'TXT'])
        layout.addWidget(self.type_combo)
        
        # 记录值
        layout.addWidget(QLabel("记录值:"))
        self.value_input = QLineEdit()
        layout.addWidget(self.value_input)
        
        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        
        for btn in [save_btn, cancel_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1890ff;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #40a9ff;
                }
            """)
        
        cancel_btn.setStyleSheet(cancel_btn.styleSheet().replace('#1890ff', '#ff4d4f'))
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # 如果是编辑模式，填充现有数据
        if self.record:
            self.domain_input.setText(self.record["domain"])
            self.rr_input.setText(self.record["rr"])
            self.type_combo.setCurrentText(self.record["type"])
            self.value_input.setText(self.record["value"])
        
        # 绑定事件
        save_btn.clicked.connect(self.save_record)
        cancel_btn.clicked.connect(self.reject)
        
    def save_record(self):
        domain = self.domain_input.text().strip()
        rr = self.rr_input.text().strip()
        record_type = self.type_combo.currentText()
        value = self.value_input.text().strip()
        
        if not all([domain, rr, value]):
            QMessageBox.warning(self, "错误", "请填写所有必填项")
            return
            
        record = {
            "domain": domain,
            "rr": rr,
            "type": record_type,
            "value": value
        }
        
        records = self.config.config.get("domain_records", [])
        
        # 检查是否存在重复记录
        if not self.record:  # 新增模式
            for r in records:
                if r["domain"] == domain and r["rr"] == rr:
                    QMessageBox.warning(self, "错误", "该记录已存在")
                    return
            records.append(record)
        else:  # 编辑模式
            for i, r in enumerate(records):
                if r["domain"] == self.record["domain"] and r["rr"] == self.record["rr"]:
                    records[i] = record
                    break
                    
        self.config.config["domain_records"] = records
        self.config.save_config()
        self.accept() 