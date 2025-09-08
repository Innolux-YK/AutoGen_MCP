"""
工具基類 - 定義工具的標準介面
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """所有工具的基類"""
    
    def __init__(self):
        self.name = self.get_name()
        self.description = self.get_description()
    
    @abstractmethod
    def get_name(self) -> str:
        """返回工具名稱"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """返回工具描述（用於 LLM 工具選擇）"""
        pass
    
    @abstractmethod
    def execute(self, query: str) -> str:
        """執行工具邏輯"""
        pass
    
    def __call__(self, query: str) -> str:
        """讓工具可以像函數一樣被調用"""
        try:
            return self.execute(query)
        except Exception as e:
            return f"❌ {self.name} 執行錯誤：{str(e)}"
