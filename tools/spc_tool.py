"""
SPC 系統診斷工具 ，這段不要拿掉

以下為該工具的完整查詢邏輯。
FACTORY_MAP = {
    "TFT6": {"path": "TFT6", "svr": "APCSPCDT", "sql_table": "ASPC_ONLNCHART", "mes_schema": "T6WPT1A1", "data_schema": "T6HEC1D", "para_table": "HAMSPARA", "glsinfo_table": "HAMSGLSINFO", "raw_table": "HAMSRAW"},
    "CF6": {"path": "CF6", "svr": "BPCSPCDT", "sql_table": "BSPC_ONLNCHART", "mes_schema": "F6WPT1A1", "data_schema": "F6HEC1D", "para_table": "HBMSPARA", "glsinfo_table": "HBMSGLSINFO", "raw_table": "HBMSRAW"},
    "LCD6": {"path": "LCD6", "svr": "CPCSPCDT", "sql_table": "CSPC_ONLNCHART", "mes_schema": "L6WPT1A1", "data_schema": "L6HEC1D", "para_table": "HCMSPARA", "glsinfo_table": "HCMSGLSINFO", "raw_table": "HCMSRAW"},
    "USL": {"path": "USL", "svr": "CPCMSRDT", "sql_table": "CSPC_ONLNCHART", "mes_schema": "U3WPT1A1", "data_schema": "U3REC1D", "para_table": "HCMSPARA", "glsinfo_table": "HCMSGLSINFO", "raw_table": "HCMSRAW"},
}

查詢步驟：
1. 從用戶查詢中提取關鍵資訊（廠別、時間、玻璃ID、設備ID、CHART ID）
2. 檢查是否提供必要的五個條件
3. 如果資訊完整，進行實際查詢
4. 查詢TRX LOG，先查http://tncimweb.cminl.oa/Apigateway/MesLogApi/TFT6/trx-log?fromDT=&toDT=&svrModules=APCSPCDT&shtId=&eqptId=&lastTStamp=&pageSize=2
其中TFT6為廠別代碼，fromDT和toDT為時間範圍(使用USER傳入的時間前後半小時)，svrModules為當TFT6時為APCSPCDT，當CF6時為BPCSPCDT，當LCD6/USL時為CPCSPCDT，shtId為玻璃ID，eqptId為設備ID
5. 如果只有查到一筆，表示時間準確，若查到多筆，表示時間範圍過大，請用戶提供更精確的時間。
6. 接著查詢http://tncimweb.cminl.oa/Apigateway/MesLogApi/TFT6/trx-log?fromDT=2025%2F08%2F25%2013%3A11%3A38&toDT=2025%2F08%2F25%2014%3A11%3A38&svrModules=APCSPCDT&lastTStamp=&pageSize=1
其中TFT6為廠別代碼，fromDT和toDT與上步查詢相同)，svrModules為當TFT6時為APCSPCDT，當CF6時為BPCSPCDT，當LCD6/USL時為CPCSPCDT
7. 接著查詢http://tncimweb.cminl.oa/Apigateway/MesLogApi/TFT6/trx-log/APCSPCDT/2025-08-25-14.11.37.556813?ignoreBody=false
其中TFT6為廠別代碼，svrModules為當TFT6時為APCSPCDT，當CF6時為BPCSPCDT，當LCD6/USL時為CPCSPCDT，2025-08-25-14.11.37.556813為上一步查到的tStamp
8. 這邊TRX LOG查詢結束。UI顯示告知USER。
9. 接著查詢DB資料。透過API查詢SPC DB，sql = SELECT * FROM {data_schema}.{glsinfo_table} a 
        inner join
    {data_schema}.{para_table} b
        on a.SEQ = b.SEQ
        inner join 
    {data_schema}.{raw_table} c
        on (b.SEQ = c.SEQ AND b.data_group = c.data_group)
WHERE  a.SHT_ID ='{sht}';"
10. 如果有找到資料，表示有資料進CHART，就停止動作。告知USER該筆資料有進CHART。
11. 若沒找到資料，表示沒有進CHART。這時候將CHART的資料調出來顯示給USER看。查詢MES DB。SQL = SELECT * FROM ASPC_ONLNCHART WHERE ONCHID = ''
其中TFT6為ASPC_ONLNCHART，CF6為BSPC_ONLNCHART，LCD6/USL為CSPC_ONLNCHART，ONCHID為用戶提供的CHART ID
12. 接著根據第6步查詢到的資料分析出Chart_Condition字串，後面為SQL的WHERE條件。查詢MES DB。SQL = SELECT * FROM ASPC_ONLNCHART WHERE + Chart_Condition字串後面字串。這邊要全部查詢不要限制筆數。
13. 比對查出來的資料是否有在第11步查詢到的CHART中。如果沒有表示條件不符。
14. 接著比對第11步查到的CHART所有欄位與第12步分析出的WHERE條件內的欄位資訊是否有不符的地方。
15. 如有不相符的地方就是問題所在。
16. 比對第9步查到資料中的DATA_GROUP欄位數值是否存在MES DB中。SQL = SELECT * FROM T6WPT1D.AMLITEM WHERE EQPT_ID='' AND REP_UNIT='' AND DATA_PAT='' AND MES_ID='' AND DATA_GROUP=''
TFT6:AMLITEM，CF6:BMLITEM，LCD6/USL:CMLITEM。EQPT_ID，REP_UNIT，DATA_PAT，MES_ID從第12步查到後面為SQL的WHERE條件取得。
    如果沒有就是回答USER:XMLITEM DB缺少設定上報DATA_GROUP
17. 比對第9步查到資料中的DATA_GROUP欄位數值是否存在第7步查到的INPUT中data_group標籤數值。
    如果沒有就是回答USER:缺少必要上報DATA_GROUP
18. 將不相同之處總結給USER。


TEST:
有進CHART: 廠別:TFT6，上報時間:2025-09-03-09.40.00，玻璃ID:T65913Y7AD，設備ID:IMRV0100，CHART ID:SPDV1400_2353_TOTAL
沒進CHART:
"""

import sys
import os
import re
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import quote

# 將專案根目錄加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.base_tool import BaseTool
from apis.universal_query_api import execute_query

