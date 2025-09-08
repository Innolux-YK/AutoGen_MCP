"""
數學計算工具
"""

import sys
import os
import re

# 將專案根目錄加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.base_tool import BaseTool

class CalculationTool(BaseTool):
    """數學計算工具"""
    
    def get_name(self) -> str:
        return "calculation"
    
    def get_description(self) -> str:
        return "執行數學計算或數據處理。支援基本四則運算（加減乘除）。當用戶提供數學表達式或計算請求時使用。"
    
    def execute(self, query: str) -> str:
        """執行數學計算"""
        try:
            # 提取數字
            numbers = re.findall(r'\d+\.?\d*', query)
            if len(numbers) >= 2:
                num1, num2 = float(numbers[0]), float(numbers[1])
                
                # 識別運算符
                if any(op in query for op in ['+', '加', '加上', '＋']):
                    result = num1 + num2
                    return f"計算結果：{self._format_number(num1)} + {self._format_number(num2)} = {self._format_number(result)}"
                
                elif any(op in query for op in ['-', '減', '減去', '－']):
                    result = num1 - num2
                    return f"計算結果：{self._format_number(num1)} - {self._format_number(num2)} = {self._format_number(result)}"
                
                elif any(op in query for op in ['*', '×', '乘', '乘以']):
                    result = num1 * num2
                    return f"計算結果：{self._format_number(num1)} × {self._format_number(num2)} = {self._format_number(result)}"
                
                elif any(op in query for op in ['/', '÷', '除', '除以']):
                    if num2 != 0:
                        result = num1 / num2
                        return f"計算結果：{self._format_number(num1)} ÷ {self._format_number(num2)} = {self._format_number(result)}"
                    else:
                        return "❌ 錯誤：除數不能為零"
                
                else:
                    return f"識別到數字：{self._format_number(num1)} 和 {self._format_number(num2)}，但無法識別運算符號"
            
            elif len(numbers) == 1:
                return f"只識別到一個數字：{numbers[0]}，請提供完整的數學表達式"
            
            else:
                return "請提供有效的數學表達式，例如：15 + 27 或 10 × 5"
                
        except Exception as e:
            return f"❌ 計算過程中發生錯誤：{str(e)}"
    
    def _format_number(self, num: float) -> str:
        """格式化數字顯示"""
        if num == int(num):
            return str(int(num))
        else:
            return str(num)
