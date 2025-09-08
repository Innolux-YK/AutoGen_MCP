"""
萬用SQL查詢API
支援SPC和MES資料庫的SELECT查詢，返回JSON格式結果
安全性：只允許SELECT語句，防止資料被意外修改或刪除
"""

import json
import logging
import sys
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import traceback

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db2_service import DB2Service

# 直接導入API logger模組
try:
    import sys
    import os
    utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
    sys.path.insert(0, utils_path)
    from api_logger import APILogger
    
    # 創建API logger實例
    api_logger = APILogger("UniversalQueryAPI")
    
    def generate_request_id() -> str:
        import hashlib
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        hash_obj = hashlib.md5(timestamp.encode())
        return hash_obj.hexdigest()[:8]
        
except ImportError as e:
    print(f"API Logger導入失敗: {e}")
    # 如果無法導入API日誌模組，使用簡化版本
    import hashlib
    from datetime import datetime
    
    class SimpleAPILogger:
        def log_api_request(self, *args, **kwargs): 
            print(f"API請求: {args} {kwargs}")
        def log_api_response(self, *args, **kwargs): 
            print(f"API回應: {args} {kwargs}")
        def log_api_error(self, *args, **kwargs): 
            print(f"API錯誤: {args} {kwargs}")
        def log_connection_test(self, *args, **kwargs): 
            print(f"連接測試: {args} {kwargs}")
    
    api_logger = SimpleAPILogger()
    
    def generate_request_id() -> str:
        timestamp = datetime.now().isoformat()
        hash_obj = hashlib.md5(timestamp.encode())
        return hash_obj.hexdigest()[:8]