class SPCTool(BaseTool):
    """SPC 系統診斷工具"""
    
    def __init__(self):
        super().__init__()
        self.factory_map = {
            "TFT6": {"path": "TFT6", "svr": "APCSPCDT", "sql_table": "ASPC_ONLNCHART", "mes_schema": "T6WPT1D", "data_schema": "T6HEC1D", "para_table": "HAMSPARA", "glsinfo_table": "HAMSGLSINFO", "raw_table": "HAMSRAW", "mlitem_table": "AMLITEM"},
            "CF6": {"path": "CF6", "svr": "BPCSPCDT", "sql_table": "BSPC_ONLNCHART", "mes_schema": "F6WPT1D", "data_schema": "F6HEC1D", "para_table": "HBMSPARA", "glsinfo_table": "HBMSGLSINFO", "raw_table": "HBMSRAW", "mlitem_table": "BMLITEM"},
            "LCD6": {"path": "LCD6", "svr": "CPCSPCDT", "sql_table": "CSPC_ONLNCHART", "mes_schema": "L6WPT1D", "data_schema": "L6HEC1D", "para_table": "HCMSPARA", "glsinfo_table": "HCMSGLSINFO", "raw_table": "HCMSRAW", "mlitem_table": "CMLITEM"},
            "USL": {"path": "USL", "svr": "CPCMSRDT", "sql_table": "CSPC_ONLNCHART", "mes_schema": "U3WPT1D", "data_schema": "U3REC1D", "para_table": "HCMSPARA", "glsinfo_table": "HCMSGLSINFO", "raw_table": "HCMSRAW", "mlitem_table": "CMLITEM"},
        }
        self.base_url = "http://tncimweb.cminl.oa/Apigateway"
        
        # 初始化詳細資料查看工具
        self.detail_viewer = None
        try:
            from .spc_detail_viewer_tool import SPCDetailViewerTool
            self.detail_viewer = SPCDetailViewerTool()
        except ImportError:
            pass
    
    def _is_safe_identifier(self, value: str) -> bool:
        """檢查是否為安全的識別符（防止 SQL injection）"""
        if not value or not isinstance(value, str):
            return False
        # 允許字母、數字、底線、破折號、括號、點號，長度限制在1-200字元
        # 這些字元對於CHART ID、設備ID、玻璃ID等是安全的
        return bool(re.match(r'^[A-Za-z0-9_\-\(\)\.]{1,200}$', value))
    
    def _is_safe_stmt(self, stmt: str) -> bool:
        """檢查 TRX stmt 是否安全（防止 SQL injection）"""
        if not stmt or not isinstance(stmt, str):
            return False
        
        # 檢查長度限制
        if len(stmt) > 1000:
            return False
        
        # 拒絕危險字元和模式
        dangerous_patterns = [
            r';',           # 分號 - 多語句執行
            r'--',          # SQL 註釋
            r'/\*',         # 多行註釋開始
            r'\*/',         # 多行註釋結束
            r'\bDROP\b',    # DROP 語句
            r'\bINSERT\b',  # INSERT 語句
            r'\bUPDATE\b',  # UPDATE 語句
            r'\bDELETE\b',  # DELETE 語句
            r'\bEXEC\b',    # EXEC 語句
            r'\bEXECUTE\b', # EXECUTE 語句
            r'\bCREATE\b',  # CREATE 語句
            r'\bALTER\b',   # ALTER 語句
            r'\bUNION\b',   # UNION - 可能用於數據洩露
            r'\bXP_\w+',    # 擴展存儲過程
        ]
        
        stmt_upper = stmt.upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, stmt_upper, re.IGNORECASE):
                return False
        
        # 只允許基本的 WHERE 條件語法
        # 允許：欄位名、=、>、<、>=、<=、AND、OR、NOT、括號、單引號字串、數字
        allowed_pattern = r"^[A-Za-z0-9_\.\s=><!'\"%()\,\-ANDORNOTandornot]+$"
        return bool(re.match(allowed_pattern, stmt))
    
    def _sanitize_stmt_for_display(self, stmt: str) -> str:
        """安全化 stmt 用於顯示（移除潛在危險內容）"""
        if not stmt:
            return ""
        # 移除註釋
        stmt = re.sub(r'--.*?(\n|$)', '', stmt, flags=re.MULTILINE)
        stmt = re.sub(r'/\*.*?\*/', '', stmt, flags=re.DOTALL)
        # 限制長度
        return stmt[:500] + "..." if len(stmt) > 500 else stmt
    
    def get_name(self) -> str:
        return "spc_query"
    
    def get_description(self) -> str:
        return """執行SPC系統診斷，檢查資料是否進入管制圖（CHART）。
        適用情況：
        - 當用戶提供廠別、時間、玻璃ID、設備ID、CHART ID等資訊時
        - 查詢「為什麼SPC沒有進CHART」或「資料是否有進CHART」
        - 診斷SPC系統問題或設備狀態
        - 檢查統計製程管制圖狀態
        
        注意：這是主要的SPC診斷工具，不是詳細資料查看工具。"""
    
    def execute(self, query: str) -> str:
        try:
            # 1. 從用戶查詢中提取關鍵資訊
            info = self._extract_spc_info(query)
            
            # 2. 檢查是否提供必要的五個條件
            missing_conditions = self._check_required_spc_conditions(info)
            
            if missing_conditions:
                return self._request_missing_spc_info(missing_conditions, info)
            
            # 3. 如果資訊完整，進行實際查詢
            return self._perform_spc_diagnosis(info)
            
        except Exception as e:
            return f"""⚠️ SPC 診斷過程中發生錯誤：{str(e)}

**手動排查建議：**
1. 檢查上報時間格式是否正確
2. 確認玻璃ID是否存在於系統中
3. 驗證設備ID是否正常運作
4. 檢查CHART ID配置

**請提供以下完整資訊以進行人工診斷：**
- 廠別(TFT6/CF6/LCD6/USL)
- 上報時間 (格式: YYYY-MM-DD HH:MM:SS)
- 玻璃ID
- 設備ID  
- CHART ID"""

    def _extract_spc_info(self, query: str) -> Dict[str, Any]:
        """從查詢中提取 SPC 相關資訊"""
        info = {
            "factory": None,
            "timestamp": None,
            "glass_id": None,
            "equipment_id": None,
            "chart_id": None,
            "raw_query": query,
            "extracted_count": 0
        }
        
        # 提取廠別
        factory_patterns = [
            r'廠別\s*[:：]\s*(TFT6|CF6|LCD6|USL)',
            r'FACTORY\s*[:：]\s*(TFT6|CF6|LCD6|USL)',
            r'\b(TFT6|CF6|LCD6|USL)\b',
        ]
        for pattern in factory_patterns:
            factory_match = re.search(pattern, query.upper())
            if factory_match:
                info["factory"] = factory_match.group(1)
                info["extracted_count"] += 1
                break
        
        # 提取時間格式 - 支援多種格式
        time_patterns = [
            # 標準格式: 2025-09-03 14:30:05
            r'上報時間\s*[:：]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            r'時間\s*[:：]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            # 檔案名格式: 2025-09-03-09.40.00
            r'上報時間\s*[:：]\s*(\d{4}-\d{2}-\d{2}-\d{2}\.\d{2}\.\d{2})',
            r'時間\s*[:：]\s*(\d{4}-\d{2}-\d{2}-\d{2}\.\d{2}\.\d{2})',
            r'(\d{4}-\d{2}-\d{2}-\d{2}\.\d{2}\.\d{2})',
            # 斜線格式: 2025/09/03 14:30:05
            r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})',
        ]
        for pattern in time_patterns:
            time_match = re.search(pattern, query)
            if time_match:
                raw_time = time_match.group(1)
                # 正規化時間格式為標準格式
                if '-' in raw_time and '.' in raw_time:
                    # 轉換 2025-09-03-09.40.00 -> 2025-09-03 09:40:00
                    parts = raw_time.split('-')
                    if len(parts) == 4:  # YYYY-MM-DD-HH.MM.SS
                        date_part = '-'.join(parts[:3])  # YYYY-MM-DD
                        time_part = parts[3].replace('.', ':')  # HH:MM:SS
                        info["timestamp"] = f"{date_part} {time_part}"
                    else:
                        info["timestamp"] = raw_time
                else:
                    info["timestamp"] = raw_time
                info["extracted_count"] += 1
                break
        
        # 提取玻璃ID
        glass_patterns = [
            r'玻璃ID\s*[:：]\s*([A-Za-z0-9]+)',
            r'GLASS\s*ID\s*[:：]\s*([A-Za-z0-9]+)',
            r'Glass\s*ID\s*[:：]\s*([A-Za-z0-9]+)',
            r'SHT_ID\s*[:：]\s*([A-Za-z0-9]+)',
        ]
        for pattern in glass_patterns:
            glass_match = re.search(pattern, query)
            if glass_match:
                info["glass_id"] = glass_match.group(1)
                info["extracted_count"] += 1
                break
        
        # 提取設備ID
        equipment_patterns = [
            r'設備ID\s*[:：]\s*([A-Za-z0-9]+)',
            r'設備\s*[:：]\s*([A-Za-z0-9]+)',
            r'EQUIPMENT\s*ID\s*[:：]\s*([A-Za-z0-9]+)',
            r'EQP_ID\s*[:：]\s*([A-Za-z0-9]+)',
            # 新增更寬鬆的模式
            r'設備ID[：:]\s*([A-Za-z0-9]+)',
            r'設備ID\s+([A-Za-z0-9]+)',
            r'\b([A-Z]{2,6}\d{4,6})\b',  # 匹配設備ID格式如 IMRV0100
        ]
        for pattern in equipment_patterns:
            eq_match = re.search(pattern, query)
            if eq_match:
                potential_equipment = eq_match.group(1)
                # 確保不是其他ID (避免誤判玻璃ID等)，但允許T6開頭的設備
                if len(potential_equipment) >= 6:
                    info["equipment_id"] = potential_equipment
                    info["extracted_count"] += 1
                    break
        
        # 提取CHART ID
        chart_patterns = [
            r'CHART\s*ID\s*[:：]\s*([A-Za-z0-9_\(\)\-\.]+)',
            r'Chart\s*ID\s*[:：]\s*([A-Za-z0-9_\(\)\-\.]+)',
            r'ONCHID\s*[:：]\s*([A-Za-z0-9_\(\)\-\.]+)',
            # 新增更寬鬆的模式
            r'CHART\s*ID[：:]\s*([A-Za-z0-9_\(\)\-\.]+)',
            r'CHART\s+ID\s+([A-Za-z0-9_\(\)\-\.]+)',
            r'\b(SPD[A-Z0-9_\(\)\-\.]+)\b',  # 匹配CHART ID格式如 SPDV1400_2353_TOTAL
            r'\b(E\d+[A-Z0-9_\(\)\-\.]*)\b',  # 匹配E904開頭的CHART ID格式
        ]
        for pattern in chart_patterns:
            chart_match = re.search(pattern, query)
            if chart_match:
                info["chart_id"] = chart_match.group(1)
                info["extracted_count"] += 1
                break
        
        return info

    def _check_required_spc_conditions(self, info: Dict[str, Any]) -> List[str]:
        """檢查 SPC 查詢必要的五個條件"""
        missing_conditions = []
        
        if not info.get("factory"):
            missing_conditions.append("廠別")
        if not info.get("timestamp"):
            missing_conditions.append("上報時間")
        if not info.get("glass_id"):
            missing_conditions.append("玻璃ID")
        if not info.get("equipment_id"):
            missing_conditions.append("設備ID")
        if not info.get("chart_id"):
            missing_conditions.append("CHART ID")
        
        return missing_conditions

    def _request_missing_spc_info(self, missing_conditions: List[str], info: Dict[str, Any]) -> str:
        """請求用戶提供缺失的 SPC 資訊"""
        
        # 顯示已提取到的資訊
        extracted_info = []
        if info.get("factory"):
            extracted_info.append(f"✅ 廠別: {info['factory']}")
        if info.get("timestamp"):
            extracted_info.append(f"✅ 上報時間: {info['timestamp']}")
        if info.get("glass_id"):
            extracted_info.append(f"✅ 玻璃ID: {info['glass_id']}")
        if info.get("equipment_id"):
            extracted_info.append(f"✅ 設備ID: {info['equipment_id']}")
        if info.get("chart_id"):
            extracted_info.append(f"✅ CHART ID: {info['chart_id']}")
        
        # 顯示缺少的資訊
        missing_info = []
        for condition in missing_conditions:
            missing_info.append(f"❌ 缺少: {condition}")
        
        if extracted_info:
            response = f"""📋 **資訊檢查結果：**

**已提取到的資訊：**
{chr(10).join(extracted_info)}

**還需要補充：**
{chr(10).join(missing_info)}

請補充缺少的資訊，例如：
「廠別:TFT6，上報時間:2025-08-28 14:30:05，玻璃ID:T65833S0BA01，設備ID:TPAB0106，CHART ID:TPAB0106_2F10_67D2_AUWitdh_01」"""
        else:
            response = """要幫您查詢「SPC為什麼沒有進CHART」，我需要以下五個資訊：

1. 廠別（例如：TFT6/CF6/LCD6/USL）
2. 上報時間（例如：2025-08-28 14:30:05）
3. 玻璃 ID（例如：T65833S0BA01）
4. 設備 ID（例如：TPAB0106）
5. Chart ID（例如：TPAB0106_2F10_67D2_AUWitdh_01）

**📝 範例格式：**
「廠別:USL，上報時間:2025-09-04 08:34:56，玻璃ID:T357M6V1NL21，設備ID:CSLI4204 ，CHART ID:E904(015T)_3000_CSLI4204_CF_LL_Cor_CP_X」"""
        
        return response

    def _perform_spc_diagnosis(self, info: Dict[str, Any]) -> str:
        """執行完整的 SPC 診斷流程"""
        result = [f"🔧 **SPC CHART 診斷開始**"]
        result.append(f"**查詢資訊：** 廠別:{info['factory']}, 時間:{info['timestamp']}, 玻璃ID:{info['glass_id']}, 設備ID:{info['equipment_id']}, CHART ID:{info['chart_id']}")
        result.append("")
        
        try:
            # 步驟 4-8: 查詢 TRX LOG
            trx_results = self._query_trx_log(info)
            result.append("📊 **TRX LOG 查詢結果：**")
            
            if trx_results["success"]:
                result.append("✅ TRX LOG 查詢成功")
                if 't_stamp' in trx_results:
                    result.append(f"🕐 交易時間: {trx_results['t_stamp']}")
                
                # 直接顯示TRX LOG詳細資料
                if 'detail' in trx_results and trx_results['detail']:
                    detail = trx_results['detail']
                    if 'evntlgDetail' in detail:
                        event_detail = detail['evntlgDetail']
                        result.append(f"📋 設備ID: {event_detail.get('eqptId', 'N/A')}, 玻璃ID: {event_detail.get('shtId', 'N/A')}")
                        result.append(f"📋 錯誤碼: {event_detail.get('errcode', 'N/A')}, 處理時間: {event_detail.get('procTime', 'N/A')}ms")
                    else:
                        result.append(f"📋 設備ID: {detail.get('eqptId', 'N/A')}, 玻璃ID: {detail.get('shtId', 'N/A')}")
                        result.append(f"📋 錯誤碼: {detail.get('errcode', 'N/A')}, 處理時間: {detail.get('procTime', 'N/A')}ms")
                    
                    result.append("")
                    # 直接顯示詳細資料
                    trx_details = self._format_trx_details(trx_results)
                    result.extend(trx_details)
            else:
                result.append("❌ TRX LOG 查詢失敗")
                # 只顯示錯誤訊息，不顯示詳細過程
                error_messages = [msg for msg in trx_results["messages"] if "❌" in msg]
                result.extend(error_messages[:3])  # 最多顯示3個錯誤訊息
            
            result.append("")
            
            # 即使TRX LOG查詢失敗，也要繼續進行SPC資料庫查詢
            if not trx_results["success"]:
                result.append("⚠️ TRX LOG 查詢失敗，將僅進行SPC資料庫查詢")
                result.append("")
            
            # 步驟 9: 查詢 SPC DB 確認是否有進 CHART
            spc_data = self._query_spc_db(info)
            result.append("🗄️ **SPC 資料庫查詢結果：**")
            result.append(f"📋 執行SQL: `{spc_data.get('sql', 'N/A')}`")
            result.append("")
            
            if spc_data["found"]:
                result.append("✅ **該筆資料已進入 CHART**")
                result.append(f"找到 {len(spc_data['data'])} 筆相關資料")
                
                # 儲存詳細資料到查看工具
                if self.detail_viewer and spc_data['data']:
                    self.detail_viewer.store_data(spc_data['data'], trx_results)
                
                # 顯示摘要資訊
                if spc_data['data']:
                    result.append("")
                    result.append("📊 **資料摘要：**")
                    for i, row in enumerate(spc_data['data']):
                        if isinstance(row, dict):
                            result.append(f"**第{i+1}筆：** 玻璃ID: {row.get('SHT_ID', 'N/A')}, 設備ID: {row.get('EQPT_ID', 'N/A')}, CHART ID: {row.get('ONCHID', 'N/A')}")
                            result.append(f"         時間: {row.get('T_STAMP', 'N/A')}, 產品: {row.get('PRODUCT_ID', 'N/A')}")
                    
                    # 直接顯示SPC資料庫詳細資料
                    result.append("")
                    spc_details = self._format_spc_details(spc_data['data'])
                    result.extend(spc_details)
                
                # 添加診斷總結
                result.append("")
                result.append("---")
                result.append("🎯 **診斷總結**  ")
                result.append("✅ **結論：該筆資料已成功進入 SPC CHART**  ")
                result.append("")
                result.append("📋 **關鍵資訊：**  ")
                result.append(f"  • 玻璃ID: {info['glass_id']}  ")
                result.append(f"  • 設備ID: {info['equipment_id']}  ")
                result.append(f"  • CHART ID: {info['chart_id']}  ")
                result.append(f"  • 進入時間: {spc_data['data'][0].get('T_STAMP', 'N/A') if spc_data['data'] else 'N/A'}  ")
                result.append("---")
                
                return "\n".join(result)
            else:
                result.append("❌ **該筆資料尚未進入 CHART，繼續分析原因...**")
                result.append(f"🔍 查詢SQL: `{spc_data.get('sql', 'N/A')}`")
                if 'error' in spc_data:
                    result.append(f"❌ 錯誤: {spc_data['error']}")
                result.append("")
            
            # 步驟 11: 查詢 CHART 設定
            chart_config = self._query_chart_config(info)
            result.append("⚙️ **CHART 設定查詢結果：**")
            if chart_config["found"]:
                result.append(f"✅ 找到 CHART 設定，共 {len(chart_config['data'])} 筆")
                # 顯示 CHART 設定詳情
                if chart_config['data']:
                    chart_item = chart_config['data'][0]
                    result.append(f"**CHART設定詳情：**")
                    result.append(f"  - CHART ID: {chart_item.get('ONCHID', 'N/A')}")
                    result.append(f"  - 狀態: {chart_item.get('STATUS', 'N/A')}")
                    result.append(f"  - 設備ID: {chart_item.get('EQP_ID', 'N/A')}")
            else:
                result.append("❌ 未找到對應的 CHART 設定")
                result.append("**可能原因：CHART ID 不存在或配置錯誤**")
            result.append("")
            
            # 步驟 12-18: 分析條件比對（僅在TRX LOG成功時進行）
            if trx_results["success"]:
                analysis = self._analyze_chart_conditions(info, trx_results, chart_config)
                result.append("🔍 **條件比對分析：**")
                result.extend(analysis)
            else:
                result.append("🔍 **條件比對分析：**")
                result.append("   ⚠️ 由於TRX LOG查詢失敗，無法進行詳細條件比對")
            
            # 添加診斷總結（未進入CHART的情況）
            result.append("")
            result.append("---")
            result.append("🎯 **診斷總結**  ")
            result.append("❌ **結論：該筆資料尚未進入 SPC CHART**  ")
            result.append("")
            result.append("📋 **關鍵資訊：**  ")
            result.append(f"  • 玻璃ID: {info['glass_id']}  ")
            result.append(f"  • 設備ID: {info['equipment_id']}  ")
            result.append(f"  • CHART ID: {info['chart_id']}  ")
            result.append(f"  • TRX LOG 狀態: {'✅ 成功' if trx_results.get('success') else '❌ 失敗'}  ")
            result.append(f"  • CHART 設定: {'✅ 存在' if chart_config.get('found') else '❌ 不存在'}  ")
            result.append("")
            result.append("💡 **建議排查方向：**  ")
            if not chart_config.get("found"):
                result.append("  1. 檢查 CHART ID 是否正確配置  ")
                result.append("  2. 確認 CHART 設定是否啟用  ")
            else:
                result.append("  1. 檢查設備ID與CHART設定是否匹配  ")
                result.append("  2. 確認時間範圍是否正確  ")
                result.append("  3. 檢查資料格式是否符合CHART要求  ")
            if not trx_results["success"]:
                result.append("  4. 檢查TRX LOG查詢參數（時間、設備ID、玻璃ID）  ")
            result.append("  5. 聯繫SPC工程師進行進一步診斷  ")
            result.append("---")
            
            return "\n".join(result)
            
        except Exception as e:
            result.append(f"❌ 診斷過程發生錯誤: {str(e)}")
            return "\n".join(result)

    def _query_trx_log(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """查詢 TRX LOG (步驟 4-8)"""
        factory = info["factory"]
        timestamp = info["timestamp"]
        factory_config = self.factory_map[factory]
        
        # 計算時間範圍 (前後半小時)
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            from_dt = (dt - timedelta(minutes=30)).strftime("%Y/%m/%d %H:%M:%S")
            to_dt = (dt + timedelta(minutes=30)).strftime("%Y/%m/%d %H:%M:%S")
        except:
            return {"success": False, "messages": ["❌ 時間格式錯誤"]}
        
        messages = []
        
        try:
            # 步驟 4: 初始查詢 (pageSize=2)
            url1 = f"{self.base_url}/MesLogApi/{factory}/trx-log"
            params1 = {
                "fromDT": from_dt,
                "toDT": to_dt,
                "svrModules": factory_config["svr"],
                "shtId": info["glass_id"],
                "eqptId": info["equipment_id"],
                "lastTStamp": "",
                "pageSize": 2
            }
            
            messages.append(f"🔍 步驟4: 查詢時間範圍內的 TRX LOG...")
            messages.append(f"   URL: {url1}")
            messages.append(f"   時間範圍: {from_dt} ~ {to_dt}")
            
            # 步驟4: 實際發送 HTTP 請求
            response1 = requests.get(url1, params=params1, timeout=30)
            if response1.status_code != 200:
                messages.append(f"❌ API請求失敗: HTTP {response1.status_code}")
                return {"success": False, "messages": messages}
            
            trx_data = response1.json()
            
            # 處理不同的 API 回應格式
            if isinstance(trx_data, list):
                # 如果 API 直接返回 list
                data_list = trx_data
            elif isinstance(trx_data, dict) and "data" in trx_data:
                # 如果 API 返回包含 data 欄位的 dict
                data_list = trx_data.get("data", [])
            else:
                # 其他格式，嘗試當作 list 處理
                data_list = []
                messages.append(f"⚠️ 未預期的 API 回應格式: {type(trx_data)}")
            
            count = len(data_list)
            
            if count == 1:
                messages.append("✅ 步驟5: 時間範圍準確，找到1筆記錄")
                t_stamp = data_list[0]["tStamp"]
            elif count > 1:
                messages.append("⚠️ 步驟5: 時間範圍過大，請提供更精確的時間")
                return {"success": False, "messages": messages}
            else:
                messages.append("❌ 步驟5: 該時間範圍內無記錄")
                return {"success": False, "messages": messages}
            
            # 步驟 6: 精確查詢 (pageSize=1)
            params2 = params1.copy()
            params2["pageSize"] = 1
            messages.append(f"🔍 步驟6: 精確查詢...")
            messages.append(f"   URL: {url1}")
            messages.append(f"   參數: pageSize=1, fromDT={from_dt}, toDT={to_dt}")
            
            response2 = requests.get(url1, params=params2, timeout=30)
            if response2.status_code != 200:
                messages.append(f"❌ 步驟6 API請求失敗: HTTP {response2.status_code}")
                return {"success": False, "messages": messages}
            
            # 處理步驟6的回應
            trx_data2 = response2.json()
            messages.append(f"✅ 步驟6 查詢成功，回應資料: {json.dumps(trx_data2, ensure_ascii=False, indent=2)}")
            
            # 步驟 7: 查詢詳細資料
            url3 = f"{self.base_url}/MesLogApi/{factory}/trx-log/{factory_config['svr']}/{t_stamp}"
            params3 = {"ignoreBody": "false"}
            messages.append(f"🔍 步驟7: 查詢詳細TRX資料...")
            messages.append(f"   URL: {url3}")
            
            response3 = requests.get(url3, params=params3, timeout=30)
            if response3.status_code != 200:
                messages.append(f"❌ 步驟7 API請求失敗: HTTP {response3.status_code}")
                return {"success": False, "messages": messages}
            
            detail_data = response3.json()
            
            messages.append("✅ 步驟8: TRX LOG 查詢完成")
            messages.append("")
            messages.append("📋 **TRX LOG 詳細資料：**")
            
            # 顯示初始查詢結果 (步驟4)
            messages.append("**📊 Tab 1: 初始查詢結果 (步驟4 - pageSize=2)**")
            if data_list:
                for i, item in enumerate(data_list):
                    messages.append(f"   第{i+1}筆: {json.dumps(item, ensure_ascii=False, indent=2)}")
            else:
                messages.append("   無資料")
            
            messages.append("")
            messages.append("**📊 Tab 2: 精確查詢結果 (步驟6 - pageSize=1)**")
            if 'trx_data2' in locals():
                if isinstance(trx_data2, list):
                    for i, item in enumerate(trx_data2):
                        messages.append(f"   第{i+1}筆: {json.dumps(item, ensure_ascii=False, indent=2)}")
                elif isinstance(trx_data2, dict) and "data" in trx_data2:
                    data_list2 = trx_data2.get("data", [])
                    for i, item in enumerate(data_list2):
                        messages.append(f"   第{i+1}筆: {json.dumps(item, ensure_ascii=False, indent=2)}")
                else:
                    messages.append(f"   原始資料: {json.dumps(trx_data2, ensure_ascii=False, indent=2)}")
            else:
                messages.append("   無資料")
            
            messages.append("")
            messages.append("**📊 Tab 3: 詳細TRX資料 (步驟7)**")
            if detail_data:
                # 格式化顯示詳細資料
                if isinstance(detail_data, dict):
                    for key, value in detail_data.items():
                        if isinstance(value, (dict, list)):
                            messages.append(f"   {key}: {json.dumps(value, ensure_ascii=False, indent=2)}")
                        else:
                            messages.append(f"   {key}: {value}")
                else:
                    messages.append(f"   資料: {json.dumps(detail_data, ensure_ascii=False, indent=2)}")
            else:
                messages.append("   無詳細資料")
            
            return {
                "success": True,
                "messages": messages,
                "t_stamp": t_stamp,
                "detail": detail_data
            }
            
        except requests.RequestException as e:
            messages.append(f"❌ 網路請求錯誤: {str(e)}")
            return {"success": False, "messages": messages}
        except Exception as e:
            messages.append(f"❌ TRX LOG 查詢錯誤: {str(e)}")
            return {"success": False, "messages": messages}

    def _query_spc_db(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """查詢 SPC DB (步驟 9)"""
        factory = info["factory"]
        glass_id = info["glass_id"]
        factory_config = self.factory_map[factory]
        
        # 安全檢查：驗證 glass_id 格式
        if not self._is_safe_identifier(glass_id):
            return {
                "found": False,
                "data": [],
                "error": f"glass_id 格式不安全，已拒絕查詢: {glass_id}",
                "sql": None
            }
        
        # 構建查詢 SQL - 使用安全的字串逃逸，並加上設備ID和CHART ID條件
        safe_glass_id = glass_id.replace("'", "''")  # SQL 標準的單引號逃逸
        safe_equipment_id = info["equipment_id"].replace("'", "''")
        safe_chart_id = info["chart_id"].replace("'", "''")
        
        sql = f"""SELECT * FROM {factory_config['data_schema']}.{factory_config['glsinfo_table']} a 
        inner join {factory_config['data_schema']}.{factory_config['para_table']} b
            on a.SEQ = b.SEQ
        WHERE a.SHT_ID = '{safe_glass_id}' AND a.eqpt_id = '{safe_equipment_id}' AND b.ONCHID = '{safe_chart_id}'"""
        
        try:
            # 使用萬用查詢 API
            result = execute_query(sql, "SPC", factory, limit=10)
            
            if result['success']:
                return {
                    "found": result['row_count'] > 0,
                    "data": result['data'],
                    "sql": sql,
                    "row_count": result['row_count']
                }
            else:
                return {
                    "found": False,
                    "data": [],
                    "error": result.get('message', '查詢失敗'),
                    "sql": sql
                }
            
        except Exception as e:
            return {
                "found": False,
                "data": [],
                "error": str(e),
                "sql": sql
            }

    def _query_chart_config(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """查詢 CHART 設定 (步驟 11)"""
        factory = info["factory"]
        chart_id = info["chart_id"]
        factory_config = self.factory_map[factory]
        
        # 安全檢查：驗證 chart_id 格式
        if not self._is_safe_identifier(chart_id):
            return {
                "found": False,
                "data": [],
                "error": f"chart_id 格式不安全，已拒絕查詢: {chart_id}",
                "sql": None
            }
        
        # 構建查詢 SQL - 使用安全的字串逃逸，並使用正確的 MES schema
        safe_chart_id = chart_id.replace("'", "''")  # SQL 標準的單引號逃逸
        # 使用 MES schema 而不是 data_schema
        mes_schema = factory_config.get('mes_schema', factory_config['data_schema'])
        sql = f"SELECT * FROM {mes_schema}.{factory_config['sql_table']} WHERE ONCHID = '{safe_chart_id}'"
        
        try:
            # 使用萬用查詢 API
            result = execute_query(sql, "MES", factory, limit=10)
            
            if result['success']:
                return {
                    "found": result['row_count'] > 0,
                    "data": result['data'],
                    "sql": sql,
                    "row_count": result['row_count']
                }
            else:
                return {
                    "found": False,
                    "data": [],
                    "error": result.get('message', '查詢失敗'),
                    "sql": sql
                }
            
        except Exception as e:
            return {
                "found": False,
                "data": [],
                "error": str(e),
                "sql": sql
            }

    def _analyze_chart_conditions(self, info: Dict[str, Any], trx_results: Dict[str, Any], chart_config: Dict[str, Any]) -> List[str]:
        """分析 CHART 條件比對 (步驟 12-18)"""
        analysis = []
        factory = info["factory"]
        factory_config = self.factory_map[factory]
        
        # 儲存SPC資料用於後續步驟
        spc_data = None
        
        try:
            # 步驟 12: 根據 TRX LOG 分析 Chart_Condition
            analysis.append("📝 **步驟12: 分析TRX LOG中的Chart_Condition字串**")
            
            # 從 TRX LOG 中提取 Chart_Condition
            chart_condition = self._extract_chart_condition(trx_results)
            
            if chart_condition:
                analysis.append(f"   從TRX LOG提取的Chart_Condition: {chart_condition}")
                
                # 安全檢查 - 最重要的防護
                if not self._is_safe_stmt(chart_condition):
                    analysis.append("   ❌ **安全警告**: TRX LOG 中的 Chart_Condition 包含不安全內容，已拒絕執行以防止 SQL injection")
                    analysis.append(f"   原始 Chart_Condition: {self._sanitize_stmt_for_display(chart_condition)}")
                    analysis.append("   💡 建議：請檢查 TRX LOG 數據來源或聯繫系統管理員")
                    return analysis
                
                # 進一步驗證：確保 chart_condition 只包含安全的 WHERE 條件
                clean_condition = chart_condition.strip()
                if not clean_condition:
                    analysis.append("   ❌ TRX LOG 中的 Chart_Condition 為空，無法執行條件查詢")
                    return analysis
                
                # 構建完整 SQL，但使用額外的安全逃逸，並使用正確的 MES schema
                # 注意：Chart_Condition 中的單引號已經是正確格式，不需要再次逃逸
                mes_schema = factory_config.get('mes_schema', factory_config['data_schema'])
                sql_with_conditions = f"SELECT * FROM {mes_schema}.{factory_config['sql_table']} WHERE {clean_condition}"
                analysis.append(f"   執行查詢: {sql_with_conditions}")
                
                try:
                    # 使用萬用查詢 API 查詢符合條件的資料，不限制筆數
                    matching_result = execute_query(sql_with_conditions, "MES", factory, limit=None)
                    
                    if matching_result['success']:
                        matching_data = matching_result['data']
                        analysis.append(f"   ✅ 查詢成功，找到 {matching_result['row_count']} 筆符合條件的資料")
                    else:
                        matching_data = []
                        analysis.append(f"   ❌ 查詢失敗: {matching_result.get('message', '未知錯誤')}")
                        
                except Exception as e:
                    matching_data = []
                    analysis.append(f"   ❌ 查詢錯誤: {str(e)}")
                
                # 步驟 13: 比對是否在 CHART 中
                analysis.append("")
                analysis.append("📝 **步驟13: 比對資料是否在CHART中**")
                
                chart_data = chart_config.get("data", [])
                if matching_data:
                    # 檢查是否與 CHART 設定匹配
                    in_chart = any(item.get("ONCHID") == info["chart_id"] for item in matching_data)
                    if in_chart:
                        analysis.append("   ✅ 資料條件符合，但仍未進CHART，可能是其他問題")
                    else:
                        analysis.append("   ❌ 資料不在指定的CHART中，條件不符")
                else:
                    analysis.append("   ❌ 沒有找到符合TRX條件的資料")
                
                # 步驟 14-15: 欄位比對分析
                analysis.append("")
                analysis.append("📝 **步驟14-15: 欄位條件比對分析**")
                
                differences = self._compare_conditions(info, chart_condition, chart_data)
                if differences:
                    analysis.append("   ❌ **發現以下不相符之處：**")
                    for diff in differences:
                        analysis.append(f"     • {diff}")
                else:
                    analysis.append("   ✅ 欄位條件比對正常")
                
                # 步驟 16-18: DATA_GROUP 比對分析
                analysis.append("")
                analysis.append("📝 **步驟16-18: DATA_GROUP 比對分析**")
                
                # 獲取第9步的SPC資料
                spc_data = self._query_spc_db(info)
                
                data_group_analysis = self._analyze_data_group(info, trx_results, chart_condition, spc_data, factory_config)
                analysis.extend(data_group_analysis)
                
                # 最終總結
                analysis.append("")
                analysis.append("� **步驟18: 總結分析結果**")
                
                all_issues = []
                if differences:
                    all_issues.extend([f"條件比對問題: {diff}" for diff in differences])
                
                # 檢查DATA_GROUP相關問題
                data_group_issues = [line for line in data_group_analysis if "❌" in line or "缺少" in line]
                if data_group_issues:
                    all_issues.extend(data_group_issues)
                
                if all_issues:
                    analysis.append("   ❌ **發現的問題總結：**")
                    for issue in all_issues:
                        analysis.append(f"     • {issue}")
                    analysis.append("")
                    analysis.append("   �💡 **建議解決方案：**")
                    analysis.append("     • 檢查設備ID設定是否正確")
                    analysis.append("     • 確認CHART條件配置")
                    analysis.append("     • 檢查DATA_GROUP設定和上報")
                    analysis.append("     • 聯繫SPC工程師檢查設定")
                else:
                    analysis.append("   ✅ 所有條件比對正常")
                    analysis.append("   💡 **其他可能原因：**")
                    analysis.append("     • 資料時間戳問題")
                    analysis.append("     • 系統處理延遲")
                    analysis.append("     • 資料格式問題")
                
            else:
                analysis.append("   ❌ 無法從TRX LOG中提取Chart_Condition")
                
                # 即使沒有Chart_Condition，也執行步驟16-17的基本檢查
                analysis.append("")
                analysis.append("📝 **步驟16-17: 基本DATA_GROUP檢查（無Chart_Condition）**")
                
                # 獲取第9步的SPC資料
                spc_data = self._query_spc_db(info)
                
                # 執行基本的DATA_GROUP檢查
                basic_data_group_analysis = self._analyze_data_group_basic(info, trx_results, spc_data)
                analysis.extend(basic_data_group_analysis)
                
                # 步驟18: 總結
                analysis.append("")
                analysis.append("📝 **步驟18: 總結分析結果**")
                analysis.append("   ❌ **主要問題：無法提取Chart_Condition，無法進行完整分析**")
                analysis.append("   💡 **建議解決方案：**")
                analysis.append("     • 檢查TRX LOG格式是否正確")
                analysis.append("     • 確認Chart_Condition欄位存在")
                analysis.append("     • 聯繫系統管理員檢查TRX LOG結構")
                
        except Exception as e:
            analysis.append(f"   ❌ 條件分析錯誤: {str(e)}")
        
        return analysis

    def _extract_chart_condition(self, trx_results: Dict[str, Any]) -> str:
        """從 TRX LOG 中提取 Chart_Condition 字串"""
        try:
            detail = trx_results.get("detail", {})
            
            # 查找包含 Chart_Condition 的內容
            # 可能在不同的欄位中
            content_sources = [
                detail.get('inputTrx', ''),
                detail.get('outputTrx', ''),
                detail.get('reqBody', ''),
                detail.get('rspBody', ''),
                detail.get('stmt', ''),
                str(detail.get('evntlgDetail', {}))
            ]
            
            for content in content_sources:
                if not content:
                    continue
                    
                # 查找 Chart_Condition[...] 格式
                chart_condition_match = re.search(r'Chart_Condition\[\s*(.*?)\s*\](?:\[\d+\])?', content, re.DOTALL)
                if chart_condition_match:
                    condition = chart_condition_match.group(1).strip()
                    # 移除可能的尾部標記（如 ], lRc=1134081）
                    condition = re.sub(r'\s*,\s*lRc=\d+\s*$', '', condition)
                    return condition
            
            return ""
            
        except Exception as e:
            return ""

    def _compare_conditions(self, info: Dict[str, Any], chart_conditions: str, chart_data: List[Dict]) -> List[str]:
        """比對條件差異"""
        differences = []
        
        try:
            # 從 Chart_Condition 中提取資訊
            trx_eqp_match = re.search(r"EQPT_ID\s*=\s*'([^']+)'", chart_conditions)
            trx_glass_match = re.search(r"GLASS_ID\s*=\s*'([^']+)'", chart_conditions)
            
            if chart_data:
                chart_item = chart_data[0]  # 取第一筆 CHART 設定
                
                # 比對設備ID
                if trx_eqp_match:
                    trx_eqp = trx_eqp_match.group(1)
                    chart_eqp = chart_item.get("EQP_ID", "")
                    if trx_eqp != chart_eqp:
                        differences.append(f"設備ID不符: Chart_Condition='{trx_eqp}' vs CHART='{chart_eqp}'")
                
                # 比對玻璃ID
                if trx_glass_match:
                    trx_glass = trx_glass_match.group(1)
                    info_glass = info.get("glass_id", "")
                    if trx_glass != info_glass:
                        differences.append(f"玻璃ID不符: Chart_Condition='{trx_glass}' vs 輸入='{info_glass}'")
                
                # 檢查 CHART 狀態
                chart_status = chart_item.get("STATUS", "")
                if chart_status != "A":
                    differences.append(f"CHART狀態異常: STATUS='{chart_status}' (應為'A')")
            
        except Exception as e:
            differences.append(f"條件比對錯誤: {str(e)}")
        
        return differences
    
    def _analyze_data_group(self, info: Dict[str, Any], trx_results: Dict[str, Any], chart_condition: str, spc_data: Dict[str, Any], factory_config: Dict[str, str]) -> List[str]:
        """分析DATA_GROUP相關問題 (步驟16-17)"""
        analysis = []
        factory = info["factory"]
        
        try:
            # 步驟 16: 檢查 SPC 資料中的 DATA_GROUP 是否存在於 MES DB 中
            analysis.append("📝 **步驟16: 檢查SPC資料中的DATA_GROUP是否存在於MES DB**")
            
            if not spc_data.get("found") or not spc_data.get("data"):
                analysis.append("   ⚠️ 無SPC資料，跳過DATA_GROUP檢查")
                return analysis
            
            # 從SPC資料中獲取DATA_GROUP
            spc_records = spc_data["data"]
            data_groups = set()
            for record in spc_records:
                if isinstance(record, dict) and 'DATA_GROUP' in record:
                    data_groups.add(record['DATA_GROUP'])
            
            if not data_groups:
                analysis.append("   ⚠️ SPC資料中無DATA_GROUP欄位")
                return analysis
            
            analysis.append(f"   從SPC資料中找到DATA_GROUP: {list(data_groups)}")
            
            # 從 Chart_Condition 中提取 MES 查詢條件
            mes_conditions = self._extract_mes_conditions_from_chart(chart_condition)
            
            if not mes_conditions:
                analysis.append("   ⚠️ 無法從Chart_Condition中提取MES查詢條件")
                return analysis
            
            analysis.append(f"   從Chart_Condition提取的條件: {mes_conditions}")
            
            # 檢查每個 DATA_GROUP 是否在 MES DB 中存在
            mlitem_table = factory_config.get('mlitem_table', 'AMLITEM')
            mes_schema = factory_config.get('mes_schema', factory_config['data_schema'])
            
            data_group_missing = []
            for data_group in data_groups:
                if not self._is_safe_identifier(str(data_group)):
                    analysis.append(f"   ❌ DATA_GROUP格式不安全: {data_group}")
                    continue
                
                # 構建查詢條件
                where_conditions = []
                for key, value in mes_conditions.items():
                    if self._is_safe_identifier(str(value)):
                        where_conditions.append(f"{key} = '{value}'")
                
                where_conditions.append(f"DATA_GROUP = '{data_group}'")
                where_clause = " AND ".join(where_conditions)
                
                sql = f"SELECT * FROM {mes_schema}.{mlitem_table} WHERE {where_clause}"
                
                try:
                    result = execute_query(sql, "MES", factory, limit=1)
                    if result['success'] and result['row_count'] > 0:
                        analysis.append(f"   ✅ DATA_GROUP '{data_group}' 在MES DB中存在")
                    else:
                        analysis.append(f"   ❌ DATA_GROUP '{data_group}' 在MES DB中不存在")
                        data_group_missing.append(data_group)
                        
                except Exception as e:
                    analysis.append(f"   ❌ 查詢DATA_GROUP '{data_group}' 時發生錯誤: {str(e)}")
                    data_group_missing.append(data_group)
            
            if data_group_missing:
                analysis.append(f"   ❌ **{mlitem_table} DB缺少設定上報DATA_GROUP: {data_group_missing}**")
            
            # 步驟 17: 檢查 TRX LOG INPUT 中的 data_group 標籤
            analysis.append("")
            analysis.append("📝 **步驟17: 檢查TRX LOG INPUT中的data_group標籤**")
            
            trx_data_groups = self._extract_data_groups_from_trx(trx_results)
            
            if not trx_data_groups:
                analysis.append("   ❌ **缺少必要上報DATA_GROUP** - TRX LOG INPUT中未找到data_group標籤")
            else:
                analysis.append(f"   從TRX LOG INPUT提取的data_group: {trx_data_groups}")
                
                # 比對 SPC 和 TRX 的 DATA_GROUP
                missing_in_trx = data_groups - set(trx_data_groups)
                if missing_in_trx:
                    analysis.append(f"   ❌ **缺少必要上報DATA_GROUP** - SPC中有但TRX INPUT中沒有: {list(missing_in_trx)}")
                else:
                    analysis.append("   ✅ TRX LOG INPUT包含所需的data_group")
            
        except Exception as e:
            analysis.append(f"   ❌ DATA_GROUP分析錯誤: {str(e)}")
        
        return analysis
    
    def _extract_mes_conditions_from_chart(self, chart_condition: str) -> Dict[str, str]:
        """從Chart_Condition中提取MES查詢條件"""
        conditions = {}
        
        # 提取各種條件
        patterns = {
            'EQPT_ID': r"EQPT_ID\s*=\s*'([^']+)'",
            'REP_UNIT': r"REP_UNIT\s*=\s*'([^']+)'", 
            'DATA_PAT': r"DATA_PAT\s*=\s*'([^']+)'",
            'MES_ID': r"MES_ID\s*=\s*'([^']+)'"
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, chart_condition)
            if match:
                conditions[field] = match.group(1)
        
        return conditions
    
    def _extract_data_groups_from_trx(self, trx_results: Dict[str, Any]) -> List[str]:
        """從TRX LOG INPUT中提取data_group標籤數值"""
        data_groups = []
        
        try:
            detail = trx_results.get("detail", {})
            
            # 查找輸入交易XML
            input_sources = [
                detail.get('inputTrx', ''),
                detail.get('input_trx', ''),
                detail.get('reqBody', '')
            ]
            
            if 'evntlgDetail' in detail:
                event_detail = detail['evntlgDetail']
                input_sources.extend([
                    event_detail.get('inputTrx', ''),
                    event_detail.get('reqBody', '')
                ])
            
            for input_xml in input_sources:
                if not input_xml:
                    continue
                
                # 查找data_group標籤
                data_group_matches = re.findall(r'<data_group[^>]*>([^<]+)</data_group>', input_xml, re.IGNORECASE)
                data_groups.extend(data_group_matches)
                
                # 也查找可能的其他格式
                data_group_matches2 = re.findall(r'data_group["\']?\s*[:=]\s*["\']?([^"\'>\s,]+)', input_xml, re.IGNORECASE)
                data_groups.extend(data_group_matches2)
        
        except Exception as e:
            pass
        
        # 去重並返回
        return list(set(data_groups))
    
    def _analyze_data_group_basic(self, info: Dict[str, Any], trx_results: Dict[str, Any], spc_data: Dict[str, Any]) -> List[str]:
        """基本DATA_GROUP檢查（當無Chart_Condition時）"""
        analysis = []
        
        try:
            # 檢查SPC資料中的DATA_GROUP
            analysis.append("📝 **檢查SPC資料中的DATA_GROUP**")
            
            if not spc_data.get("found") or not spc_data.get("data"):
                analysis.append("   ⚠️ 無SPC資料，無法檢查DATA_GROUP")
            else:
                spc_records = spc_data["data"]
                data_groups = set()
                for record in spc_records:
                    if isinstance(record, dict) and 'DATA_GROUP' in record:
                        data_groups.add(record['DATA_GROUP'])
                
                if data_groups:
                    analysis.append(f"   📋 SPC資料中的DATA_GROUP: {list(data_groups)}")
                else:
                    analysis.append("   ⚠️ SPC資料中無DATA_GROUP欄位")
            
            # 檢查TRX LOG INPUT中的data_group
            analysis.append("")
            analysis.append("📝 **檢查TRX LOG INPUT中的data_group標籤**")
            
            trx_data_groups = self._extract_data_groups_from_trx(trx_results)
            
            if not trx_data_groups:
                analysis.append("   ❌ **缺少必要上報DATA_GROUP** - TRX LOG INPUT中未找到data_group標籤")
            else:
                analysis.append(f"   ✅ TRX LOG INPUT中的data_group: {trx_data_groups}")
                
                # 如果有SPC資料，進行簡單比對
                if spc_data.get("found") and spc_data.get("data"):
                    spc_records = spc_data["data"]
                    spc_data_groups = set()
                    for record in spc_records:
                        if isinstance(record, dict) and 'DATA_GROUP' in record:
                            spc_data_groups.add(record['DATA_GROUP'])
                    
                    if spc_data_groups:
                        missing_in_trx = spc_data_groups - set(trx_data_groups)
                        if missing_in_trx:
                            analysis.append(f"   ⚠️ SPC中有但TRX INPUT中沒有的data_group: {list(missing_in_trx)}")
                        else:
                            analysis.append("   ✅ TRX LOG INPUT包含SPC所需的data_group")
            
        except Exception as e:
            analysis.append(f"   ❌ 基本DATA_GROUP檢查錯誤: {str(e)}")
        
        return analysis
    
    def _format_trx_details(self, trx_results: Dict) -> List[str]:
        """格式化TRX LOG詳細資料"""
        details = []
        
        if not trx_results.get("success") or 'detail' not in trx_results:
            return details
        
        detail = trx_results['detail']
        
        # 基本資訊表格
        details.append("### 📋 TRX LOG 基本資訊")
        details.append("")
        details.append("| 項目 | 值 |")
        details.append("|------|-----|")
        
        # 嘗試從不同可能的資料結構中提取資訊
        basic_info = {}
        
        # 如果detail是字典且包含evntlgDetail
        if isinstance(detail, dict) and 'evntlgDetail' in detail:
            event_detail = detail['evntlgDetail']
            basic_info = {
                '時間戳記': event_detail.get('tStamp', trx_results.get('t_stamp', 'N/A')),
                '設備ID': event_detail.get('eqptId', 'N/A'),
                '玻璃ID': event_detail.get('shtId', 'N/A'),
                '載盤ID': event_detail.get('crrId', 'N/A'),
                '錯誤碼': event_detail.get('errcode', 'N/A'),
                '處理時間': f"{event_detail.get('procTime', 'N/A')}ms" if event_detail.get('procTime') != 'N/A' else 'N/A'
            }
        # 如果detail直接包含這些欄位
        elif isinstance(detail, dict):
            basic_info = {
                '時間戳記': detail.get('tStamp', trx_results.get('t_stamp', 'N/A')),
                '設備ID': detail.get('eqptId', 'N/A'),
                '玻璃ID': detail.get('shtId', 'N/A'),
                '載盤ID': detail.get('crrId', 'N/A'),
                '錯誤碼': detail.get('errcode', 'N/A'),
                '處理時間': f"{detail.get('procTime', 'N/A')}ms" if detail.get('procTime') != 'N/A' else 'N/A'
            }
        
        # 如果都沒有，從TRX results本身獲取
        if all(v == 'N/A' for v in basic_info.values()):
            basic_info = {
                '時間戳記': trx_results.get('t_stamp', 'N/A'),
                '設備ID': 'N/A',
                '玻璃ID': 'N/A', 
                '載盤ID': 'N/A',
                '錯誤碼': 'N/A',
                '處理時間': 'N/A'
            }
        
        for field_name, value in basic_info.items():
            details.append(f"| {field_name} | {value} |")
        
        details.append("")
        
        # 輸入交易XML (格式化)
        input_trx = None
        if isinstance(detail, dict):
            # 嘗試不同的欄位名稱
            input_trx = detail.get('inputTrx') or detail.get('input_trx') or detail.get('reqBody')
            if 'evntlgDetail' in detail:
                event_detail = detail['evntlgDetail']
                input_trx = input_trx or event_detail.get('inputTrx') or event_detail.get('reqBody')
        
        if input_trx:
            details.append("### 📥 輸入交易 XML")
            details.append("```xml")
            details.append(self._format_xml_pretty(input_trx))
            details.append("```")
            details.append("")
        
        # 輸出交易XML
        output_trx = None
        if isinstance(detail, dict):
            # 嘗試不同的欄位名稱
            output_trx = detail.get('outputTrx') or detail.get('output_trx') or detail.get('rspBody')
            if 'evntlgDetail' in detail:
                event_detail = detail['evntlgDetail']
                output_trx = output_trx or event_detail.get('outputTrx') or event_detail.get('rspBody')
        
        if output_trx:
            details.append("### 📤 輸出交易 XML")
            details.append("```xml") 
            details.append(self._format_xml_pretty(output_trx))
            details.append("```")
            details.append("")
        
        return details
    
    def _format_spc_details(self, spc_data: List[Dict]) -> List[str]:
        """格式化SPC資料庫詳細資料"""
        details = []
        
        if not spc_data:
            return details
        
        details.append("### 📊 SPC 資料庫詳細記錄")
        details.append("")
        
        for i, record in enumerate(spc_data):
            details.append(f"#### 📋 第{i+1}筆記錄")
            details.append("")
            details.append("| 欄位名稱 | 值 |")
            details.append("|----------|-----|")
            
            # 重要欄位優先顯示
            important_fields = [
                ('基本資訊', ['T_STAMP', 'SHT_ID', 'LOT_ID', 'CRR_ID', 'PRODUCT_ID']),
                ('設備資訊', ['EQPT_ID', 'ONCHID', 'CLDATE', 'CLTIME', 'PROC_ID']),
                ('數值資訊', ['DTX', 'USPEC', 'LSPEC', 'TARGET', 'UCL1', 'LCL1']),
                ('狀態資訊', ['OOS', 'OOC1', 'OOC2', 'OOC3', 'DELFLG', 'DATA_GROUP'])
            ]
            
            for category, fields in important_fields:
                details.append(f"| **{category}** | |")
                for field in fields:
                    if field in record:
                        value = record[field]
                        if value is None:
                            value = 'NULL'
                        elif isinstance(value, (int, float)):
                            value = str(value)
                        elif isinstance(value, str):
                            # 截斷過長的字串
                            value = value[:50] + "..." if len(value) > 50 else value
                        details.append(f"| {field} | {value} |")
            
            details.append("")
            
            # 如果有多筆記錄，在記錄間加分隔線
            if i < len(spc_data) - 1:
                details.append("---")
                details.append("")
        
        return details
    
    def _format_xml_pretty(self, xml_content: str) -> str:
        """美化XML格式"""
        try:
            import xml.etree.ElementTree as ET
            import re
            
            # 清理XML內容
            xml_content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', xml_content)
            
            # 解析XML
            root = ET.fromstring(xml_content)
            
            # 美化格式
            def indent_xml(elem, level=0):
                indent_str = "\n" + level * "  "
                if len(elem):
                    if not elem.text or not elem.text.strip():
                        elem.text = indent_str + "  "
                    if not elem.tail or not elem.tail.strip():
                        elem.tail = indent_str
                    for child in elem:
                        indent_xml(child, level + 1)
                    if not child.tail or not child.tail.strip():
                        child.tail = indent_str
                else:
                    if level and (not elem.tail or not elem.tail.strip()):
                        elem.tail = indent_str
            
            indent_xml(root)
            return ET.tostring(root, encoding='unicode')
            
        except Exception as e:
            # 如果XML解析失敗，返回原始內容
            return xml_content


