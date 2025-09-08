"""
EDC 格式檢查工具
"""

import sys
import os
import xml.etree.ElementTree as ET
import re
from datetime import datetime

# 將專案根目錄加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.base_tool import BaseTool

class EDCFormatTool(BaseTool):
    """EDC XML 格式檢查工具"""
    
    def get_name(self) -> str:
        return "edc_format_check"
    
    def get_description(self) -> str:
        return """檢查 EDC XML 檔案格式是否正確。
        關鍵字：EDC, XML, 格式, 檢查, 驗證, 錯誤, 語法
        當用戶詢問「EDC檔案格式哪裡錯了」或需要驗證 EDC XML 格式時使用此工具。
        可以直接處理用戶貼上的 XML 內容進行驗證。"""
    
    def execute(self, query: str) -> str:
        """執行 EDC 格式檢查"""
        query_upper = query.upper()
        
        # 檢查是否包含 XML 內容
        if "<?xml" in query and "<EDC>" in query:
            # 用戶提供了 XML 內容，進行格式檢查
            return self._validate_edc_xml(query)
        elif any(keyword in query_upper for keyword in ["規範", "說明", "幫助", "HELP", "文檔", "文件", "完整"]):
            # 用戶想了解完整的格式規範
            return self._edc_format_help()
        elif any(keyword in query_upper for keyword in ["格式", "錯誤", "檢查", "驗證", "XML"]):
            # 用戶詢問格式問題但沒提供 XML
            return self._request_edc_xml()
        else:
            # 預設顯示格式檢查指引
            return self._request_edc_xml()
    
    def _validate_edc_xml(self, xml_content: str) -> str:
        """驗證 EDC XML 檔案格式"""
        try:
            # 提取 XML 部分
            xml_start = xml_content.find("<?xml")
            if xml_start == -1:
                return "❌ 找不到有效的 XML 開始標籤"
            
            xml_part = xml_content[xml_start:]
            xml_end = xml_part.find("</EDC>")
            if xml_end == -1:
                return "❌ 找不到 EDC 結束標籤"
            
            xml_part = xml_part[:xml_end + 6]  # +6 for "</EDC>"
            
            # 解析 XML
            try:
                root = ET.fromstring(xml_part)
            except ET.ParseError as e:
                return f"❌ XML 格式錯誤：{str(e)}"
            
            if root.tag != "EDC":
                return "❌ 根節點必須是 <EDC>"
            
            # 進行詳細驗證
            validation_result = self._perform_detailed_validation(root)
            
            return validation_result
            
        except Exception as e:
            return f"❌ 檢查過程發生錯誤：{str(e)}\n\n請確認提供的是完整且有效的 XML 內容。"
    
    def _perform_detailed_validation(self, root) -> str:
        """執行詳細的 XML 驗證"""
        errors = []
        warnings = []
        
        # 定義必填欄位和驗證規則
        # EDC 欄位定義（根據最新規範）
        required_fields = {
            "glass_id": {"max_length": 25, "required": True, "description": "玻璃 ID"},
            "product_id": {"max_length": 25, "required": True, "description": "產品 ID"},
            "eqp_id": {"max_length": 8, "required": True, "description": "機台名稱"},
            "cldate": {"required": True, "description": "資料生成日期", "format": "yyyy-MM-dd"},
            "cltime": {"required": True, "description": "資料生成時間", "format": "HH:mm:ss"},
            "recipe_id": {"max_length": 32, "required": True, "description": "Recipe ID"},
            "operation": {"max_length": 4, "required": True, "description": "站點"}
        }
        
        optional_fields = {
            "line_batch_id": {"max_length": 16, "description": "Line ID"},
            "group_id": {"max_length": 25, "description": "Group ID"},
            "lot_id": {"max_length": 25, "description": "Lot ID"},
            "pfcd": {"max_length": 25, "description": "產品 ID (通常跟 product_id 相同)"},
            "ec_code": {"max_length": 2, "description": "EC Code"},
            "route_no": {"max_length": 10, "description": "Route ID"},
            "route_version": {"description": "Route 版號"},
            "owner": {"max_length": 4, "description": "Owner"},
            "rtc_flag": {"description": "RTC 模式"},
            "pnp": {"description": "PNP 碼", "values": ["P", "N", ""]},
            "chamber": {"max_length": 100, "description": "Chamber 記錄"},
            "cassette_id": {"max_length": 25, "description": "卡匣 ID"},
            "line_batch_id": {"max_length": 16, "description": "Line batch ID"},
            "split_id": {"max_length": 2, "description": "Split ID"},
            "mes_link_key": {"max_length": 4, "description": "MES key 值"},
            "rework_count": {"max_length": 4, "description": "重工次數"},
            "operator": {"max_length": 20, "description": "OP 工號"},
            "reserve_field_1": {"description": "保留欄位 1"},
            "reserve_field_2": {"description": "保留欄位 2"}
        }
        
        # 檢查必填欄位
        for field_name, rules in required_fields.items():
            element = root.find(field_name)
            if element is None:
                errors.append(f"❌ 缺少必填欄位：<{field_name}> - {rules['description']}")
            elif not element.text or element.text.strip() == "":
                errors.append(f"❌ 必填欄位不能為空：<{field_name}> - {rules['description']}")
            else:
                # 檢查長度
                if "max_length" in rules and len(element.text) > rules["max_length"]:
                    errors.append(f"❌ <{field_name}> 長度超過限制 ({len(element.text)} > {rules['max_length']} 碼)")
                
                # 檢查日期時間格式
                if field_name == "cldate":
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', element.text):
                        errors.append(f"❌ <cldate> 格式錯誤，應為 yyyy-MM-dd，實際：{element.text}")
                elif field_name == "cltime":
                    if not re.match(r'^\d{2}:\d{2}:\d{2}$', element.text):
                        errors.append(f"❌ <cltime> 格式錯誤，應為 HH:mm:ss，實際：{element.text}")
        
        # 檢查選填欄位
        for field_name, rules in optional_fields.items():
            element = root.find(field_name)
            if element is not None and element.text:
                # 檢查長度
                if "max_length" in rules and len(element.text) > rules["max_length"]:
                    warnings.append(f"⚠️ <{field_name}> 長度超過建議限制 ({len(element.text)} > {rules['max_length']} 碼)")
                
                # 檢查特定值
                if "values" in rules and element.text not in rules["values"]:
                    warnings.append(f"⚠️ <{field_name}> 值不在建議範圍內：{element.text}，建議值：{rules['values']}")
        
        # 檢查 datas 區塊
        datas_element = root.find("datas")
        if datas_element is None:
            errors.append("❌ 缺少 <datas> 區塊")
        else:
            data_errors, data_warnings = self._validate_datas_section(datas_element)
            errors.extend(data_errors)
            warnings.extend(data_warnings)
        
        # 生成檢查報告
        return self._generate_validation_report(errors, warnings)
    
    def _validate_datas_section(self, datas_element):
        """驗證 datas 區塊"""
        errors = []
        warnings = []
        
        iary_elements = datas_element.findall("iary")
        if not iary_elements:
            warnings.append("⚠️ <datas> 區塊中沒有 <iary> 測項資料")
        else:
            # 檢查測項重複
            seen_keys = set()
            for i, iary in enumerate(iary_elements, 1):
                item_name_elem = iary.find("item_name")
                item_type_elem = iary.find("item_type")
                item_value_elem = iary.find("item_value")
                
                # 檢查必填欄位
                if item_name_elem is None or not item_name_elem.text:
                    errors.append(f"❌ 測項 {i}：缺少 <item_name>")
                if item_type_elem is None or not item_type_elem.text:
                    errors.append(f"❌ 測項 {i}：缺少 <item_type>")
                if item_value_elem is None or not item_value_elem.text:
                    errors.append(f"❌ 測項 {i}：缺少 <item_value>")
                
                # 檢查長度
                if item_name_elem is not None and item_name_elem.text and len(item_name_elem.text) > 16:
                    errors.append(f"❌ 測項 {i}：<item_name> 長度超過 16 碼")
                if item_type_elem is not None and item_type_elem.text and len(item_type_elem.text) > 4:
                    errors.append(f"❌ 測項 {i}：<item_type> 長度超過 4 碼")
                if item_value_elem is not None and item_value_elem.text and len(item_value_elem.text) > 30:
                    errors.append(f"❌ 測項 {i}：<item_value> 長度超過 30 碼")
                
                # 檢查重複 key
                if item_name_elem is not None and item_type_elem is not None:
                    if item_name_elem.text and item_type_elem.text:
                        key = f"{item_name_elem.text}+{item_type_elem.text}"
                        if key in seen_keys:
                            errors.append(f"❌ 測項 {i}：重複的 item_name + item_type 組合：{key}")
                        else:
                            seen_keys.add(key)
                
                # 檢查 item_type 值
                if item_type_elem is not None and item_type_elem.text:
                    valid_types = ["X", "EDC", "MAX", "MIN", "SDV", "AVG"]
                    if item_type_elem.text not in valid_types and not item_type_elem.text.isdigit():
                        warnings.append(f"⚠️ 測項 {i}：<item_type> 值 '{item_type_elem.text}' 不在標準類型中，建議使用：{valid_types} 或數字")
        
        return errors, warnings
    
    def _generate_validation_report(self, errors, warnings) -> str:
        """生成驗證報告"""
        result = "🔍 **EDC XML 格式檢查結果**\n\n"
        
        if not errors and not warnings:
            result += "✅ **格式完全正確！**\n"
            result += "您的 EDC XML 檔案符合所有格式要求。"
        else:
            if errors:
                result += f"❌ **發現 {len(errors)} 個錯誤（必須修正）：**\n"
                for error in errors:
                    result += f"{error}\n"
                result += "\n"
            
            if warnings:
                result += f"⚠️ **發現 {len(warnings)} 個警告（建議檢查）：**\n"
                for warning in warnings:
                    result += f"{warning}\n"
                result += "\n"
            
            result += "**📝 修正建議：**\n"
            if errors:
                result += "1. 請先修正上述錯誤項目\n"
                result += "2. 確保所有必填欄位都有值且格式正確\n"
            if warnings:
                result += "3. 檢查警告項目，雖然不影響基本功能但建議修正\n"
        
        return result
    
    def _request_edc_xml(self) -> str:
        """請求用戶提供 EDC XML 內容"""
        return """📄 **EDC XML 檔案格式檢查**

請**貼上您的完整 EDC XML 檔案內容**，我就能幫您檢查格式是否正確！

**支援檢查項目：**
✅ 必填欄位完整性檢查
✅ 欄位長度限制驗證  
✅ 日期時間格式驗證
✅ 測項資料重複性檢查
✅ XML 結構正確性驗證

**完整 EDC XML 檔案格式規範：**

**📋 必填欄位清單：**
```
欄位名稱        格式/限制說明                是否可留空    補充說明
glass_id       25 碼，不可為空               否          玻璃ID
eqp_id         8 碼，不可為空                否          機台ID
cldate         yyyy-MM-dd，不可為空          否          資料生成日期
cltime         HH:mm:ss，不可為空            否          資料生成時間
recipe_id      32 碼，不可為空               否          Recipe ID
operation      4 碼，不可為空                否          站點
product_id     25 碼，不可為空               否          產品ID
line_batch_id  16 碼，不可為空               否          Line batch ID
chamber        100 碼，可為空                是          Chamber記錄
cassette_id    25 碼，可為空                 是          CST ID
split_id       2 碼，可為空                  是          Split ID
mes_link_key   4 碼，可為空                  是          MES key值
rework_count   4 碼，可為空                  是          重工次數
operator       20 碼，可為空                 是          操作員
reserve_field_1 不限長度，可為空             是          保留欄位1
reserve_field_2 不限長度，可為空             是          保留欄位2
```

**📝 標準 XML 格式範例：**
```xml
<?xml version="1.0"?>
<EDC>
    <glass_id>T65833S0BA01</glass_id>
    <eqp_id>EQ001</eqp_id>
    <cldate>2025-08-28</cldate>
    <cltime>14:30:05</cltime>
    <recipe_id>RECIPE_001</recipe_id>
    <operation>OP01</operation>
    <product_id>PROD123</product_id>
    <chamber>CHAMBER_A</chamber>
    <cassette_id>CASS001</cassette_id>
    <line_batch_id>LB001</line_batch_id>
    <split_id>01</split_id>
    <mes_link_key>MES1</mes_link_key>
    <rework_count>0</rework_count>
    <operator>OP001</operator>
    <reserve_field_1></reserve_field_1>
    <reserve_field_2></reserve_field_2>
    <datas>
        <iary>
            <item_name>TEMP</item_name>
            <item_type>X</item_type>
            <item_value>25.5</item_value>
        </iary>
        <iary>
            <item_name>PRESSURE</item_name>
            <item_type>MAX</item_type>
            <item_value>1013.25</item_value>
        </iary>
    </datas>
</EDC>
```

**⚠️ 重要注意事項：**
• **測項唯一性**：同一檔案內 `item_name` + `item_type` 組合不可重複
• **日期格式**：cldate 必須為 yyyy-MM-dd 格式
• **時間格式**：cltime 必須為 HH:mm:ss 格式  
• **item_type 標準值**：X / EDC / MAX / MIN / SDV / AVG / 數字

請直接貼上您的 XML 內容，我會立即進行詳細的格式檢查！🔍"""
    
    def _edc_format_help(self) -> str:
        """EDC 格式說明"""
        return """📋 **EDC XML 檔案格式完整規範**

**🔴 必填欄位清單（不可為空）：**
```
欄位名稱        格式/限制說明                補充說明
glass_id       25 碼，不可為空              玻璃ID
product_id     25 碼，不可為空              產品ID
eqp_id         8 碼，不可為空               機台名稱  
cldate         yyyy-MM-dd，不可為空         資料生成日期
cltime         HH:mm:ss，不可為空           資料生成時間
recipe_id      32 碼，不可為空              Recipe ID
operation      4 碼，不可為空               站點
```

**🟡 選填欄位清單（可為空或有預設值）：**
```
欄位名稱          格式/限制說明              補充說明
line_batch_id    16 碼                     Line batch ID
chamber          100 碼                    Chamber記錄
cassette_id      25 碼                     卡匣ID
split_id         2 碼                      Split ID
mes_link_key     4 碼                      MES key值
rework_count     4 碼                      重工次數
operator         20 碼                     OP工號
reserve_field_1  不限長度                   保留欄位1
reserve_field_2  不限長度                   保留欄位2
```

**📊 測項資料 (datas/iary) 規範：**
• `item_name` - 測項名稱（不可重複組合）
• `item_type` - 測項類型，標準值：X / EDC / MAX / MIN / SDV / AVG / 數字
• `item_value` - 測項數值

**⚠️ 重要格式要求：**
1. **測項唯一性**：同一檔案內 `item_name` + `item_type` 組合不可重複
2. **日期格式**：cldate 必須嚴格遵循 yyyy-MM-dd 格式
3. **時間格式**：cltime 必須嚴格遵循 HH:mm:ss 格式
4. **欄位長度**：請確實遵守各欄位的字元數限制
5. **XML 結構**：必須符合標準 XML 語法規則

**🔍 需要檢查 XML 檔案？**
請直接貼上您的完整 XML 內容，我會幫您進行詳細的格式驗證，包含：
• 必填欄位檢查
• 欄位長度驗證
• 日期時間格式檢查
• 測項重複性檢查
• XML 語法正確性驗證"""
