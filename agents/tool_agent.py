"""
工具代理 - 負責調用各種工具和計算功能
"""

import re
import math
from datetime import datetime
from typing import Dict, Any

class ToolAgent:
    """工具代理 - 內建工具調用"""
    
    def __init__(self):
        print("🔧 工具代理初始化完成")
    
    def use_tool(self, query: str) -> Dict[str, Any]:
        """
        根據查詢使用相應的工具
        
        Args:
            query: 用戶查詢
            
        Returns:
            工具執行結果
        """
        try:
            # 判斷查詢類型並使用相應工具
            if self._is_calculation(query):
                return self._calculate(query)
            elif "時間" in query or "日期" in query:
                return self._get_time_info(query)
            elif "長度" in query or "轉換" in query:
                return self._unit_conversion(query)
            else:
                return {
                    "answer": "抱歉，我無法理解您要使用什麼工具。",
                    "confidence": 0.0
                }
                
        except Exception as e:
            return {
                "answer": f"工具執行失敗: {str(e)}",
                "confidence": 0.0
            }
    
    def _is_calculation(self, query: str) -> bool:
        """判斷是否為計算請求"""
        calc_patterns = [
            r"\d+\s*[\+\-\*\/]\s*\d+",
            r"計算|算|加|減|乘|除",
            r"平方|開方|次方",
            r"等於|=|結果"
        ]
        
        for pattern in calc_patterns:
            if re.search(pattern, query):
                return True
        return False
    
    def _calculate(self, query: str) -> Dict[str, Any]:
        """執行數學計算"""
        try:
            # 提取數學表達式
            expression = self._extract_math_expression(query)
            
            if not expression:
                return {
                    "answer": "抱歉，我無法識別計算表達式。",
                    "confidence": 0.2
                }
            
            # 安全地評估表達式
            result = self._safe_eval(expression)
            
            if result is not None:
                return {
                    "answer": f"計算結果：{expression} = {result}",
                    "confidence": 0.9,
                    "tool": "calculator"
                }
            else:
                return {
                    "answer": "計算表達式無效或不安全。",
                    "confidence": 0.1
                }
                
        except Exception as e:
            return {
                "answer": f"計算錯誤: {str(e)}",
                "confidence": 0.1
            }
    
    def _extract_math_expression(self, query: str) -> str:
        """從查詢中提取數學表達式"""
        # 簡單的數學表達式匹配
        patterns = [
            r"(\d+(?:\.\d+)?\s*[\+\-\*\/]\s*\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*[\+\-\*\/]\s*(\d+(?:\.\d+)?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(0)
        
        return ""
    
    def _safe_eval(self, expression: str) -> float:
        """安全地評估數學表達式"""
        try:
            # 只允許安全的字符
            allowed_chars = "0123456789+-*/.() "
            if all(c in allowed_chars for c in expression):
                # 替換運算符
                expression = expression.replace("×", "*").replace("÷", "/")
                result = eval(expression)
                return round(result, 6)
        except:
            pass
        return None
    
    def _get_time_info(self, query: str) -> Dict[str, Any]:
        """獲取時間資訊"""
        now = datetime.now()
        
        if "現在幾點" in query or "目前時間" in query:
            time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
            return {
                "answer": f"現在時間是：{time_str}",
                "confidence": 1.0,
                "tool": "clock"
            }
        elif "今天日期" in query:
            date_str = now.strftime("%Y年%m月%d日")
            return {
                "answer": f"今天是：{date_str}",
                "confidence": 1.0,
                "tool": "calendar"
            }
        else:
            return {
                "answer": "請明確指定您想知道的時間資訊。",
                "confidence": 0.3
            }
    
    def _unit_conversion(self, query: str) -> Dict[str, Any]:
        """單位轉換（示例）"""
        # 這裡可以實現各種單位轉換
        return {
            "answer": "單位轉換功能正在開發中。",
            "confidence": 0.3,
            "tool": "converter"
        }
