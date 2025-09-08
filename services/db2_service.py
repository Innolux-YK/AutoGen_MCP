"""
IBM DB2 資料庫服務模組 (完整版)
提供安全的SELECT查詢功能，防止資料被意外修改或刪除
支援：SQL驗證、腳本生成、實際資料庫連接
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager

# 導入 ODBC 模組
try:
    import pyodbc
    ODBC_AVAILABLE = True
except ImportError:
    ODBC_AVAILABLE = False

class DB2Service:
    """IBM DB2資料庫服務類別 - 支援完整功能和離線模式"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
        # SPC 資料庫連接配置
        self.spc_db_configs = {
            "TFT6": {
                "host": "10.99.1.5",
                "port": 50501,
                "database": "T6HEDC1",
                "username": "t6hec1a1",
                "password": "hec1a1t6",
                "para_table": "HAMSPARA",
                "info_table": "HAMSGLSINFO",
                "odbc_string": "DRIVER={IBM DB2 ODBC DRIVER};DATABASE=T6HEDC1;HOSTNAME=10.99.1.5;PORT=50501;PROTOCOL=TCPIP;UID=t6hec1a1;PWD=hec1a1t6;"
            },
            "CF6": {
                "host": "10.99.1.6", 
                "port": 50601,
                "database": "F6HEDC1",
                "username": "f6hec1a1",
                "password": "hec1a1f6",
                "para_table": "HBMSPARA",
                "info_table": "HBMSGLSINFO",
                "odbc_string": "DRIVER={IBM DB2 ODBC DRIVER};DATABASE=F6HEDC1;HOSTNAME=10.99.1.6;PORT=50601;PROTOCOL=TCPIP;UID=f6hec1a1;PWD=hec1a1f6;"
            },
            "LCD6": {
                "host": "10.99.1.6",
                "port": 50602,
                "database": "L6HEDC1",
                "username": "l6hec1a1",
                "password": "hec1a1l6",
                "para_table": "HCMSPARA",
                "info_table": "HCMSGLSINFO",
                "odbc_string": "DRIVER={IBM DB2 ODBC DRIVER};DATABASE=L6HEDC1;HOSTNAME=10.99.1.6;PORT=50602;PROTOCOL=TCPIP;UID=l6hec1a1;PWD=hec1a1l6;"
            },
            "USL": {
                "host": "10.131.1.62",
                "port": 50203,
                "database": "U3REDC1",
                "username": "u3rec1a1",
                "password": "phoebus",
                "para_table": "HCMSPARA",
                "info_table": "HCMSGLSINFO",
                "odbc_string": "DRIVER={IBM DB2 ODBC DRIVER};DATABASE=U3REDC1;HOSTNAME=10.131.1.62;PORT=50203;PROTOCOL=TCPIP;UID=u3rec1a1;PWD=phoebus;"
            }
        }
        
        # MES 資料庫連接配置
        self.mes_db_configs = {
            "TFT6": {
                "host": "10.99.1.1",
                "port": 50101,
                "database": "T6WPPT1",
                "username": "t6wpt1a1",
                "password": "wpt1a1t6",
                "odbc_string": "DRIVER={IBM DB2 ODBC DRIVER};DATABASE=T6WPPT1;HOSTNAME=10.99.1.1;PORT=50101;PROTOCOL=TCPIP;UID=t6wpt1a1;PWD=wpt1a1t6;"
            },
            "CF6": {
                "host": "10.99.1.2",
                "port": 50201,
                "database": "F6WPPT1",
                "username": "f6wpt1a1",
                "password": "wpt1a1f6",
                "odbc_string": "DRIVER={IBM DB2 ODBC DRIVER};DATABASE=F6WPPT1;HOSTNAME=10.99.1.2;PORT=50201;PROTOCOL=TCPIP;UID=f6wpt1a1;PWD=wpt1a1f6;"
            },
            "LCD6": {
                "host": "10.99.1.3",
                "port": 50301,
                "database": "L6WPPT1",
                "username": "l6wpt1a1",
                "password": "wpt1a1l6",
                "odbc_string": "DRIVER={IBM DB2 ODBC DRIVER};DATABASE=L6WPPT1;HOSTNAME=10.99.1.3;PORT=50301;PROTOCOL=TCPIP;UID=l6wpt1a1;PWD=wpt1a1l6;"
            },
            "USL": {
                "host": "10.131.1.60",
                "port": 50001,
                "database": "U3WPPT1",
                "username": "u3wpt1a1",
                "password": "phoebus",
                "odbc_string": "DRIVER={IBM DB2 ODBC DRIVER};DATABASE=U3WPPT1;HOSTNAME=10.131.1.60;PORT=50001;PROTOCOL=TCPIP;UID=u3wpt1a1;PWD=phoebus;"
            }
        }
        
        # 預設使用SPC資料庫配置，保持向後相容性
        self.db_configs = self.spc_db_configs
    
    def _setup_logger(self) -> logging.Logger:
        """設置日志記錄器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def validate_select_query(self, sql: str) -> Tuple[bool, str]:
        """
        驗證SQL語句是否為合法的SELECT查詢
        
        Args:
            sql: 要驗證的SQL語句
            
        Returns:
            Tuple[bool, str]: (是否合法, 錯誤信息或成功信息)
        """
        if not sql or not isinstance(sql, str):
            return False, "SQL語句不能為空"
        
        # 移除註釋和多餘空白
        cleaned_sql = re.sub(r'--.*?(\n|$)', '', sql, flags=re.MULTILINE)
        cleaned_sql = re.sub(r'/\*.*?\*/', '', cleaned_sql, flags=re.DOTALL)
        cleaned_sql = cleaned_sql.strip()
        
        if not cleaned_sql:
            return False, "SQL語句在移除註釋後為空"
        
        # 檢查是否以SELECT開頭（忽略大小寫）
        if not re.match(r'^\s*SELECT\s+', cleaned_sql, re.IGNORECASE):
            return False, "只允許執行SELECT查詢語句"
        
        # 檢查是否包含危險的關鍵字
        dangerous_keywords = [
            r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b',
            r'\bCREATE\b', r'\bALTER\b', r'\bTRUNCATE\b', r'\bEXEC\b',
            r'\bEXECUTE\b', r'\bCALL\b', r'\bMERGE\b', r'\bGRANT\b',
            r'\bREVOKE\b'
        ]
        
        # 移除字符串字面值，避免誤判
        temp_sql = re.sub(r"'(?:[^'\\]|\\.)*'", '', cleaned_sql)
        temp_sql = re.sub(r'"(?:[^"\\]|\\.)*"', '', temp_sql)
        
        for keyword_pattern in dangerous_keywords:
            if re.search(keyword_pattern, temp_sql, re.IGNORECASE):
                keyword = keyword_pattern.replace(r'\b', '').replace(r'\b', '')
                return False, f"SQL語句包含被禁止的關鍵字: {keyword}"
        
        return True, "SQL語句驗證通過"
    
    def is_odbc_available(self) -> bool:
        """檢查ODBC模組是否可用"""
        return ODBC_AVAILABLE
    
    @contextmanager
    def _get_odbc_connection(self, db_name: str, db_type: str = "SPC"):
        """獲取ODBC連接"""
        if not ODBC_AVAILABLE:
            raise ImportError(
                "pyodbc 模組未安裝。請執行: pip install pyodbc"
            )
        
        # 根據資料庫類型選擇配置
        if db_type.upper() == "MES":
            configs = self.mes_db_configs
        else:
            configs = self.spc_db_configs
        
        if db_name not in configs:
            raise ValueError(f"不支援的{db_type}資料庫: {db_name}")
        
        config = configs[db_name]
        connection = None
        
        try:
            self.logger.info(f"正在透過ODBC連接到{db_type}資料庫: {db_name}")
            connection = pyodbc.connect(config["odbc_string"])
            
            if connection:
                self.logger.info(f"ODBC連接成功: {db_type}-{db_name}")
                yield connection
            else:
                raise Exception(f"ODBC連接失敗: {db_type}-{db_name}")
                
        except Exception as e:
            self.logger.error(f"ODBC連接失敗 {db_type}-{db_name}: {str(e)}")
            raise
            
        finally:
            if connection:
                try:
                    connection.close()
                    self.logger.info(f"已關閉ODBC連接: {db_type}-{db_name}")
                except Exception as e:
                    self.logger.error(f"關閉ODBC連接時發生錯誤: {str(e)}")
    
    def execute_select_query(
        self, 
        db_name: str, 
        sql: str, 
        limit: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        執行SELECT查詢 (使用ODBC)
        
        Args:
            db_name: 資料庫名稱 (TFT6, CF6, LCD6, USL)
            sql: SELECT SQL語句
            limit: 結果數量限制（可選）
            
        Returns:
            Tuple[List[Dict[str, Any]], List[str]]: (查詢結果, 欄位名稱列表)
            
        Raises:
            ValueError: 當SQL不是合法的SELECT語句時
            ImportError: 當pyodbc模組不可用時
            Exception: 資料庫連接或查詢錯誤時
        """
        return self.execute_select_query_odbc(db_name, sql, limit)
    
    def execute_select_query_odbc(
        self, 
        db_name: str, 
        sql: str, 
        limit: Optional[int] = None,
        db_type: str = "SPC"
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """執行SELECT查詢 (ODBC版本)"""
        # 驗證SQL
        is_valid, message = self.validate_select_query(sql)
        if not is_valid:
            raise ValueError(f"SQL驗證失敗: {message}")
        
        # 添加限制
        if limit and limit > 0:
            sql = f"{sql.rstrip(';')} FETCH FIRST {limit} ROWS ONLY"
        
        try:
            with self._get_odbc_connection(db_name, db_type) as connection:
                self.logger.info(f"執行{db_type} ODBC查詢: {sql}")
                
                cursor = connection.cursor()
                cursor.execute(sql)
                
                # 獲取欄位名稱
                columns = [column[0] for column in cursor.description]
                
                # 獲取結果
                results = []
                for row in cursor.fetchall():
                    row_dict = {}
                    for i, value in enumerate(row):
                        row_dict[columns[i]] = value
                    results.append(row_dict)
                
                cursor.close()
                
                self.logger.info(f"{db_type} ODBC查詢完成，返回 {len(results)} 筆記錄")
                return results, columns
                
        except Exception as e:
            self.logger.error(f"{db_type} ODBC查詢執行失敗: {str(e)}")
            raise
    
    def execute_select_query_with_params(
        self, 
        db_name: str, 
        sql: str, 
        params: List[Any], 
        limit: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        執行帶參數的SELECT查詢 (使用ODBC)
        
        Args:
            db_name: 資料庫名稱
            sql: 包含參數佔位符(?)的SELECT SQL語句
            params: 參數列表
            limit: 結果數量限制（可選）
            
        Returns:
            Tuple[List[Dict[str, Any]], List[str]]: (查詢結果, 欄位名稱列表)
        """
        # 驗證SQL語句
        is_valid, message = self.validate_select_query(sql)
        if not is_valid:
            raise ValueError(f"SQL驗證失敗: {message}")
        
        # 添加限制
        if limit and limit > 0:
            sql = f"{sql.rstrip(';')} FETCH FIRST {limit} ROWS ONLY"
        
        try:
            with self._get_odbc_connection(db_name) as connection:
                self.logger.info(f"執行ODBC參數化查詢: {sql}")
                self.logger.info(f"參數: {params}")
                
                cursor = connection.cursor()
                cursor.execute(sql, params)
                
                # 獲取欄位名稱
                columns = [column[0] for column in cursor.description]
                
                # 獲取結果
                results = []
                for row in cursor.fetchall():
                    row_dict = {}
                    for i, value in enumerate(row):
                        row_dict[columns[i]] = value
                    results.append(row_dict)
                
                cursor.close()
                
                self.logger.info(f"ODBC參數化查詢完成，返回 {len(results)} 筆記錄")
                return results, columns
                
        except Exception as e:
            self.logger.error(f"ODBC參數化查詢執行失敗: {str(e)}")
            raise
    
    def execute_select_smart(
        self, 
        db_name: str, 
        sql: str, 
        limit: Optional[int] = None,
        prefer_odbc: bool = True
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        智慧執行SELECT查詢 - 使用ODBC連接
        
        Args:
            db_name: 資料庫名稱
            sql: SQL查詢語句
            limit: 結果數量限制
            prefer_odbc: 保留參數以向後相容 (現在總是使用ODBC)
            
        Returns:
            Tuple[List[Dict[str, Any]], List[str]]: (查詢結果, 欄位名稱列表)
        """
        # 驗證SQL
        is_valid, message = self.validate_select_query(sql)
        if not is_valid:
            raise ValueError(f"SQL驗證失敗: {message}")
        
        # 使用ODBC連接
        if ODBC_AVAILABLE:
            self.logger.info("使用ODBC連接執行查詢")
            return self.execute_select_query_odbc(db_name, sql, limit)
        else:
            raise ImportError(
                "沒有可用的資料庫連接模組。請安裝：\n"
                "pip install pyodbc"
            )
    
    def execute_spc_query(
        self, 
        db_name: str, 
        sql: str, 
        limit: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        執行SPC資料庫查詢
        
        Args:
            db_name: 資料庫名稱 (TFT6, CF6, LCD6, USL)
            sql: SELECT SQL語句
            limit: 結果數量限制（可選）
            
        Returns:
            Tuple[List[Dict[str, Any]], List[str]]: (查詢結果, 欄位名稱列表)
        """
        return self.execute_select_query_odbc(db_name, sql, limit, "SPC")
    
    def execute_mes_query(
        self, 
        db_name: str, 
        sql: str, 
        limit: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        執行MES資料庫查詢
        
        Args:
            db_name: 資料庫名稱 (TFT6, CF6, LCD6, USL)
            sql: SELECT SQL語句
            limit: 結果數量限制（可選）
            
        Returns:
            Tuple[List[Dict[str, Any]], List[str]]: (查詢結果, 欄位名稱列表)
        """
        return self.execute_select_query_odbc(db_name, sql, limit, "MES")
    
    def test_connection(self, db_name: str, prefer_odbc: bool = True, db_type: str = "SPC") -> bool:
        """
        測試資料庫連接 - 使用ODBC
        
        Args:
            db_name: 資料庫名稱
            prefer_odbc: 保留參數以向後相容 (現在總是使用ODBC)
            db_type: 資料庫類型 ("SPC" 或 "MES")
            
        Returns:
            bool: 連接成功返回True，失敗返回False
        """
        # 嘗試ODBC連接
        if ODBC_AVAILABLE:
            try:
                with self._get_odbc_connection(db_name, db_type):
                    self.logger.info(f"資料庫 {db_type}-{db_name} ODBC連接測試成功")
                    return True
            except Exception as e:
                self.logger.warning(f"{db_type} ODBC連接測試失敗: {str(e)}")
        
        self.logger.error(f"資料庫 {db_type}-{db_name} 連接失敗 - ODBC不可用或連接錯誤")
        return False
    
    def test_spc_connection(self, db_name: str) -> bool:
        """測試SPC資料庫連接"""
        return self.test_connection(db_name, True, "SPC")
    
    def test_mes_connection(self, db_name: str) -> bool:
        """測試MES資料庫連接"""
        return self.test_connection(db_name, True, "MES")
    
    def get_table_info(self, db_name: str, table_name: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        獲取表格結構資訊
        
        Args:
            db_name: 資料庫名稱
            table_name: 表格名稱
            
        Returns:
            Tuple[List[Dict[str, Any]], List[str]]: (表格結構資訊, 欄位名稱列表)
        """
        sql = """
        SELECT 
            COLNAME as COLUMN_NAME,
            TYPENAME as DATA_TYPE,
            LENGTH as COLUMN_SIZE,
            SCALE as DECIMAL_DIGITS,
            NULLS as IS_NULLABLE,
            DEFAULT as COLUMN_DEFAULT,
            KEYSEQ as KEY_SEQ
        FROM SYSCAT.COLUMNS 
        WHERE TABNAME = UPPER(?)
        ORDER BY COLNO
        """
        
        return self.execute_select_query_with_params(
            db_name, 
            sql, 
            [table_name.upper()]
        )
    
    def format_sql_for_db2(self, sql: str, limit: Optional[int] = None) -> str:
        """
        為DB2格式化SQL語句
        
        Args:
            sql: 原始SQL語句
            limit: 結果數量限制
            
        Returns:
            str: 格式化後的SQL語句
        """
        formatted_sql = sql.strip().rstrip(';')
        
        if limit and limit > 0:
            formatted_sql = f"{formatted_sql} FETCH FIRST {limit} ROWS ONLY"
        
        return formatted_sql
    
    def generate_connection_script(self, db_name: str, sql: str, limit: Optional[int] = None) -> str:
        """
        生成可執行的ODBC連接腳本
        
        Args:
            db_name: 資料庫名稱
            sql: SQL語句
            limit: 結果限制
            
        Returns:
            str: Python腳本代碼
        """
        if db_name not in self.db_configs:
            raise ValueError(f"不支援的資料庫: {db_name}")
        
        is_valid, message = self.validate_select_query(sql)
        if not is_valid:
            raise ValueError(f"SQL驗證失敗: {message}")
        
        config = self.db_configs[db_name]
        
        # 添加限制
        formatted_sql = sql.strip().rstrip(';')
        if limit and limit > 0:
            formatted_sql = f"{formatted_sql} FETCH FIRST {limit} ROWS ONLY"
        
        script = f'''"""
自動生成的DB2 ODBC查詢腳本
資料庫: {db_name}
"""

import pyodbc

# 資料庫ODBC連接字串
ODBC_STRING = "{config['odbc_string']}"

# SQL查詢
SQL = """{formatted_sql}"""

def execute_query():
    """執行查詢"""
    connection = None
    try:
        print("正在透過ODBC連接到資料庫 {db_name}...")
        connection = pyodbc.connect(ODBC_STRING)
        
        if not connection:
            raise Exception("ODBC連接失敗")
        
        print("ODBC連接成功，執行查詢...")
        print(f"SQL: {{SQL}}")
        
        # 執行查詢
        cursor = connection.cursor()
        cursor.execute(SQL)
        
        # 獲取欄位名稱
        columns = [column[0] for column in cursor.description]
        print(f"查詢欄位: {{columns}}")
        print("\\n查詢結果:")
        print("-" * 80)
        
        # 獲取和顯示結果
        row_count = 0
        for row in cursor.fetchall():
            row_count += 1
            print(f"記錄 {{row_count}}:")
            for i, value in enumerate(row):
                print(f"  {{columns[i]}}: {{value}}")
            print()
        
        cursor.close()
        print(f"總共返回 {{row_count}} 筆記錄")
        
    except Exception as e:
        print(f"錯誤: {{str(e)}}")
        
    finally:
        if connection:
            try:
                connection.close()
                print("ODBC連接已關閉")
            except:
                pass

if __name__ == "__main__":
    execute_query()
'''
        return script
    
    def get_available_databases(self) -> List[str]:
        """獲取可用的資料庫列表"""
        return list(self.db_configs.keys())
    
    def get_database_info(self, db_name: str) -> Dict[str, Any]:
        """獲取指定資料庫的配置資訊"""
        if db_name not in self.db_configs:
            raise ValueError(f"不支援的資料庫: {db_name}")
        
        config = self.db_configs[db_name].copy()
        # 隱藏密碼
        config['password'] = '***'
        config['odbc_string'] = re.sub(r'PWD=[^;]+', 'PWD=***', config['odbc_string'])
        
        return config
    
    def generate_test_queries(self, db_name: str) -> List[str]:
        """生成測試查詢語句"""
        if db_name not in self.db_configs:
            raise ValueError(f"不支援的資料庫: {db_name}")
        
        config = self.db_configs[db_name]
        
        queries = [
            f"SELECT COUNT(*) as TOTAL_RECORDS FROM {config['para_table']}",
            f"SELECT * FROM {config['para_table']} FETCH FIRST 5 ROWS ONLY",
            f"SELECT COUNT(*) as TOTAL_RECORDS FROM {config['info_table']}",
            f"SELECT * FROM {config['info_table']} FETCH FIRST 5 ROWS ONLY",
            "SELECT CURRENT TIMESTAMP as CURRENT_TIME FROM SYSIBM.SYSDUMMY1",
            "SELECT CURRENT USER as CURRENT_USER FROM SYSIBM.SYSDUMMY1"
        ]
        
        return queries


# 便利函數
def validate_sql(sql: str) -> Tuple[bool, str]:
    """驗證SQL語句"""
    service = DB2Service()
    return service.validate_select_query(sql)

def generate_script(db_name: str, sql: str, limit: Optional[int] = None) -> str:
    """生成執行腳本"""
    service = DB2Service()
    return service.generate_connection_script(db_name, sql, limit)

def get_test_queries(db_name: str) -> List[str]:
    """獲取測試查詢"""
    service = DB2Service()
    return service.generate_test_queries(db_name)

# 新增的便利函數，提供與原始完整版本相同的接口
def execute_select(db_name: str, sql: str, limit: Optional[int] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    執行SELECT查詢的便利函數
    
    Args:
        db_name: 資料庫名稱
        sql: SELECT SQL語句
        limit: 結果數量限制
        
    Returns:
        Tuple[List[Dict[str, Any]], List[str]]: (查詢結果, 欄位名稱列表)
    """
    service = DB2Service()
    return service.execute_select_query(db_name, sql, limit)

def execute_select_with_params(
    db_name: str, 
    sql: str, 
    params: List[Any], 
    limit: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    執行帶參數的SELECT查詢的便利函數
    
    Args:
        db_name: 資料庫名稱
        sql: 包含參數佔位符的SELECT SQL語句
        params: 參數列表
        limit: 結果數量限制
        
    Returns:
        Tuple[List[Dict[str, Any]], List[str]]: (查詢結果, 欄位名稱列表)
    """
    service = DB2Service()
    return service.execute_select_query_with_params(db_name, sql, params, limit)

def get_db2_service() -> DB2Service:
    """獲取DB2服務實例"""
    return DB2Service()

def test_db_connection(db_name: str, prefer_odbc: bool = True) -> bool:
    """測試資料庫連接"""
    service = DB2Service()
    return service.test_connection(db_name, prefer_odbc)

def execute_select_smart(db_name: str, sql: str, limit: Optional[int] = None, prefer_odbc: bool = True) -> Tuple[List[Dict[str, Any]], List[str]]:
    """智慧執行SELECT查詢"""
    service = DB2Service()
    return service.execute_select_smart(db_name, sql, limit, prefer_odbc)

def execute_select_odbc(db_name: str, sql: str, limit: Optional[int] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
    """使用ODBC執行SELECT查詢"""
    service = DB2Service()
    return service.execute_select_query_odbc(db_name, sql, limit)
