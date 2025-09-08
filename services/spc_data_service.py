"""
SPC 資料查詢服務 - 專門處理 SPC 系統的資料查詢和診斷
"""

import os
import json
import sqlite3
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

# 添加專案根目錄到路徑以導入db2_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.db2_service import DB2Service, validate_sql

class SPCDataService:
    """SPC 資料查詢服務"""
    
    def __init__(self):
        # TODO: 替換為實際的資料庫連線資訊
        self.db2service = DB2Service()
        print("📊 SPC 資料查詢服務初始化完成")
    
    def query_chart_data(self, glass_id: str = None, equipment_id: str = None, 
                        chart_id: str = None, data_group: str = None) -> Dict[str, Any]:
        """查詢 CHART 資料 - 先從MES DB查詢線上圖表，再從SPC DB查詢製程資料"""
        
        try:
            # 檢查必要參數
            if not glass_id or not equipment_id or not chart_id or not data_group:
                return {
                    "success": False,
                    "error": "缺少必要參數：glass_id（玻璃ID）、equipment_id（設備ID）、chart_id（圖表ID）、data_group（資料群組）",
                    "data": None
                }
            
            # 步驟1: 從MES DB查詢線上圖表資料
            mes_result = self._query_mes_online_chart(equipment_id, chart_id)
            if not mes_result["success"]:
                return mes_result
            
            # 步驟2: 從SPC DB查詢製程資料
            spc_result = self._query_spc_process_data(glass_id, equipment_id, chart_id, data_group)
            if not spc_result["success"]:
                return spc_result
            
            # 合併結果
            return {
                "success": True,
                "source": "mes_and_spc_database",
                "data": {
                    "mes_chart_data": mes_result["data"],
                    "spc_process_data": spc_result["data"],
                    "total_mes_records": len(mes_result["data"]["results"]) if mes_result["data"]["results"] else 0,
                    "total_spc_records": len(spc_result["data"]["results"]) if spc_result["data"]["results"] else 0
                },
                "query_info": {
                    "glass_id": glass_id,
                    "equipment_id": equipment_id,
                    "chart_id": chart_id,
                    "data_group": data_group,
                    "mes_query_info": mes_result.get("query_info"),
                    "spc_query_info": spc_result.get("query_info")
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"查詢過程發生錯誤: {str(e)}",
                "data": None
            }
    
    def _query_from_db2_database(self, glass_id: str, equipment_id: str, 
                               chart_id: str, timestamp: str) -> Dict[str, Any]:
        """使用DB2Service從資料庫查詢資料"""
        
        try:
            # 檢查DB2Service是否可用
            if not self.db2service.is_odbc_available():
                return {
                    "success": False,
                    "error": "ODBC模組不可用，請安裝: pip install pyodbc",
                    "data": None
                }

            # 檢查必要參數
            if not timestamp or not equipment_id or not glass_id:
                return {
                    "success": False,
                    "error": "缺少必要參數：timestamp（時間戳）、equipment_id（設備ID）、glass_id（玻璃ID）",
                    "data": None
                }

            # 解析時間並計算前後半小時
            try:
                from datetime import datetime, timedelta
                
                # 解析傳入的時間戳
                if isinstance(timestamp, str):
                    # 支援多種時間格式
                    time_formats = [
                        '%Y-%m-%d %H:%M:%S.%f',  # 2021-11-09 00:55:18.000000
                        '%Y-%m-%d %H:%M:%S',     # 2021-11-09 00:55:18
                        '%Y-%m-%d %H:%M',        # 2021-11-09 00:55
                    ]
                    
                    parsed_time = None
                    for fmt in time_formats:
                        try:
                            parsed_time = datetime.strptime(timestamp, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if parsed_time is None:
                        raise ValueError(f"無法解析時間格式: {timestamp}")
                else:
                    parsed_time = timestamp
                
                # 計算前後半小時
                start_time = parsed_time - timedelta(minutes=30)
                end_time = parsed_time + timedelta(minutes=30)
                
                # 格式化為DB2需要的格式
                start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')
                end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S.%f')
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"時間格式錯誤: {str(e)}",
                    "data": None
                }

            # 根據設備ID判斷廠別並設定表格名稱
            factory_tables = self._get_factory_tables(equipment_id)
            para_table = factory_tables['para_table']
            info_table = factory_tables['info_table']
            
            # 構建複雜的SQL查詢
            sql = f"""
            SELECT * FROM {para_table} 
            WHERE SEQ IN (
                SELECT SEQ FROM {info_table} 
                WHERE T_STAMP > '{start_time_str}' 
                AND T_STAMP < '{end_time_str}' 
                AND EQPT_ID = '{equipment_id}' 
                AND SHT_ID = '{glass_id}'
            )
            """
            
            print(f"🔍 執行DB2查詢:")
            print(f"   設備ID: {equipment_id}")
            print(f"   玻璃ID: {glass_id}")
            print(f"   時間範圍: {start_time_str} ~ {end_time_str}")
            print(f"   PARA表: {para_table}")
            print(f"   INFO表: {info_table}")
            print(f"   SQL: {sql}")
            
            # 執行查詢
            results, columns = self.db2service.execute_select_smart(
                factory_tables['database'],
                sql,
                limit=1000  # 增加限制以處理更多資料
            )
            
            return {
                "success": True,
                "source": "db2_database",
                "data": {
                    "results": results,
                    "columns": columns,
                    "total_records": len(results)
                },
                "query_info": {
                    "database": factory_tables['database'],
                    "para_table": para_table,
                    "info_table": info_table,
                    "equipment_id": equipment_id,
                    "glass_id": glass_id,
                    "time_range": f"{start_time_str} ~ {end_time_str}",
                    "sql": sql,
                    "execution_method": "ODBC"
                }
            }
            
        except Exception as e:
            print(f"❌ DB2查詢錯誤: {str(e)}")
            return {
                "success": False,
                "error": f"DB2資料庫查詢錯誤: {str(e)}",
                "data": None,
                "query_info": {
                    "attempted_equipment_id": equipment_id,
                    "attempted_glass_id": glass_id,
                    "attempted_timestamp": timestamp
                }
            }
    
    def _query_mes_online_chart(self, equipment_id: str, chart_id: str) -> Dict[str, Any]:
        """從MES資料庫查詢線上圖表資料"""
        
        try:
            # 檢查DB2Service是否可用
            if not self.db2service.is_odbc_available():
                return {
                    "success": False,
                    "error": "ODBC模組不可用，請安裝: pip install pyodbc",
                    "data": None
                }
            
            # 根據設備ID判斷廠別並設定MES表格名稱
            factory_info = self._get_factory_tables(equipment_id)
            database = factory_info['database']
            
            # 根據廠別選擇對應的MES線上圖表表格
            mes_chart_table = self._get_mes_chart_table(equipment_id)
            
            # 構建MES查詢SQL
            mes_sql = f"SELECT * FROM {mes_chart_table} WHERE ONCHID = '{chart_id}'"
            
            print(f"🔍 執行MES查詢:")
            print(f"   資料庫: {database}")
            print(f"   圖表表格: {mes_chart_table}")
            print(f"   圖表ID: {chart_id}")
            print(f"   SQL: {mes_sql}")
            
            # 執行MES查詢
            results, columns = self.db2service.execute_mes_query(
                database,
                mes_sql,
                limit=100
            )
            
            return {
                "success": True,
                "source": "mes_database",
                "data": {
                    "results": results,
                    "columns": columns,
                    "total_records": len(results)
                },
                "query_info": {
                    "database": database,
                    "chart_table": mes_chart_table,
                    "chart_id": chart_id,
                    "sql": mes_sql,
                    "execution_method": "MES_ODBC"
                }
            }
            
        except Exception as e:
            print(f"❌ MES查詢錯誤: {str(e)}")
            return {
                "success": False,
                "error": f"MES資料庫查詢錯誤: {str(e)}",
                "data": None,
                "query_info": {
                    "attempted_chart_id": chart_id,
                    "attempted_equipment_id": equipment_id
                }
            }
    
    def _query_spc_process_data(self, glass_id: str, equipment_id: str, chart_id: str, data_group: str) -> Dict[str, Any]:
        """從SPC資料庫查詢製程資料"""
        
        try:
            # 根據設備ID判斷廠別並設定SPC表格名稱
            factory_tables = self._get_factory_tables(equipment_id)
            para_table = factory_tables['para_table']
            info_table = factory_tables['info_table']
            database = factory_tables['database']
            
            # 構建SPC查詢SQL - JOIN HAMSGLSINFO和HAMSPARA
            spc_sql = f"""
            SELECT 
                H.*,
                P.*
            FROM 
                {info_table} H
            JOIN 
                {para_table} P ON H.SEQ = P.SEQ
            WHERE 
                H.SHT_ID = '{glass_id}' AND
                P.DATA_GROUP = '{data_group}' AND 
                H.EQPT_ID = '{equipment_id}' AND 
                P.ONCHID = '{chart_id}'
            """
            
            print(f"🔍 執行SPC查詢:")
            print(f"   資料庫: {database}")
            print(f"   PARA表: {para_table}")
            print(f"   INFO表: {info_table}")
            print(f"   玻璃ID: {glass_id}")
            print(f"   設備ID: {equipment_id}")
            print(f"   圖表ID: {chart_id}")
            print(f"   資料群組: {data_group}")
            print(f"   SQL: {spc_sql}")
            
            # 執行SPC查詢
            results, columns = self.db2service.execute_spc_query(
                database,
                spc_sql,
                limit=1000
            )
            
            return {
                "success": True,
                "source": "spc_database",
                "data": {
                    "results": results,
                    "columns": columns,
                    "total_records": len(results)
                },
                "query_info": {
                    "database": database,
                    "para_table": para_table,
                    "info_table": info_table,
                    "glass_id": glass_id,
                    "equipment_id": equipment_id,
                    "chart_id": chart_id,
                    "data_group": data_group,
                    "sql": spc_sql,
                    "execution_method": "SPC_ODBC"
                }
            }
            
        except Exception as e:
            print(f"❌ SPC查詢錯誤: {str(e)}")
            return {
                "success": False,
                "error": f"SPC資料庫查詢錯誤: {str(e)}",
                "data": None,
                "query_info": {
                    "attempted_glass_id": glass_id,
                    "attempted_equipment_id": equipment_id,
                    "attempted_chart_id": chart_id,
                    "attempted_data_group": data_group
                }
            }
    
    def _get_mes_chart_table(self, equipment_id: str) -> str:
        """根據設備ID判斷MES線上圖表表格名稱"""
        
        equipment_upper = equipment_id.upper()
        
        if equipment_upper.startswith('T6') or 'TFT6' in equipment_upper:
            return 'T6WPT1D.ASPC_ONLNCHART'  # 修正schema為T6WPT1D
        elif equipment_upper.startswith('F6') or 'CF6' in equipment_upper:
            return 'F6WPT1D.BSPC_ONLNCHART'  # 修正schema為F6WPT1D
        elif equipment_upper.startswith('L6') or 'LCD6' in equipment_upper:
            return 'L6WPT1D.CSPC_ONLNCHART'  # 修正schema為L6WPT1D
        elif equipment_upper.startswith('U3') or 'USL' in equipment_upper:
            return 'U3WPT1D.CSPC_ONLNCHART'  # 修正schema為U3WPT1D
        else:
            # 預設使用TFT6的表格
            return 'T6WPT1D.ASPC_ONLNCHART'
    
    def _get_factory_tables(self, equipment_id: str) -> Dict[str, str]:
        """根據設備ID判斷廠別並返回對應的表格名稱"""
        
        # 根據設備ID的命名規則判斷廠別
        equipment_upper = equipment_id.upper()
        
        if equipment_upper.startswith('T6') or 'TFT6' in equipment_upper:
            # TFT6廠 - 使用實際查到的schema和表格名稱
            return {
                'database': 'TFT6',
                'para_table': 'T6HEC1D.HAMSPARA',
                'info_table': 'T6HEC1D.HAMSGLSINFO'
            }
        elif equipment_upper.startswith('F6') or 'CF6' in equipment_upper:
            # CF6廠 - 假設有類似的schema結構
            return {
                'database': 'CF6', 
                'para_table': 'F6HEC1D.HBMSPARA',
                'info_table': 'F6HEC1D.HBMSGLSINFO'
            }
        elif equipment_upper.startswith('L6') or 'LCD6' in equipment_upper:
            # LCD6廠 - 假設有類似的schema結構
            return {
                'database': 'LCD6',
                'para_table': 'L6HEC1D.HCMSPARA', 
                'info_table': 'L6HEC1D.HCMSGLSINFO'
            }
        elif equipment_upper.startswith('U3') or 'USL' in equipment_upper:
            # USL廠 - 假設有類似的schema結構
            return {
                'database': 'USL',
                'para_table': 'U3HEC1D.HDMSPARA',
                'info_table': 'U3HEC1D.HDMSGLSINFO' 
            }
        else:
            # 預設使用TFT6的實際schema和表格，適用於PIPR等設備
            return {
                'database': 'TFT6',
                'para_table': 'T6HEC1D.HAMSPARA',  # 使用實際存在的表格
                'info_table': 'T6HEC1D.HAMSGLSINFO'  # 使用實際存在的表格
            }
        