class UniversalQueryAPI:
    """萬用SQL查詢API類別"""
    
    def __init__(self):
        self.db_service = DB2Service()
        self.logger = self._setup_logger()
        
        # 支援的資料庫類型
        self.supported_db_types = ["SPC", "MES"]
        
        # 支援的資料庫名稱
        self.supported_db_names = ["TFT6", "CF6", "LCD6", "USL"]
    
    def _setup_logger(self) -> logging.Logger:
        """設置日志記錄器"""
        logger = logging.getLogger(f"{__name__}.UniversalQueryAPI")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def validate_parameters(
        self, 
        sql: str, 
        db_source: str, 
        db_name: str
    ) -> tuple[bool, str]:
        """
        驗證輸入參數
        
        Args:
            sql: SQL查詢語句
            db_source: 資料庫來源 (SPC/MES)
            db_name: 資料庫名稱 (TFT6/CF6/LCD6/USL)
            
        Returns:
            tuple[bool, str]: (是否有效, 錯誤信息)
        """
        # 檢查SQL語句
        if not sql or not isinstance(sql, str):
            return False, "SQL語句不能為空"
        
        # 檢查資料庫來源
        if not db_source or db_source.upper() not in self.supported_db_types:
            return False, f"不支援的資料庫來源: {db_source}，支援的類型: {', '.join(self.supported_db_types)}"
        
        # 檢查資料庫名稱
        if not db_name or db_name.upper() not in self.supported_db_names:
            return False, f"不支援的資料庫名稱: {db_name}，支援的名稱: {', '.join(self.supported_db_names)}"
        
        # 使用DB2Service驗證SQL語句
        is_valid, message = self.db_service.validate_select_query(sql)
        if not is_valid:
            return False, f"SQL驗證失敗: {message}"
        
        return True, "參數驗證成功"
    
    def query(
        self, 
        sql: str, 
        db_source: str, 
        db_name: str, 
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        執行SQL查詢並返回JSON結果
        
        Args:
            sql: SQL查詢語句 (只允許SELECT)
            db_source: 資料庫來源 ("SPC" 或 "MES")
            db_name: 資料庫名稱 ("TFT6", "CF6", "LCD6", "USL")
            limit: 結果數量限制 (可選)
            
        Returns:
            Dict[str, Any]: JSON格式的查詢結果
            {
                "success": bool,
                "message": str,
                "data": List[Dict[str, Any]],
                "columns": List[str],
                "row_count": int,
                "query_info": {
                    "sql": str,
                    "db_source": str,
                    "db_name": str,
                    "limit": int,
                    "timestamp": str
                },
                "error": str (僅在失敗時)
            }
        """
        # 生成請求ID用於日誌追蹤
        request_id = generate_request_id()
        
        # 記錄API請求
        api_logger.log_api_request(
            request_id=request_id,
            method="QUERY",
            sql=sql,
            db_source=db_source,
            db_name=db_name,
            limit=limit
        )
        
        # 記錄查詢開始時間
        start_time = datetime.now()
        
        # 建立回應結構
        response = {
            "success": False,
            "message": "",
            "data": [],
            "columns": [],
            "row_count": 0,
            "query_info": {
                "request_id": request_id,
                "sql": sql,
                "db_source": db_source.upper() if db_source else "",
                "db_name": db_name.upper() if db_name else "",
                "limit": limit,
                "timestamp": start_time.isoformat()
            }
        }
        
        try:
            # 參數驗證
            is_valid, validation_message = self.validate_parameters(sql, db_source, db_name)
            if not is_valid:
                response["message"] = validation_message
                response["error"] = validation_message
                self.logger.error(f"[{request_id}] 參數驗證失敗: {validation_message}")
                
                # 記錄錯誤到API日誌
                api_logger.log_api_error(
                    request_id=request_id,
                    error_type="ValidationError",
                    error_message=validation_message,
                    sql=sql,
                    db_source=db_source,
                    db_name=db_name
                )
                
                return response
            
            # 標準化參數
            db_source = db_source.upper()
            db_name = db_name.upper()
            
            self.logger.info(f"[{request_id}] 開始執行查詢: {db_source}-{db_name}")
            self.logger.info(f"[{request_id}] SQL: {sql}")
            
            # 執行查詢
            results, columns = self.db_service.execute_select_query_odbc(
                db_name=db_name,
                sql=sql,
                limit=limit,
                db_type=db_source
            )
            
            # 計算執行時間
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 建立成功回應
            response.update({
                "success": True,
                "message": f"查詢成功執行，返回 {len(results)} 筆記錄",
                "data": results,
                "columns": columns,
                "row_count": len(results),
            })
            
            # 更新查詢資訊
            response["query_info"].update({
                "execution_time_seconds": round(execution_time, 3),
                "end_timestamp": end_time.isoformat()
            })
            
            self.logger.info(f"[{request_id}] 查詢成功完成: {len(results)} 筆記錄，耗時 {execution_time:.3f} 秒")
            
            # 記錄API成功回應
            api_logger.log_api_response(
                request_id=request_id,
                success=True,
                message=response["message"],
                row_count=len(results),
                execution_time=execution_time,
                data_sample=results[:3] if results else [],  # 只記錄前3筆作為樣本
                columns=columns
            )
            
        except Exception as e:
            # 記錄錯誤
            error_message = str(e)
            error_trace = traceback.format_exc()
            
            response.update({
                "success": False,
                "message": f"查詢執行失敗: {error_message}",
                "error": error_message
            })
            
            self.logger.error(f"[{request_id}] 查詢執行失敗: {error_message}")
            self.logger.debug(f"[{request_id}] 錯誤堆疊: {error_trace}")
            
            # 記錄API錯誤回應
            api_logger.log_api_error(
                request_id=request_id,
                error_type=type(e).__name__,
                error_message=error_message,
                stack_trace=error_trace,
                sql=sql,
                db_source=db_source,
                db_name=db_name
            )
            
            # 記錄失敗的API回應
            api_logger.log_api_response(
                request_id=request_id,
                success=False,
                message=response["message"],
                error=error_message
            )
        
        return response
    
    def query_with_params(
        self, 
        sql: str, 
        params: List[Any], 
        db_source: str, 
        db_name: str, 
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        執行帶參數的SQL查詢
        
        Args:
            sql: 包含參數佔位符(?)的SQL查詢語句
            params: 參數列表
            db_source: 資料庫來源 ("SPC" 或 "MES")
            db_name: 資料庫名稱 ("TFT6", "CF6", "LCD6", "USL")
            limit: 結果數量限制 (可選)
            
        Returns:
            Dict[str, Any]: JSON格式的查詢結果
        """
        # 記錄查詢開始時間
        start_time = datetime.now()
        
        # 建立回應結構
        response = {
            "success": False,
            "message": "",
            "data": [],
            "columns": [],
            "row_count": 0,
            "query_info": {
                "sql": sql,
                "params": params,
                "db_source": db_source.upper() if db_source else "",
                "db_name": db_name.upper() if db_name else "",
                "limit": limit,
                "timestamp": start_time.isoformat()
            }
        }
        
        try:
            # 參數驗證
            is_valid, validation_message = self.validate_parameters(sql, db_source, db_name)
            if not is_valid:
                response["message"] = validation_message
                response["error"] = validation_message
                self.logger.error(f"參數驗證失敗: {validation_message}")
                return response
            
            # 檢查參數
            if not isinstance(params, list):
                response["message"] = "參數必須是列表格式"
                response["error"] = "參數必須是列表格式"
                return response
            
            # 標準化參數
            db_source = db_source.upper()
            db_name = db_name.upper()
            
            self.logger.info(f"開始執行參數化查詢: {db_source}-{db_name}")
            self.logger.info(f"SQL: {sql}")
            self.logger.info(f"參數: {params}")
            
            # 執行查詢 (注意：需要修改db_service支援不同db_type)
            # 暫時使用標準方法，未來可擴展支援MES
            if db_source == "MES":
                # 目前DB2Service可能不支援MES類型的參數化查詢
                # 這裡我們需要手動處理
                results, columns = self._execute_mes_query_with_params(
                    db_name, sql, params, limit
                )
            else:
                results, columns = self.db_service.execute_select_query_with_params(
                    db_name=db_name,
                    sql=sql,
                    params=params,
                    limit=limit
                )
            
            # 計算執行時間
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 建立成功回應
            response.update({
                "success": True,
                "message": f"參數化查詢成功執行，返回 {len(results)} 筆記錄",
                "data": results,
                "columns": columns,
                "row_count": len(results),
            })
            
            # 更新查詢資訊
            response["query_info"].update({
                "execution_time_seconds": round(execution_time, 3),
                "end_timestamp": end_time.isoformat()
            })
            
            self.logger.info(f"參數化查詢成功完成: {len(results)} 筆記錄，耗時 {execution_time:.3f} 秒")
            
        except Exception as e:
            # 記錄錯誤
            error_message = str(e)
            error_trace = traceback.format_exc()
            
            response.update({
                "success": False,
                "message": f"參數化查詢執行失敗: {error_message}",
                "error": error_message
            })
            
            self.logger.error(f"參數化查詢執行失敗: {error_message}")
            self.logger.debug(f"錯誤堆疊: {error_trace}")
        
        return response
    
    def _execute_mes_query_with_params(
        self, 
        db_name: str, 
        sql: str, 
        params: List[Any], 
        limit: Optional[int] = None
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        執行MES資料庫的參數化查詢
        這是一個臨時方法，直到DB2Service完全支援MES類型
        """
        # 這裡需要實現MES資料庫的連接邏輯
        # 暫時拋出異常，提示需要實現
        raise NotImplementedError("MES參數化查詢尚未實現，請使用非參數化查詢")
    
    def get_supported_databases(self) -> Dict[str, Any]:
        """
        獲取支援的資料庫清單
        
        Returns:
            Dict[str, Any]: 支援的資料庫資訊
        """
        return {
            "supported_db_types": self.supported_db_types,
            "supported_db_names": self.supported_db_names,
            "database_info": {
                "SPC": {
                    "description": "SPC (Statistical Process Control) 資料庫",
                    "databases": {
                        "TFT6": "TFT6 SPC資料庫",
                        "CF6": "CF6 SPC資料庫", 
                        "LCD6": "LCD6 SPC資料庫",
                        "USL": "USL SPC資料庫"
                    }
                },
                "MES": {
                    "description": "MES (Manufacturing Execution System) 資料庫",
                    "databases": {
                        "TFT6": "TFT6 MES資料庫",
                        "CF6": "CF6 MES資料庫",
                        "LCD6": "LCD6 MES資料庫", 
                        "USL": "USL MES資料庫"
                    }
                }
            }
        }
    
    def test_connection(self, db_source: str, db_name: str) -> Dict[str, Any]:
        """
        測試資料庫連接
        
        Args:
            db_source: 資料庫來源 ("SPC" 或 "MES")
            db_name: 資料庫名稱 ("TFT6", "CF6", "LCD6", "USL")
            
        Returns:
            Dict[str, Any]: 連接測試結果
        """
        # 生成請求ID
        request_id = generate_request_id()
        start_time = datetime.now()
        
        response = {
            "success": False,
            "message": "",
            "db_source": db_source.upper() if db_source else "",
            "db_name": db_name.upper() if db_name else "",
            "request_id": request_id,
            "timestamp": start_time.isoformat()
        }
        
        try:
            # 參數驗證
            if not db_source or db_source.upper() not in self.supported_db_types:
                error_msg = f"不支援的資料庫來源: {db_source}"
                response["message"] = error_msg
                
                api_logger.log_connection_test(
                    request_id=request_id,
                    db_source=db_source,
                    db_name=db_name,
                    success=False,
                    error=error_msg
                )
                return response
            
            if not db_name or db_name.upper() not in self.supported_db_names:
                error_msg = f"不支援的資料庫名稱: {db_name}"
                response["message"] = error_msg
                
                api_logger.log_connection_test(
                    request_id=request_id,
                    db_source=db_source,
                    db_name=db_name,
                    success=False,
                    error=error_msg
                )
                return response
            
            # 標準化參數
            db_source = db_source.upper()
            db_name = db_name.upper()
            
            # 執行簡單的測試查詢
            test_sql = "SELECT 1 FROM SYSIBM.SYSDUMMY1"
            
            self.logger.info(f"[{request_id}] 測試資料庫連接: {db_source}-{db_name}")
            
            results, columns = self.db_service.execute_select_query_odbc(
                db_name=db_name,
                sql=test_sql,
                limit=1,
                db_type=db_source
            )
            
            # 計算回應時間
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            response.update({
                "success": True,
                "message": f"資料庫連接測試成功: {db_source}-{db_name}",
                "test_result": results[0] if results else None,
                "response_time_seconds": round(response_time, 3)
            })
            
            self.logger.info(f"[{request_id}] 資料庫連接測試成功: {db_source}-{db_name}")
            
            # 記錄成功的連接測試
            api_logger.log_connection_test(
                request_id=request_id,
                db_source=db_source,
                db_name=db_name,
                success=True,
                response_time=response_time
            )
            
        except Exception as e:
            error_message = str(e)
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            response.update({
                "success": False,
                "message": f"資料庫連接測試失敗: {error_message}",
                "error": error_message,
                "response_time_seconds": round(response_time, 3)
            })
            
            self.logger.error(f"[{request_id}] 資料庫連接測試失敗 {db_source}-{db_name}: {error_message}")
            
            # 記錄失敗的連接測試
            api_logger.log_connection_test(
                request_id=request_id,
                db_source=db_source,
                db_name=db_name,
                success=False,
                response_time=response_time,
                error=error_message
            )
        
        return response


# 便捷函數，用於快速調用
def execute_query(
    sql: str, 
    db_source: str, 
    db_name: str, 
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    便捷函數：執行SQL查詢
    
    Args:
        sql: SQL查詢語句 (只允許SELECT)
        db_source: 資料庫來源 ("SPC" 或 "MES")
        db_name: 資料庫名稱 ("TFT6", "CF6", "LCD6", "USL")
        limit: 結果數量限制 (可選)
        
    Returns:
        Dict[str, Any]: JSON格式的查詢結果
    """
    api = UniversalQueryAPI()
    return api.query(sql, db_source, db_name, limit)


def execute_query_with_params(
    sql: str, 
    params: List[Any], 
    db_source: str, 
    db_name: str, 
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    便捷函數：執行帶參數的SQL查詢
    
    Args:
        sql: 包含參數佔位符(?)的SQL查詢語句
        params: 參數列表
        db_source: 資料庫來源 ("SPC" 或 "MES") 
        db_name: 資料庫名稱 ("TFT6", "CF6", "LCD6", "USL")
        limit: 結果數量限制 (可選)
        
    Returns:
        Dict[str, Any]: JSON格式的查詢結果
    """
    api = UniversalQueryAPI()
    return api.query_with_params(sql, params, db_source, db_name, limit)


def test_database_connection(db_source: str, db_name: str) -> Dict[str, Any]:
    """
    便捷函數：測試資料庫連接
    
    Args:
        db_source: 資料庫來源 ("SPC" 或 "MES")
        db_name: 資料庫名稱 ("TFT6", "CF6", "LCD6", "USL")
        
    Returns:
        Dict[str, Any]: 連接測試結果
    """
    api = UniversalQueryAPI()
    return api.test_connection(db_source, db_name)


def get_supported_databases() -> Dict[str, Any]:
    """
    便捷函數：獲取支援的資料庫清單
    
    Returns:
        Dict[str, Any]: 支援的資料庫資訊
    """
    api = UniversalQueryAPI()
    return api.get_supported_databases()


if __name__ == "__main__":
    """
    測試程式
    """
    print("=== 萬用SQL查詢API測試 ===")
    
    # 測試1: 獲取支援的資料庫
    print("\n1. 支援的資料庫:")
    db_info = get_supported_databases()
    print(json.dumps(db_info, indent=2, ensure_ascii=False))
    
    # 測試2: 測試資料庫連接
    print("\n2. 測試資料庫連接:")
    conn_result = test_database_connection("SPC", "TFT6")
    print(json.dumps(conn_result, indent=2, ensure_ascii=False))
    
    # 測試3: 簡單查詢
    print("\n3. 簡單查詢測試:")
    query_result = execute_query(
        sql="SELECT 1 as test_col FROM SYSIBM.SYSDUMMY1",
        db_source="SPC",
        db_name="TFT6",
        limit=1
    )
    print(json.dumps(query_result, indent=2, ensure_ascii=False))
