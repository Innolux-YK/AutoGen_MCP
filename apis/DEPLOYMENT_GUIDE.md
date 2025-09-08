# 萬用SQL查詢API - 部署與使用指南

## 🚀 API概述

這是一個**本地化**的萬用SQL查詢API，可以安全地對SPC和MES資料庫執行SELECT查詢，並返回JSON格式結果。這個API設計為**直接調用模式**，不需要啟動Web服務器。

## 📦 安裝與配置

### 1. 環境要求

- Python 3.8+
- Windows環境 (目前配置)
- 必要的Python套件

### 2. 依賴安裝

```bash
# 安裝必要套件
pip install pyodbc
pip install logging

# 或安裝專案所有依賴
pip install -r requirements.txt
```

## 🎯 使用方式

### 方式一：直接Python調用 (推薦)

這是**最簡單的使用方式**，直接在Python程式中調用：

```python
# 導入API模組
from apis.universal_query_api import execute_query, test_database_connection

# 測試資料庫連接
conn_result = test_database_connection("SPC", "TFT6")
if conn_result['success']:
    print("✅ 資料庫連接正常")
    
    # 執行查詢
    result = execute_query(
        sql="SELECT CURRENT TIMESTAMP as query_time FROM SYSIBM.SYSDUMMY1",
        db_source="SPC",    # SPC 或 MES
        db_name="TFT6",     # TFT6, CF6, LCD6, USL
        limit=10            # 可選：限制結果數量
    )
    
    if result['success']:
        print(f"查詢成功！返回 {result['row_count']} 筆記錄")
        for row in result['data']:
            print(row)
    else:
        print(f"查詢失敗: {result['message']}")
else:
    print(f"連接失敗: {conn_result['message']}")
```

### 方式二：腳本調用

創建查詢腳本：

```python
# query_script.py
import sys
import json
from apis.universal_query_api import execute_query

def main():
    if len(sys.argv) < 4:
        print("使用方式: python query_script.py <SQL> <DB_SOURCE> <DB_NAME> [LIMIT]")
        return
    
    sql = sys.argv[1]
    db_source = sys.argv[2]
    db_name = sys.argv[3]
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    result = execute_query(sql, db_source, db_name, limit)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    main()
```

使用方式：
```bash
cd d:\Git_Code\RAG_AGENT_LLM
python query_script.py "SELECT 1 FROM SYSIBM.SYSDUMMY1" "SPC" "TFT6" 1
```

### 方式三：Web API服務 (進階)

如需要Web API服務，可以使用Flask包裝：

```python
# api_server.py
from flask import Flask, request, jsonify
from apis.universal_query_api import execute_query, test_database_connection

app = Flask(__name__)

@app.route('/api/query', methods=['POST'])
def api_query():
    data = request.json
    
    result = execute_query(
        sql=data.get('sql'),
        db_source=data.get('db_source'),
        db_name=data.get('db_name'),
        limit=data.get('limit')
    )
    
    return jsonify(result)

@app.route('/api/test', methods=['POST'])
def api_test():
    data = request.json
    
    result = test_database_connection(
        db_source=data.get('db_source'),
        db_name=data.get('db_name')
    )
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

啟動Web服務：
```bash
python api_server.py
```

使用curl測試：
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT 1 FROM SYSIBM.SYSDUMMY1", "db_source": "SPC", "db_name": "TFT6"}'
```

## 🔧 配置說明

### 1. 資料庫配置

資料庫連接配置在 `services/db2_service.py` 中：

```python
# SPC 資料庫配置
spc_db_configs = {
    "TFT6": {
        "host": "10.99.1.5",
        "port": 50501,
        "database": "T6HEDC1",
        "username": "t6hec1a1",
        "password": "hec1a1t6"
    },
    # ... 其他配置
}

# MES 資料庫配置  
mes_db_configs = {
    "TFT6": {
        "host": "10.99.1.1", 
        "port": 50101,
        "database": "T6WPPT1",
        "username": "t6wpt1a1",
        "password": "wpt1a1t6"
    },
    # ... 其他配置
}
```

### 2. 日誌配置

日誌配置在 `config.py` 中：

```python
API_LOG_CONFIG = {
    "enabled": True,                        # 啟用日誌
    "log_file": "logs/api_queries.log",    # 日誌檔案路徑
    "log_level": "INFO",                    # 日誌級別
    "max_file_size": 10 * 1024 * 1024,    # 最大檔案大小 (10MB)
    "backup_count": 5,                      # 備份檔案數量
    "log_input": True,                      # 記錄輸入
    "log_output": True,                     # 記錄輸出
}
```

