"""
SPC 詳細資料查看工具

提供格式化的SPC和TRX LOG詳細資料查看功能
"""

from typing import Dict, Any, List
from .base_tool import BaseTool
import json
import xml.dom.minidom

class SPCDetailViewerTool(BaseTool):
    name = "spc_detail_viewer"
    description = "查看已執行SPC診斷後的詳細資料，包括格式化的表格和XML顯示。注意：此工具僅用於查看詳細資料，不是診斷工具。"
    
    def __init__(self):
        super().__init__()
        self.cached_data = {}  # 暫存詳細資料
    
    def get_name(self) -> str:
        """返回工具名稱"""
        return self.name
    
    def get_description(self) -> str:
        """返回工具描述"""
        return """查看已執行SPC診斷後的詳細資料，支援表格、XML、JSON格式。
        使用條件：必須先執行spc_query工具進行診斷
        用法：spc_detail_viewer type:spc|trx|all
        注意：此工具不執行SPC診斷，僅查看詳細資料"""
    
    def execute(self, query: str, **kwargs) -> str:
        """執行工具的主要方法"""
        return self._run(query, **kwargs)
    
    def _run(self, query: str, **kwargs) -> str:
        """
        顯示SPC詳細資料
        query格式: "type:spc" 或 "type:trx" 或 "type:all"
        """
        try:
            # 解析查詢類型
            if "type:spc" in query.lower():
                return self._show_spc_details()
            elif "type:trx" in query.lower():
                return self._show_trx_details()
            elif "type:all" in query.lower():
                return self._show_all_details()
            else:
                return self._show_format_options()
        
        except Exception as e:
            return f"❌ 查看詳細資料時發生錯誤: {str(e)}"
    
    def store_data(self, spc_data: List[Dict], trx_data: Dict):
        """儲存詳細資料供後續查看"""
        self.cached_data = {
            'spc': spc_data,
            'trx': trx_data,
            'timestamp': self._get_current_time()
        }
    
    def _show_format_options(self) -> str:
        """顯示可用的格式選項"""
        result = []
        result.append("📋 **SPC 詳細資料查看選項：**")
        result.append("")
        result.append("🔗 **可用命令：**")
        result.append("• `spc_detail_viewer type:spc` - 查看SPC資料庫詳細記錄")
        result.append("• `spc_detail_viewer type:trx` - 查看TRX LOG詳細記錄")
        result.append("• `spc_detail_viewer type:all` - 查看所有詳細記錄")
        result.append("")
        result.append("📊 **顯示格式：**")
        result.append("• 表格格式 - 易於閱讀的表格形式")
        result.append("• XML格式 - 結構化的XML文檔")
        result.append("• JSON格式 - 原始JSON數據")
        
        return "\n".join(result)
    
    def _show_spc_details(self) -> str:
        """顯示SPC資料庫詳細資料"""
        if 'spc' not in self.cached_data:
            return "❌ 暫無SPC資料，請先執行SPC診斷"
        
        result = []
        result.append("📊 **SPC 資料庫詳細記錄**")
        result.append("=" * 50)
        result.append("")
        
        spc_data = self.cached_data['spc']
        
        # 表格格式
        result.append("### 📋 表格格式")
        result.append("")
        result.append(self._format_spc_as_table(spc_data[0]))
        result.append("")
        
        # XML格式
        result.append("### 🗂️ XML格式")
        result.append("```xml")
        result.append(self._format_spc_as_xml(spc_data[0]))
        result.append("```")
        result.append("")
        
        # JSON格式
        result.append("### 📄 JSON格式")
        result.append("```json")
        # 處理datetime對象
        spc_data_json = self._convert_datetime_to_string(spc_data[0])
        result.append(json.dumps(spc_data_json, ensure_ascii=False, indent=2))
        result.append("```")
        
        return "\n".join(result)
    
    def _show_trx_details(self) -> str:
        """顯示TRX LOG詳細資料"""
        if 'trx' not in self.cached_data:
            return "❌ 暫無TRX LOG資料，請先執行SPC診斷"
        
        result = []
        result.append("🔍 **TRX LOG 詳細記錄**")
        result.append("=" * 50)
        result.append("")
        
        trx_data = self.cached_data['trx']
        
        # 基本資訊表格
        result.append("### 📋 基本資訊")
        result.append("")
        result.append("| 項目 | 值 |")
        result.append("|------|-----|")
        
        if 'detail' in trx_data:
            detail = trx_data['detail']
            basic_fields = ['tStamp', 'eqptId', 'shtId', 'crrId', 'errcode', 'procTime']
            for field in basic_fields:
                if field in detail:
                    result.append(f"| {field} | {detail[field]} |")
        
        result.append("")
        
        # 輸入交易XML (格式化)
        if 'detail' in trx_data and 'inputTrx' in trx_data['detail']:
            result.append("### 📥 輸入交易 (格式化XML)")
            result.append("```xml")
            result.append(self._format_xml_pretty(trx_data['detail']['inputTrx']))
            result.append("```")
            result.append("")
        
        # 輸出交易XML
        if 'detail' in trx_data and 'outputTrx' in trx_data['detail']:
            result.append("### 📤 輸出交易")
            result.append("```xml")
            result.append(self._format_xml_pretty(trx_data['detail']['outputTrx']))
            result.append("```")
            result.append("")
        
        # 完整JSON
        result.append("### 📄 完整JSON資料")
        result.append("```json")
        # 處理datetime對象
        trx_data_json = self._convert_datetime_to_string(trx_data['detail'])
        result.append(json.dumps(trx_data_json, ensure_ascii=False, indent=2))
        result.append("```")
        
        return "\n".join(result)
    
    def _show_all_details(self) -> str:
        """顯示所有詳細資料"""
        result = []
        result.append("📊 **SPC 完整診斷詳細資料**")
        result.append("=" * 60)
        result.append("")
        
        # SPC資料
        result.append(self._show_spc_details())
        result.append("")
        result.append("-" * 60)
        result.append("")
        
        # TRX資料
        result.append(self._show_trx_details())
        
        return "\n".join(result)
    
    def _format_spc_as_table(self, data: Dict) -> str:
        """將SPC資料格式化為表格"""
        table_rows = []
        table_rows.append("| 欄位名稱 | 值 |")
        table_rows.append("|----------|-----|")
        
        # 重要欄位優先顯示
        important_fields = [
            ('基本資訊', ['T_STAMP', 'SHT_ID', 'LOT_ID', 'CRR_ID', 'PRODUCT_ID']),
            ('設備資訊', ['EQPT_ID', 'ONCHID', 'CLDATE', 'CLTIME']),
            ('數值資訊', ['DTX', 'USPEC', 'LSPEC', 'TARGET', 'UCL1', 'LCL1']),
            ('狀態資訊', ['OOS', 'OOC1', 'OOC2', 'OOC3', 'DELFLG'])
        ]
        
        for category, fields in important_fields:
            table_rows.append(f"| **{category}** | |")
            for field in fields:
                if field in data:
                    value = str(data[field]) if data[field] is not None else 'N/A'
                    table_rows.append(f"| {field} | {value} |")
            table_rows.append("| | |")  # 空行分隔
        
        # 其他欄位
        other_fields = set(data.keys()) - set([field for _, fields in important_fields for field in fields])
        if other_fields:
            table_rows.append("| **其他欄位** | |")
            for field in sorted(other_fields):
                value = str(data[field]) if data[field] is not None else 'N/A'
                if len(value) > 50:
                    value = value[:47] + "..."
                table_rows.append(f"| {field} | {value} |")
        
        return "\n".join(table_rows)
    
    def _format_spc_as_xml(self, data: Dict) -> str:
        """將SPC資料格式化為XML"""
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append('<SPC_Data>')
        
        for key, value in data.items():
            value_str = str(value) if value is not None else ''
            # 處理XML特殊字符
            value_str = value_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            xml_lines.append(f'  <{key}>{value_str}</{key}>')
        
        xml_lines.append('</SPC_Data>')
        return "\n".join(xml_lines)
    
    def _format_xml_pretty(self, xml_string: str) -> str:
        """格式化XML字符串"""
        try:
            dom = xml.dom.minidom.parseString(xml_string)
            return dom.toprettyxml(indent="  ", encoding=None)
        except:
            return xml_string
    
    def _get_current_time(self) -> str:
        """獲取當前時間"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _convert_datetime_to_string(self, data):
        """將資料中的datetime對象轉換為字符串"""
        if isinstance(data, dict):
            return {key: self._convert_datetime_to_string(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_datetime_to_string(item) for item in data]
        elif hasattr(data, 'strftime'):  # datetime對象
            return data.strftime("%Y-%m-%d %H:%M:%S.%f") if hasattr(data, 'microsecond') else data.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return data
