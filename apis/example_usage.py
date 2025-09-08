"""
萬用SQL查詢API - 實際使用範例
展示如何在實際應用中使用這個API
"""

import json
from apis.universal_query_api import execute_query, test_database_connection, get_supported_databases


def example_basic_usage():
    """基本使用範例"""
    print("=== 基本使用範例 ===")
    
    # 1. 查看支援的資料庫
    print("\n1. 查看支援的資料庫:")
    supported_dbs = get_supported_databases()
    print(f"支援的資料庫類型: {supported_dbs['supported_db_types']}")
    print(f"支援的資料庫名稱: {supported_dbs['supported_db_names']}")
    
    # 2. 測試資料庫連接
    print("\n2. 測試資料庫連接:")
    conn_result = test_database_connection("SPC", "TFT6")
    if conn_result['success']:
        print("✅ SPC-TFT6 連接正常")
    else:
        print(f"❌ 連接失敗: {conn_result['message']}")
    
    # 3. 執行簡單查詢
    print("\n3. 執行簡單查詢:")
    result = execute_query(
        sql="SELECT CURRENT TIMESTAMP as query_time, 'Hello World' as message FROM SYSIBM.SYSDUMMY1",
        db_source="SPC",
        db_name="TFT6",
        limit=1
    )
    
    if result['success']:
        print(f"✅ 查詢成功，返回 {result['row_count']} 筆記錄")
        print(f"📊 查詢結果: {result['data'][0]}")
        print(f"⏱️ 執行時間: {result['query_info']['execution_time_seconds']} 秒")
    else:
        print(f"❌ 查詢失敗: {result['message']}")


def example_error_handling():
    """錯誤處理範例"""
    print("\n=== 錯誤處理範例 ===")
    
    # 嘗試執行非法的SQL
    print("\n1. 測試SQL安全驗證:")
    dangerous_sql = "UPDATE HAMSPARA SET PARA_VALUE = 'HACKED'"
    result = execute_query(dangerous_sql, "SPC", "TFT6")
    
    if not result['success']:
        print(f"✅ 安全驗證成功阻擋: {result['message']}")
    else:
        print("❌ 安全驗證失敗 - 這不應該發生!")
    
    # 嘗試查詢不存在的表格
    print("\n2. 測試不存在的表格:")
    result = execute_query(
        sql="SELECT * FROM NON_EXISTENT_TABLE",
        db_source="SPC", 
        db_name="TFT6",
        limit=1
    )
    
    if not result['success']:
        print(f"✅ 正確處理表格不存在錯誤: 包含 '未定義的名稱' 信息")
        print(f"📝 錯誤詳情: {result.get('error', 'N/A')[:100]}...")
    

def example_different_databases():
    """不同資料庫查詢範例"""
    print("\n=== 不同資料庫查詢範例 ===")
    
    # 測試多個資料庫
    databases = [
        ("SPC", "TFT6"),
        ("SPC", "CF6"),
        ("MES", "TFT6"),
    ]
    
    for db_source, db_name in databases:
        print(f"\n測試 {db_source}-{db_name}:")
        
        result = execute_query(
            sql="SELECT 'Database: ' || '" + f"{db_source}-{db_name}" + "' as info, CURRENT TIMESTAMP as timestamp FROM SYSIBM.SYSDUMMY1",
            db_source=db_source,
            db_name=db_name,
            limit=1
        )
        
        if result['success']:
            print(f"  ✅ 連接成功: {result['data'][0]}")
        else:
            print(f"  ❌ 連接失敗: {result['message'][:80]}...")


def example_real_world_queries():
    """實際應用查詢範例"""
    print("\n=== 實際應用查詢範例 ===")
    
    # 這些是可能在實際SPC/MES環境中使用的查詢
    real_queries = [
        {
            "name": "系統狀態檢查",
            "sql": "SELECT CURRENT TIMESTAMP as system_time, USER as current_user FROM SYSIBM.SYSDUMMY1",
            "description": "檢查系統時間和當前用戶"
        },
        {
            "name": "資料庫資訊查詢",
            "sql": "SELECT SUBSTR(CURRENT SERVER,1,20) as server_name, CURRENT TIMEZONE as timezone FROM SYSIBM.SYSDUMMY1",
            "description": "查看伺服器名稱和時區"
        }
    ]
    
    for query_info in real_queries:
        print(f"\n{query_info['name']} - {query_info['description']}")
        
        result = execute_query(
            sql=query_info['sql'],
            db_source="SPC",
            db_name="TFT6",
            limit=1
        )
        
        if result['success']:
            print(f"  ✅ 成功: {result['data'][0]}")
        else:
            print(f"  ❌ 失敗: {result['message']}")


def example_json_output():
    """JSON輸出格式範例"""
    print("\n=== JSON輸出格式範例 ===")
    
    result = execute_query(
        sql="SELECT 1 as number, 'test' as text, CURRENT TIMESTAMP as timestamp FROM SYSIBM.SYSDUMMY1",
        db_source="SPC",
        db_name="TFT6",
        limit=1
    )
    
    print("\n完整的JSON回應格式:")
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


def main():
    """主函數 - 執行所有範例"""
    print("🚀 萬用SQL查詢API - 實際使用範例")
    print("="*50)
    
    try:
        example_basic_usage()
        example_error_handling()
        example_different_databases()
        example_real_world_queries()
        example_json_output()
        
        print("\n" + "="*50)
        print("🎉 所有範例執行完成！")
        print("💡 這個API可以安全地執行SELECT查詢並返回結構化的JSON結果")
        print("📚 詳細文檔請參考 apis/README.md")
        
    except Exception as e:
        print(f"\n❌ 範例執行過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
