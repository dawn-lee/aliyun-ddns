from aliyunsdkcore.client import AcsClient
from aliyunsdkalidns.request.v20150109.DescribeDomainsRequest import DescribeDomainsRequest
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
import json
import requests
import re

class DNSUpdater:
    def __init__(self, config_manager):
        self.config = config_manager
        self.client = None
        self.init_client()

    def update_config(self, config):
        """更新配置并重新初始化客户端"""
        if isinstance(config, dict):
            # 如果传入的是字典，更新特定的配置项
            self.config.config.update(config)
        else:
            # 如果传入的是配置管理器，更新整个配置
            self.config = config
        
        # 重新初始化客户端
        self.init_client()

    def init_client(self):
        """初始化阿里云客户端"""
        try:
            access_key_id = self.config.config.get("access_key_id")
            access_key_secret = self.config.config.get("access_key_secret")
            
            if access_key_id and access_key_secret:
                self.client = AcsClient(
                    access_key_id,
                    access_key_secret,
                    'cn-hangzhou'
                )
                print("阿里云客户端初始化成功")  # 调试信息
            else:
                self.client = None
                print("未配置阿里云账号")  # 调试信息
                
        except Exception as e:
            self.client = None
            print(f"初始化阿里云客户端失败: {str(e)}")  # 调试信息
            raise Exception(f"初始化阿里云客户端失败: {str(e)}")

    def get_domains(self):
        """获取所有域名"""
        if not self.client:
            raise Exception("未配置阿里云账号")
            
        request = DescribeDomainsRequest()
        request.set_accept_format('json')
        
        try:
            response = self.client.do_action_with_exception(request)
            result = json.loads(response)
            return result.get("Domains", {}).get("Domain", [])
        except Exception as e:
            raise Exception(f"获取域名列表失败: {str(e)}")
            
    def get_domain_records(self, domain_name):
        """获取指定域名的所有解析记录（支持分页）"""
        if not self.client:
            raise Exception("未配置阿里云账号")
            
        all_records = []
        page_number = 1
        page_size = 100  # 每页获取100条记录
        
        while True:
            request = DescribeDomainRecordsRequest()
            request.set_accept_format('json')
            request.set_DomainName(domain_name)
            request.set_PageNumber(page_number)
            request.set_PageSize(page_size)
            
            try:
                response = self.client.do_action_with_exception(request)
                result = json.loads(response)
                
                records = result.get("DomainRecords", {}).get("Record", [])
                total_count = result.get("TotalCount", 0)
                
                all_records.extend(records)
                
                # 判断是否获取完所有记录
                if len(all_records) >= total_count:
                    break
                    
                page_number += 1
                
            except Exception as e:
                raise Exception(f"获取域名 {domain_name} 的记录失败: {str(e)}")
                
        return all_records

    def get_all_domain_records(self):
        """获取所有域名的所有记录"""
        all_records = []
        domains = self.get_domains()
        
        for domain in domains:
            try:
                domain_name = domain["DomainName"]
                print(f"正在获取域名 {domain_name} 的记录...")  # 调试信息
                records = self.get_domain_records(domain_name)
                print(f"域名 {domain_name} 获取到 {len(records)} 条记录")  # 调试信息
                all_records.extend(records)
            except Exception as e:
                print(f"获取域名 {domain_name} 的记录失败: {str(e)}")
                continue
                
        print(f"总共获取到 {len(all_records)} 条记录")  # 调试信息
        return all_records

    def get_current_ips(self):
        """同时获取当前的IPv4和IPv6地址"""
        ips = {"ipv4": None, "ipv6": None}
        
        try:
            # 获取IPv4
            response = requests.get('http://4.ipw.cn', timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            ipv4 = response.text.strip()
            
            # 验证IPv4格式
            if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ipv4):
                parts = [int(part) for part in ipv4.split('.')]
                if all(0 <= part <= 255 for part in parts):
                    ips["ipv4"] = ipv4
                    print(f"成功获取IPv4: {ipv4}")
        except Exception as e:
            print(f"获取IPv4失败: {str(e)}")
            
        try:
            # 获取IPv6
            response = requests.get('http://6.ipw.cn', timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            ipv6 = response.text.strip()
            
            # 验证IPv6格式
            if re.match(r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$', ipv6):
                ips["ipv6"] = ipv6
                print(f"成功获取IPv6: {ipv6}")
        except Exception as e:
            print(f"获取IPv6失败: {str(e)}")
            
        return ips

    def get_record_value(self, domain_name, rr, record_type="A"):
        """获取指定记录的当前值"""
        request = DescribeDomainRecordsRequest()
        request.set_accept_format('json')
        request.set_DomainName(domain_name)
        request.set_RRKeyWord(rr)
        request.set_Type(record_type)
        
        try:
            response = self.client.do_action_with_exception(request)
            result = json.loads(response)
            records = result.get("DomainRecords", {}).get("Record", [])
            
            for record in records:
                if record["RR"] == rr and record["Type"] == record_type:
                    return record["Value"]
            return None
        except Exception as e:
            print(f"获取记录值失败: {str(e)}")
            return None

    def update_record(self, record_id, rr, record_type, value, domain_name):
        """更新域名记录"""
        if not self.client:
            raise Exception("未配置阿里云账号")
            
        # 先查询当前实际记录值
        current_value = self.get_record_value(domain_name, rr, record_type)
        if current_value == value:
            print(f"记录 {rr}.{domain_name} ({record_type}) 的当前值已经是 {value}，无需更新")
            return True
            
        # 处理主机记录格式
        rr = rr.strip()
        if rr.endswith('.'):
            rr = rr[:-1]
            
        # 确保记录类型正确
        record_type = record_type.upper()
        if record_type not in ['A', 'AAAA']:
            raise Exception(f"不支持的记录类型: {record_type}")
            
        # 验证IP地址格式
        if record_type == 'A':
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        else:  # AAAA
            ip_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
            
        if not re.match(ip_pattern, value.strip()):
            raise Exception(f"无效的IP地址格式: {value}")
            
        request = UpdateDomainRecordRequest()
        request.set_accept_format('json')
        request.set_RecordId(record_id)
        request.set_RR(rr)
        request.set_Type(record_type)
        request.set_Value(value.strip())
        request.set_TTL(600)
        request.set_Line("default")
        
        # 添加重试机制
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                print(f"更新记录参数: RecordId={record_id}, RR={rr}, Type={record_type}, Value={value}")
                response = self.client.do_action_with_exception(request)
                result = json.loads(response)
                print(f"更新成功，尝试次数: {attempt + 1}")
                return True
            except Exception as e:
                error_msg = str(e)
                print(f"更新失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                
                if "DomainRecordDuplicate" in error_msg:
                    # 如果是重复记录错误，检查实际值是否已更新
                    actual_value = self.get_record_value(domain_name, rr, record_type)
                    if actual_value == value:
                        print(f"记录已经更新为目标值: {value}")
                        return True
                
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                    
                raise Exception(f"更新记录失败: {error_msg}")

    def sync_records(self, current_ips=None):
        """同步所有选中的记录
        current_ips: 可选的当前IP字典，包含ipv4和ipv6
        """
        if not self.client:
            raise Exception("未配置阿里云账号")
            
        try:
            # 如果没有传入IP，则获取一次
            if current_ips is None:
                current_ips = self.get_current_ips()
                
            current_ipv4 = current_ips["ipv4"]
            current_ipv6 = current_ips["ipv6"]
            
            if not current_ipv4 and not current_ipv6:
                raise Exception("无法获取任何IP地址")
                
        except Exception as e:
            raise Exception(f"获取IP失败: {str(e)}")
            
        sync_records = self.config.config.get("sync_records", [])
        if not sync_records:
            return []
            
        print(f"需要同步的记录数: {len(sync_records)}")
        
        results = []
        for record in sync_records:
            try:
                if record["Type"] in ["A", "AAAA"]:
                    # 根据记录类型选择对应的IP
                    current_ip = current_ipv4 if record["Type"] == "A" else current_ipv6
                    
                    # 如果是IPv6记录但没有获取到IPv6地址，则跳过
                    if record["Type"] == "AAAA" and not current_ipv6:
                        results.append({
                            "domain": record["DomainName"],
                            "rr": record["RR"],
                            "type": "AAAA",
                            "status": "skipped",
                            "message": "未能获取IPv6地址"
                        })
                        continue
                        
                    # 如果是IPv4记录但没有获取到IPv4地址，则跳过
                    if record["Type"] == "A" and not current_ipv4:
                        results.append({
                            "domain": record["DomainName"],
                            "rr": record["RR"],
                            "type": "A",
                            "status": "skipped",
                            "message": "未能获取IPv4地址"
                        })
                        continue
                        
                    # 检查当前实际记录值
                    actual_value = self.get_record_value(record["DomainName"], record["RR"], record["Type"])
                    if actual_value == current_ip:
                        results.append({
                            "domain": record["DomainName"],
                            "rr": record["RR"],
                            "type": record["Type"],
                            "old_ip": actual_value,
                            "new_ip": current_ip,
                            "status": "skipped",
                            "message": f"IP未变化，无需更新: {current_ip}"
                        })
                        continue
                        
                    print(f"需要更新{record['Type']}记录: {record['RR']}.{record['DomainName']} 从 {actual_value} 到 {current_ip}")
                    if self.update_record(
                        record["RecordId"],
                        record["RR"],
                        record["Type"],
                        current_ip,
                        record["DomainName"]
                    ):
                        record["Value"] = current_ip
                        results.append({
                            "domain": record["DomainName"],
                            "rr": record["RR"],
                            "type": record["Type"],
                            "old_ip": actual_value,
                            "new_ip": current_ip,
                            "status": "success",
                            "message": f"更新成功: {record['RR']}.{record['DomainName']} -> {current_ip}"
                        })
                else:
                    results.append({
                        "domain": record["DomainName"],
                        "rr": record["RR"],
                        "type": record["Type"],
                        "status": "skipped",
                        "message": f"不支持的记录类型: {record['Type']}"
                    })
            except Exception as e:
                print(f"更新记录失败: {str(e)}")
                results.append({
                    "domain": record["DomainName"],
                    "rr": record["RR"],
                    "type": record["Type"],
                    "status": "error",
                    "message": f"更新失败: {str(e)}"
                })
        
        self.config.config["sync_records"] = sync_records
        self.config.save_config()
        
        return results 