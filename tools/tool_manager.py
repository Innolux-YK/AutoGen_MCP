"""
工具管理器 - 集中管理所有工具的載入和配置
"""

import sys
import os
from typing import List, Dict, Any
from langchain_core.tools import tool, StructuredTool
from pydantic import BaseModel, Field

# 將專案根目錄加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入所有工具
from tools.time_tool import TimeTool
from tools.calculation_tool import CalculationTool
from tools.spc_tool import SPCTool
from tools.edc_query_tool import EDCQueryTool
from tools.edc_format_tool import EDCFormatTool
from tools.ip_edc_config_tool import IPEDCConfigTool
from tools.spc_detail_viewer_tool import SPCDetailViewerTool

class ToolInput(BaseModel):
    query: str = Field(description="用戶的查詢內容")

class ToolManager:
    """工具管理器 - 負責載入和管理所有工具"""
    
    def __init__(self):
        """初始化工具管理器"""
        self.tools = self._load_all_tools()
        print(f"🔧 工具管理器已載入 {len(self.tools)} 個工具")
    
    def _load_all_tools(self) -> Dict[str, Any]:
        """載入所有工具實例"""
        tools = {}
        
        # 創建工具實例
        time_tool = TimeTool()
        calculation_tool = CalculationTool()
        spc_tool = SPCTool()
        edc_query_tool = EDCQueryTool()
        edc_format_tool = EDCFormatTool()
        ip_edc_config_tool = IPEDCConfigTool()
        spc_detail_viewer_tool = SPCDetailViewerTool()
        
        # 註冊工具
        tools[time_tool.get_name()] = time_tool
        tools[calculation_tool.get_name()] = calculation_tool
        tools[spc_tool.get_name()] = spc_tool
        tools[edc_query_tool.get_name()] = edc_query_tool
        tools[edc_format_tool.get_name()] = edc_format_tool
        tools[ip_edc_config_tool.get_name()] = ip_edc_config_tool
        tools[spc_detail_viewer_tool.get_name()] = spc_detail_viewer_tool
        
        return tools
    
    def get_langchain_tools(self) -> List:
        """轉換為 LangChain 工具格式"""
        langchain_tools = []
        
        for tool_name, tool_instance in self.tools.items():
            # 創建一個包裝函數來確保完整輸出
            def create_tool_wrapper(tool_inst):
                def wrapper(query: str) -> str:
                    result = tool_inst.execute(query)
                    # 確保回傳完整結果，不截斷
                    return str(result)
                return wrapper
            
            # 使用 StructuredTool 創建 LangChain 工具
            langchain_tool = StructuredTool(
                name=tool_instance.get_name(),
                description=tool_instance.get_description(),
                args_schema=ToolInput,
                func=create_tool_wrapper(tool_instance),
                return_direct=False  # 確保不直接返回，讓 Agent 可以進一步處理
            )
            langchain_tools.append(langchain_tool)
        
        return langchain_tools
    
    def get_tool_info(self) -> Dict[str, Dict[str, str]]:
        """獲取所有工具的資訊"""
        tool_info = {}
        
        for tool_name, tool_instance in self.tools.items():
            tool_info[tool_name] = {
                "name": tool_instance.get_name(),
                "description": tool_instance.get_description(),
                "class": tool_instance.__class__.__name__
            }
        
        return tool_info
    
    def execute_tool(self, tool_name: str, query: str) -> str:
        """直接執行指定工具"""
        if tool_name in self.tools:
            return self.tools[tool_name].execute(query)
        else:
            return f"❌ 找不到工具: {tool_name}"
    
    def list_tools(self) -> List[str]:
        """列出所有可用工具"""
        return list(self.tools.keys())
