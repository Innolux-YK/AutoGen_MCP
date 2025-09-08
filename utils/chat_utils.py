"""
聊天工具函數
"""

from typing import Dict, Any, List
import re
from datetime import datetime

def format_message(content: str, role: str = "assistant") -> str:
    """
    格式化訊息內容
    
    Args:
        content: 訊息內容
        role: 角色類型
        
    Returns:
        格式化後的訊息
    """
    # 添加時間戳記
    timestamp = datetime.now().strftime("%H:%M")
    
    if role == "user":
        return f"[{timestamp}] 👤 {content}"
    else:
        return f"[{timestamp}] 🤖 {content}"

def extract_keywords(text: str) -> List[str]:
    """從文字中提取關鍵字"""
    # 移除標點符號和特殊字符
    clean_text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    
    # 分割成詞語
    words = clean_text.split()
    
    # 過濾短詞和常見詞
    stopwords = {'的', '是', '在', '了', '有', '和', '與', '或', '但是', '然而', '因為', '所以', '這', '那', '什麼', '如何', '為什麼'}
    keywords = [word for word in words if len(word) > 1 and word not in stopwords]
    
    return list(set(keywords))[:10]  # 返回前10個去重的關鍵字

def calculate_similarity(text1: str, text2: str) -> float:
    """
    計算兩個文字的簡單相似度
    
    Args:
        text1: 文字1
        text2: 文字2
        
    Returns:
        相似度分數 (0-1)
    """
    keywords1 = set(extract_keywords(text1))
    keywords2 = set(extract_keywords(text2))
    
    if not keywords1 or not keywords2:
        return 0.0
    
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)
    
    return len(intersection) / len(union) if union else 0.0

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    截斷文字到指定長度
    
    Args:
        text: 要截斷的文字
        max_length: 最大長度
        
    Returns:
        截斷後的文字
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def format_confidence(confidence: float) -> str:
    """
    格式化信心度顯示
    
    Args:
        confidence: 信心度分數 (0-1)
        
    Returns:
        格式化的信心度字符串
    """
    if confidence >= 0.8:
        return f"🟢 高信心度 ({confidence:.1%})"
    elif confidence >= 0.5:
        return f"🟡 中等信心度 ({confidence:.1%})"
    else:
        return f"🔴 低信心度 ({confidence:.1%})"

def sanitize_filename(filename: str) -> str:
    """
    清理檔名，移除不安全字符
    
    Args:
        filename: 原始檔名
        
    Returns:
        清理後的檔名
    """
    # 移除或替換不安全字符
    unsafe_chars = r'<>:"/\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    return filename.strip()

def parse_query_intent(query: str) -> Dict[str, Any]:
    """
    分析查詢意圖
    
    Args:
        query: 用戶查詢
        
    Returns:
        意圖分析結果
    """
    query_lower = query.lower()
    
    intent = {
        "type": "general",
        "keywords": extract_keywords(query),
        "is_question": False,
        "is_calculation": False,
        "is_search": False,
        "requires_images": False
    }
    
    # 判斷是否為問題
    question_patterns = [r'什麼', r'如何', r'怎麼', r'為什麼', r'哪裡', r'誰', r'何時', r'\?']
    intent["is_question"] = any(re.search(pattern, query_lower) for pattern in question_patterns)
    
    # 判斷是否為計算
    calc_patterns = [r'\d+\s*[\+\-\*\/]\s*\d+', r'計算', r'算']
    intent["is_calculation"] = any(re.search(pattern, query_lower) for pattern in calc_patterns)
    
    # 判斷是否為搜尋
    search_patterns = [r'搜尋', r'查找', r'找', r'顯示']
    intent["is_search"] = any(re.search(pattern, query_lower) for pattern in search_patterns)
    
    # 判斷是否需要圖片
    image_patterns = [r'圖片', r'圖像', r'照片', r'截圖', r'圖']
    intent["requires_images"] = any(re.search(pattern, query_lower) for pattern in image_patterns)
    
    return intent
