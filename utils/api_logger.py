"""
API 日誌處理模組
專門處理萬用SQL查詢API的輸入輸出日誌記錄
"""

import logging
import os
import sys
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional, List
import hashlib

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import API_LOG_CONFIG


class APILogger:
    """API專用日誌記錄器"""
    
    def __init__(self, name: str = "UniversalQueryAPI"):
        self.name = name
        self.config = API_LOG_CONFIG
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """設置API日誌記錄器"""
        logger = logging.getLogger(f"API.{self.name}")
        
        # 避免重複添加handler
        if logger.handlers:
            return logger
            
        logger.setLevel(getattr(logging, self.config["log_level"]))
        
        if self.config["enabled"]:
            # 確保日誌目錄存在
            log_dir = os.path.dirname(self.config["log_file"])
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # 創建輪轉文件處理器
            file_handler = RotatingFileHandler(
                filename=self.config["log_file"],
                maxBytes=self.config["max_file_size"],
                backupCount=self.config["backup_count"],
                encoding=self.config["encoding"]
            )
            
            # 設置格式器
            formatter = logging.Formatter(
                fmt=self.config["log_format"],
                datefmt=self.config["date_format"]
            )
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
        
        return logger
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """遮罩敏感資料"""
        if not self.config["mask_sensitive_data"]:
            return data
            
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                # 遮罩可能的敏感欄位
                if any(sensitive in key.lower() for sensitive in ['password', 'pwd', 'token', 'key', 'secret']):
                    masked_data[key] = "*" * 8
                else:
                    masked_data[key] = self._mask_sensitive_data(value)
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        elif isinstance(data, str) and len(data) > self.config["max_data_length"]:
            return data[:self.config["max_data_length"]] + "...[truncated]"
        else:
            return data
    
    def _truncate_data(self, data: Any) -> Any:
        """截斷過長的資料"""
        if isinstance(data, str) and len(data) > self.config["max_data_length"]:
            return data[:self.config["max_data_length"]] + "...[truncated]"
        elif isinstance(data, list) and len(data) > 10:
            return data[:10] + ["...[truncated]"]
        elif isinstance(data, dict):
            return {k: self._truncate_data(v) for k, v in data.items()}
        else:
            return data
    
    def generate_request_id(self) -> str:
        """生成唯一的請求ID"""
        timestamp = datetime.now().isoformat()
        hash_obj = hashlib.md5(timestamp.encode())
        return hash_obj.hexdigest()[:8]
    
    def log_api_request(
        self, 
        request_id: str,
        method: str,
        sql: str,
        db_source: str,
        db_name: str,
        limit: Optional[int] = None,
        params: Optional[List[Any]] = None,
        **kwargs
    ):
        """記錄API請求"""
        if not (self.config["enabled"] and self.config["log_input"]):
            return
            
        request_data = {
            "request_id": request_id,
            "method": method,
            "sql": sql if self.config["log_sql_queries"] else "[SQL_HIDDEN]",
            "db_source": db_source,
            "db_name": db_name,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
        if params is not None:
            request_data["params"] = self._mask_sensitive_data(params)
            
        # 添加額外參數
        for key, value in kwargs.items():
            request_data[key] = self._mask_sensitive_data(value)
        
        # 截斷過長資料
        request_data = self._truncate_data(request_data)
        
        self.logger.info(f"API_REQUEST: {json.dumps(request_data, ensure_ascii=False, default=str)}")
    
    def log_api_response(
        self,
        request_id: str,
        success: bool,
        message: str,
        row_count: int = 0,
        execution_time: Optional[float] = None,
        data_sample: Optional[List[Dict]] = None,
        error: Optional[str] = None,
        **kwargs
    ):
        """記錄API回應"""
        if not (self.config["enabled"] and self.config["log_output"]):
            return
            
        response_data = {
            "request_id": request_id,
            "success": success,
            "message": message,
            "row_count": row_count,
            "timestamp": datetime.now().isoformat()
        }
        
        if execution_time is not None and self.config["log_execution_time"]:
            response_data["execution_time_seconds"] = execution_time
            
        if error:
            response_data["error"] = error
            
        # 只記錄資料樣本，不記錄完整資料
        if data_sample:
            response_data["data_sample"] = self._mask_sensitive_data(data_sample[:3])  # 只記錄前3筆
            
        # 添加額外參數
        for key, value in kwargs.items():
            response_data[key] = self._mask_sensitive_data(value)
        
        # 截斷過長資料
        response_data = self._truncate_data(response_data)
        
        log_level = "ERROR" if not success else "INFO"
        getattr(self.logger, log_level.lower())(
            f"API_RESPONSE: {json.dumps(response_data, ensure_ascii=False, default=str)}"
        )
    
    def log_api_error(
        self,
        request_id: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        **kwargs
    ):
        """記錄API錯誤"""
        if not self.config["enabled"]:
            return
            
        error_data = {
            "request_id": request_id,
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        
        if stack_trace:
            error_data["stack_trace"] = stack_trace[:2000] + "...[truncated]" if len(stack_trace) > 2000 else stack_trace
            
        # 添加額外參數
        for key, value in kwargs.items():
            error_data[key] = self._mask_sensitive_data(value)
        
        self.logger.error(f"API_ERROR: {json.dumps(error_data, ensure_ascii=False, default=str)}")
    
    def log_connection_test(
        self,
        request_id: str,
        db_source: str,
        db_name: str,
        success: bool,
        response_time: Optional[float] = None,
        error: Optional[str] = None
    ):
        """記錄資料庫連接測試"""
        if not self.config["enabled"]:
            return
            
        test_data = {
            "request_id": request_id,
            "type": "CONNECTION_TEST",
            "db_source": db_source,
            "db_name": db_name,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if response_time is not None:
            test_data["response_time_seconds"] = response_time
            
        if error:
            test_data["error"] = error
        
        log_level = "ERROR" if not success else "INFO"
        getattr(self.logger, log_level.lower())(
            f"CONNECTION_TEST: {json.dumps(test_data, ensure_ascii=False, default=str)}"
        )


# 創建全域API日誌記錄器實例
api_logger = APILogger()


# 便捷函數
def log_query_request(request_id: str, sql: str, db_source: str, db_name: str, **kwargs):
    """記錄查詢請求的便捷函數"""
    api_logger.log_api_request(request_id, "QUERY", sql, db_source, db_name, **kwargs)


def log_query_response(request_id: str, success: bool, message: str, **kwargs):
    """記錄查詢回應的便捷函數"""
    api_logger.log_api_response(request_id, success, message, **kwargs)


def log_query_error(request_id: str, error_type: str, error_message: str, **kwargs):
    """記錄查詢錯誤的便捷函數"""
    api_logger.log_api_error(request_id, error_type, error_message, **kwargs)


def generate_request_id() -> str:
    """生成請求ID的便捷函數"""
    return api_logger.generate_request_id()


if __name__ == "__main__":
    """測試API日誌功能"""
    print("=== API日誌測試 ===")
    
    # 測試請求記錄
    request_id = generate_request_id()
    print(f"生成請求ID: {request_id}")
    
    log_query_request(
        request_id=request_id,
        sql="SELECT * FROM TEST_TABLE WHERE id = ?",
        db_source="SPC",
        db_name="TFT6",
        limit=10,
        params=["test_param"]
    )
    
    # 測試回應記錄
    log_query_response(
        request_id=request_id,
        success=True,
        message="查詢成功",
        row_count=5,
        execution_time=0.123,
        data_sample=[{"id": 1, "name": "test"}]
    )
    
    # 測試錯誤記錄
    error_request_id = generate_request_id()
    log_query_error(
        request_id=error_request_id,
        error_type="ValidationError",
        error_message="SQL語句驗證失敗",
        sql="UPDATE TABLE SET value = 1"
    )
    
    print("API日誌測試完成，請檢查 logs/api_queries.log 檔案")
