"""
IP EDC 配置查詢工具 - 查詢指定 IP 是否有設定 GET EDC 功能
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import glob
import config
from tools.base_tool import BaseTool

class IPEDCConfigTool(BaseTool):
    """查詢 IP 的 EDC 配置工具"""
    
    def __init__(self):
        super().__init__()
        # 從 config.py 讀取配置路徑，預設為 D:\Git_Code\GETEDCFILE_CONFIG
        self.config_base_path = getattr(config, 'GETEDCFILE_CONFIG_PATH', r'D:\Git_Code\GETEDCFILE_CONFIG')
    
    def get_name(self) -> str:
        return "ip_edc_config_check"
    
    def get_description(self) -> str:
        return """查詢指定IP或機台名稱是否有設定GET EDC功能。
        用法：
        1. IP查詢：廠區名 IP地址 (例如：TFT6 10.99.3.111)
        2. IP查詢：IP地址 (例如：10.99.3.111)
        3. 機台查詢：廠區名 機台名稱 (例如：TFT6 TPRB0100)
        4. 機台查詢：機台名稱 (例如：TPRB0100)"""
    
    def execute(self, query: str) -> str:
        """執行 IP 或機台名稱 EDC 配置查詢"""
        try:
            # 解析輸入參數
            parts = query.strip().split()
            
            if len(parts) == 1:
                # 只有一個參數，可能是 IP 或機台名稱
                param = parts[0]
                factory = None
                
                # 判斷是 IP 還是機台名稱
                if self._is_valid_ip(param):
                    # 是 IP 地址，搜尋所有廠區
                    search_type = "ip"
                    search_value = param
                else:
                    # 是機台名稱，搜尋所有廠區
                    search_type = "machine"
                    search_value = param
                    
            elif len(parts) == 2:
                # 廠區 + IP 或 廠區 + 機台名稱
                factory = parts[0]
                param = parts[1]
                
                # 判斷是 IP 還是機台名稱
                if self._is_valid_ip(param):
                    search_type = "ip"
                    search_value = param
                else:
                    search_type = "machine"
                    search_value = param
            else:
                return "❌ 請提供正確的格式：\n- 廠區名稱 IP地址/機台名稱\n- IP地址/機台名稱"
            
            # 驗證 IP 格式（如果是 IP 查詢）
            if search_type == "ip" and not self._is_valid_ip(search_value):
                return f"❌ IP 地址格式錯誤：{search_value}"
            
            # 搜尋配置
            results = self._search_config(search_value, search_type, factory)
            
            if not results:
                available_factories = self._get_available_factories()
                search_desc = "IP" if search_type == "ip" else "機台名稱"
                return f"""❌ 未找到 {search_desc} {search_value} 的 EDC 配置