## 📊 日誌查看

API會自動記錄詳細的輸入輸出日誌：

```bash
# 查看即時日誌
tail -f logs/api_queries.log

# 查看最新的查詢
grep "API_REQUEST" logs/api_queries.log | tail -5

# 查看錯誤日誌
grep "ERROR" logs/api_queries.log
```

日誌格式範例：
```json
{
  "request_id": "6c40e4e7",
  "method": "QUERY", 
  "sql": "SELECT 1 FROM SYSIBM.SYSDUMMY1",
  "db_source": "SPC",
  "db_name": "TFT6",
  "timestamp": "2025-09-02T14:30:45"
}
```

## 🔍 測試與除錯

### 1. 連接測試

```python
from apis.universal_query_api import test_database_connection

# 測試所有資料庫
databases = [
    ("SPC", "TFT6"), ("SPC", "CF6"), ("SPC", "LCD6"), ("SPC", "USL"),
    ("MES", "TFT6"), ("MES", "CF6"), ("MES", "LCD6"), ("MES", "USL"),
]

for db_source, db_name in databases:
    result = test_database_connection(db_source, db_name)
    status = "✅" if result['success'] else "❌"
    print(f"{status} {db_source}-{db_name}: {result['message']}")
```

### 2. 功能測試

```bash
# 運行完整測試
cd d:\Git_Code\RAG_AGENT_LLM
python apis\test_universal_query_api.py

# 運行使用範例
python apis\example_usage.py
```

### 3. 常見問題除錯

**問題1: 無法連接資料庫**
```
解決方案:
1. 檢查網路連接
2. 確認資料庫伺服器狀態  
3. 驗證帳號密碼
4. 檢查防火牆設定
```

**問題2: 權限不足**
```
解決方案:
1. 確認資料庫使用者權限
2. 檢查表格存取權限
3. 聯絡資料庫管理員
```

## 🛡️ 安全性

### 1. SQL安全驗證

API會自動驗證SQL語句：
- ✅ 只允許 SELECT 查詢
- ❌ 阻擋 INSERT, UPDATE, DELETE
- ❌ 阻擋 DROP, CREATE, ALTER
- ❌ 阻擋危險函數和關鍵字

### 2. 日誌安全

- 敏感資料自動遮罩
- 密碼和金鑰不會記錄
- 長資料自動截斷
- 支援日誌輪轉

## 📈 效能考量

### 1. 查詢最佳化

```python
# 好的做法
result = execute_query(
    sql="SELECT id, name FROM users WHERE status = 'active'",
    db_source="SPC",
    db_name="TFT6", 
    limit=100  # 限制結果數量
)

# 避免的做法  
result = execute_query(
    sql="SELECT * FROM large_table",  # 避免查詢大表格的所有欄位
    db_source="SPC",
    db_name="TFT6"
    # 沒有 limit 可能返回過多資料
)
```

### 2. 連接管理

API會自動管理資料庫連接：
- 自動開啟連接
- 查詢完成後自動關閉
- 支援連接池 (在db2_service中)

## 🔄 監控與維護

### 1. 日誌監控

```bash
# 設定日誌監控腳本
# monitor_api.sh
#!/bin/bash
while true; do
    echo "=== $(date) ==="
    tail -n 10 logs/api_queries.log | grep "ERROR"
    sleep 60
done
```

### 2. 效能監控

查看查詢效能統計：
```python
import json
import re

def analyze_performance():
    with open('logs/api_queries.log', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    execution_times = []
    for line in lines:
        if 'execution_time_seconds' in line:
            match = re.search(r'"execution_time_seconds": ([0-9.]+)', line)
            if match:
                execution_times.append(float(match.group(1)))
    
    if execution_times:
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        print(f"平均執行時間: {avg_time:.3f} 秒")
        print(f"最長執行時間: {max_time:.3f} 秒")
        print(f"總查詢次數: {len(execution_times)}")

analyze_performance()
```

## 📞 技術支援

如果遇到問題，請提供以下資訊：

1. **錯誤訊息**: 完整的錯誤輸出
2. **日誌檔案**: `logs/api_queries.log` 的相關片段  
3. **查詢資訊**: 使用的SQL語句和參數
4. **環境資訊**: Python版本、作業系統、網路環境

---

**🎉 現在您的萬用SQL查詢API已經準備就緒！**

開始使用最簡單的方式：
```python
from apis.universal_query_api import execute_query
result = execute_query("SELECT 1", "SPC", "TFT6")
print(result)
```
