"""
時間查詢工具
"""

import sys
import os
from datetime import datetime

# 將專案根目錄加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.base_tool import BaseTool

class TimeTool(BaseTool):
    """時間查詢工具"""
    
    def get_name(self) -> str:
        return "current_time"
    
    def get_description(self) -> str:
        return "獲取當前時間和日期。當用戶詢問現在幾點、今天日期、當前時間等問題時使用。"
    
    def execute(self, query: str) -> str:
        """執行時間查詢"""
        now = datetime.now()
        
        # 根據查詢內容決定返回格式
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ["日期", "今天", "date"]):
            return f"今天日期：{now.strftime('%Y年%m月%d日')} ({now.strftime('%A')})"
        elif any(keyword in query_lower for keyword in ["時間", "幾點", "time"]):
            return f"現在時間：{now.strftime('%H:%M:%S')}"
        else:
            return f"現在時間：{now.strftime('%Y年%m月%d日 %H:%M:%S')} ({now.strftime('%A')})"