📁 可用廠區：{', '.join(available_factories) if available_factories else '無'}
💡 請確認：
1. {search_desc}是否正確
2. 廠區名稱是否正確
3. 配置檔案是否存在於 {self.config_base_path}"""
            
            # 格式化輸出結果
            return self._format_results(results, search_value, search_type)
            
        except Exception as e:
            return f"❌ 查詢過程中發生錯誤：{str(e)}"
    
    def _is_valid_ip(self, ip: str) -> bool:
        """驗證 IP 地址格式"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except:
            return False
    
    def _get_available_factories(self) -> List[str]:
        """獲取可用的廠區列表"""
        try:
            if not os.path.exists(self.config_base_path):
                return []
            
            factories = []
            for item in os.listdir(self.config_base_path):
                item_path = os.path.join(self.config_base_path, item)
                # 排除 .git 目錄和隱藏檔案
                if os.path.isdir(item_path) and not item.startswith('.'):
                    factories.append(item)
            return sorted(factories)
        except:
            return []
    
    def _search_config(self, search_value: str, search_type: str, factory: Optional[str] = None) -> List[Dict[str, Any]]:
        """搜尋 IP 或機台名稱配置"""
        results = []
        
        try:
            if not os.path.exists(self.config_base_path):
                return results
            
            # 確定搜尋路徑
            search_paths = []
            if factory:
                # 指定廠區
                factory_path = os.path.join(self.config_base_path, factory)
                if os.path.exists(factory_path):
                    search_paths.append((factory, factory_path))
            else:
                # 搜尋所有廠區（排除隱藏目錄）
                for item in os.listdir(self.config_base_path):
                    item_path = os.path.join(self.config_base_path, item)
                    if os.path.isdir(item_path) and not item.startswith('.'):
                        search_paths.append((item, item_path))
            
            # 在每個廠區中遞歸搜尋 XML 檔案
            for factory_name, factory_path in search_paths:
                # 使用遞歸模式搜尋所有子目錄中的 XML 檔案
                xml_files = glob.glob(os.path.join(factory_path, "**", "*.xml"), recursive=True)
                
                for xml_file in xml_files:
                    try:
                        config_info = self._parse_xml_config(xml_file, search_value, search_type)
                        if config_info:
                            config_info['factory'] = factory_name
                            config_info['file_path'] = xml_file
                            # 計算相對路徑以便更好地顯示
                            relative_path = os.path.relpath(xml_file, self.config_base_path)
                            config_info['relative_path'] = relative_path
                            results.append(config_info)
                    except Exception as e:
                        print(f"解析 XML 檔案錯誤 {xml_file}: {e}")
                        continue
            
            return results
            
        except Exception as e:
            print(f"搜尋配置錯誤: {e}")
            return results
    
    def _parse_xml_config(self, xml_file: str, search_value: str, search_type: str) -> Optional[Dict[str, Any]]:
        """解析 XML 配置檔案"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # 找到 CTCS_LIST
            ctcs_list = root.find('.//CTCS_LIST')
            if ctcs_list is None:
                return None
            
            # 搜尋匹配的設備
            for eqp in ctcs_list.findall('EQP'):
                match_found = False
                
                if search_type == "ip":
                    # 按 IP 搜尋
                    ip = eqp.get('IP', '').strip()
                    if ip == search_value:
                        match_found = True
                elif search_type == "machine":
                    # 按機台名稱（CTCS）搜尋
                    ctcs = eqp.get('CTCS', '').strip()
                    if ctcs == search_value:
                        match_found = True
                
                if match_found:
                    # 找到匹配的設備，提取配置資訊
                    config = {
                        'ctcs': eqp.get('CTCS', ''),
                        'ip': eqp.get('IP', ''),
                        'alarmflag': eqp.get('ALARMFLAG', ''),
                        'native_mode': eqp.get('NATIVE_MODE', ''),
                        'login_info': {},
                        'file_path_info': {}
                    }
                    
                    # 提取登入資訊
                    login = eqp.find('LOGIN')
                    if login is not None:
                        config['login_info'] = {
                            'userid': login.get('USERID', ''),
                            'password': login.get('PASSWORD', '').replace('..', '**')  # 隱藏密碼
                        }
                    
                    # 提取檔案路徑資訊
                    file_path = eqp.find('FILE_PATH')
                    if file_path is not None:
                        config['file_path_info'] = {
                            'diskdrive': file_path.get('DISKDRIVE', ''),
                            'sourcepath': file_path.get('SOURCEPATH', ''),
                            'sourcedisk': file_path.get('SOURCEDISK', ''),
                            'filetype': file_path.get('FILETYPE', '')
                        }
                    
                    return config
            
            return None
            
        except Exception as e:
            print(f"解析 XML 錯誤: {e}")
            return None
    
    def _format_results(self, results: List[Dict[str, Any]], search_value: str, search_type: str) -> str:
        """格式化查詢結果"""
        if not results:
            search_desc = "IP" if search_type == "ip" else "機台名稱"
            return f"❌ 未找到 {search_desc} {search_value} 的 EDC 配置"
        
        search_desc = "IP" if search_type == "ip" else "機台名稱"
        output = [f"✅ 找到 {search_desc} {search_value} 的 EDC 配置：\n"]
        
        for i, result in enumerate(results, 1):
            output.append(f"📍 **配置 {i}** (廠區：{result['factory']})")
            output.append(f"```xml")
            
            # 構建 EQP 標籤屬性
            eqp_attrs = [f'CTCS="{result["ctcs"]}"', f'IP="{result["ip"]}"']
            if result.get('alarmflag'):
                eqp_attrs.append(f'ALARMFLAG="{result["alarmflag"]}"')
            if result.get('native_mode'):
                eqp_attrs.append(f'NATIVE_MODE="{result["native_mode"]}"')
            
            output.append(f"<EQP {' '.join(eqp_attrs)}>")
            
            if result['login_info']:
                login = result['login_info']
                output.append(f"  <LOGIN USERID=\"{login['userid']}\" PASSWORD=\"{login['password']}\" />")
            
            if result['file_path_info']:
                fp = result['file_path_info']
                fp_attrs = []
                if fp.get('diskdrive'):
                    fp_attrs.append(f'DISKDRIVE="{fp["diskdrive"]}"')
                if fp.get('sourcepath'):
                    fp_attrs.append(f'SOURCEPATH="{fp["sourcepath"]}"')
                if fp.get('sourcedisk'):
                    fp_attrs.append(f'SOURCEDISK="{fp["sourcedisk"]}"')
                if fp.get('filetype'):
                    fp_attrs.append(f'FILETYPE="{fp["filetype"]}"')
                
                if fp_attrs:
                    output.append(f"  <FILE_PATH {' '.join(fp_attrs)} />")
            
            output.append(f"</EQP>")
            output.append(f"```")
            
            # 顯示詳細資訊
            output.append(f"🏭 **廠區：** {result['factory']}")
            output.append(f"🤖 **機台名稱：** {result['ctcs']}")
            output.append(f"🌐 **IP 地址：** {result['ip']}")
            
            # 顯示相對路徑更容易閱讀
            relative_path = result.get('relative_path', result['file_path'])
            output.append(f"📁 **檔案位置：** `{relative_path}`")
            
            if i < len(results):
                output.append("")
        
        return "\n".join(output)

# 工具實例
ip_edc_config_tool = IPEDCConfigTool()
