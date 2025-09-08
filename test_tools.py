"""
工具系統測試腳本
測試所有拆分後的工具是否正常工作
"""

import sys
import os

# 將專案根目錄加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import ToolManager

def test_all_tools():
    """測試所有工具"""
    print("🧪 開始測試工具系統...")
    
    # 初始化工具管理器
    tool_manager = ToolManager()
    
    print(f"\n📋 可用工具列表：")
    tools = tool_manager.list_tools()
    for i, tool_name in enumerate(tools, 1):
        print(f"  {i}. {tool_name}")
    
    print(f"\n🔍 工具詳細資訊：")
    tool_info = tool_manager.get_tool_info()
    for name, info in tool_info.items():
        print(f"\n**{name}**:")
        print(f"  - 類別: {info['class']}")
        print(f"  - 描述: {info['description'][:100]}...")
    
    print(f"\n🧪 測試各工具功能：")
    
    # 測試時間工具
    print("\n1. 測試時間工具：")
    result = tool_manager.execute_tool("current_time", "現在幾點？")
    print(f"   結果: {result}")
    
    # 測試計算工具
    print("\n2. 測試計算工具：")
    result = tool_manager.execute_tool("calculation", "15 + 27")
    print(f"   結果: {result}")
    
    # 測試 SPC 工具
    print("\n3. 測試 SPC 工具：")
    result = tool_manager.execute_tool("spc_query", "SPC為什麼沒有進CHART？")
    print(f"   結果: {result[:200]}...")
    
    # 測試 EDC 查詢工具
    print("\n4. 測試 EDC 查詢工具：")
    result = tool_manager.execute_tool("edc_query", "EDC 檔案上傳失敗")
    print(f"   結果: {result[:200]}...")
    
    # 測試 EDC 格式工具
    print("\n5. 測試 EDC 格式工具：")
    result = tool_manager.execute_tool("edc_format_check", "EDC檔案格式檢查")
    print(f"   結果: {result[:200]}...")
    
    print(f"\n✅ 工具系統測試完成！")

def test_langchain_integration():
    """測試 LangChain 集成"""
    print("\n🔗 測試 LangChain 工具集成...")
    
    tool_manager = ToolManager()
    langchain_tools = tool_manager.get_langchain_tools()
    
    print(f"成功轉換 {len(langchain_tools)} 個 LangChain 工具")
    
    for tool in langchain_tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")
    
    print("✅ LangChain 集成測試通過！")

if __name__ == "__main__":
    test_all_tools()
    test_langchain_integration()
