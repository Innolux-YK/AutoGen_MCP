"""
LLM 服務 - 大語言模型調用服務
"""

import os
import requests
import json
from typing import Dict, Any, Optional
import config

class LLMService:
    """大語言模型服務"""
    
    def __init__(self):
        self.api_key = config.API_KEY
        self.model_name = config.INNOAI_DEFAULT_MODEL
        self.api_url = config.get_api_url(self.model_name)
        self.temperature = config.LLM_TEMPERATURE
        self.max_tokens = config.LLM_MAX_TOKENS
        
        print(f"✅ LLM 服務初始化完成，使用模型: {self.model_name}")
    
    def generate_response(self, prompt: str, model: str = None, **kwargs) -> str:
        """
        生成回應
        
        Args:
            prompt: 輸入提示詞
            model: 指定使用的模型（可選）
            **kwargs: 其他參數
            
        Returns:
            生成的回應文字
        """
        # 使用指定的模型或默認模型
        target_model = model or self.model_name
        
        # 首先嘗試使用 API
        api_response = self._try_api_request(prompt, model=target_model, **kwargs)
        if api_response:
            return api_response
        
        # 如果 API 失敗，返回預設回應
        return self._generate_fallback_response(prompt)
    
    def _try_api_request(self, prompt: str, model: str = None, **kwargs) -> str:
        """嘗試 API 請求"""
        try:
            # 使用指定的模型或默認模型
            target_model = model or self.model_name
            target_api_url = config.get_api_url(target_model)
            
            # 構建請求參數
            payload = {
                "model": target_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens)
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 嘗試不同的 API 端點
            api_endpoints = [
                f"{target_api_url}/chat/completions",
                f"{target_api_url}/v1/completions"
            ]
            
            for endpoint in api_endpoints:
                try:
                    print(f"🔗 嘗試 API 端點: {endpoint} (模型: {target_model})")
                    response = requests.post(
                        endpoint,
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "choices" in result and len(result["choices"]) > 0:
                            content = result["choices"][0]["message"]["content"].strip()
                            print(f"✅ API 請求成功")
                            return content
                    else:
                        print(f"⚠️ API 端點 {endpoint} 失敗: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"⚠️ 連接 {endpoint} 失敗: {e}")
                    continue
            
            return None
                
        except Exception as e:
            print(f"❌ API 請求過程發生錯誤: {e}")
            return None
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """生成備用回應"""
        # 簡單的關鍵字回應邏輯
        prompt_lower = prompt.lower()
        
        if "edc" in prompt_lower:
            return """EDC (Electronic Data Capture) 是電子資料擷取系統，主要用於：
1. 收集和管理臨床試驗數據
2. 確保數據品質和完整性
3. 符合法規要求
4. 提供即時數據監控
5. 支援數據分析和報告生成

請查閱相關文檔以獲取更詳細的資訊。"""
        
        elif "spc" in prompt_lower:
            return """SPC (Statistical Process Control) 是統計製程控制，主要功能包括：
1. 監控製程穩定性
2. 檢測製程異常
3. 控制圖分析
4. 品質控制
5. 持續改善支援

請參考相關技術文檔以了解具體操作方法。"""
        
        elif "計算" in prompt_lower or "算" in prompt_lower:
            return "抱歉，目前 AI 服務暫時不可用，計算功能已轉交給工具代理處理。請嘗試使用簡單的計算表達式，如：15 + 27"
        
        elif "時間" in prompt_lower or "日期" in prompt_lower:
            from datetime import datetime
            now = datetime.now()
            return f"當前時間：{now.strftime('%Y年%m月%d日 %H:%M:%S')}"
        
        else:
            return """抱歉，AI 模型服務暫時不可用。可能的原因：
1. API 服務暫時中斷
2. 網路連接問題
3. API 金鑰或配置有誤

請檢查：
- 網路連接狀態
- config.py 中的 API 設定
- API 金鑰是否有效

或稍後再試。"""
    
    def chat_completion(self, messages: list, **kwargs) -> Dict[str, Any]:
        """
        多輪對話完成
        
        Args:
            messages: 對話消息列表
            **kwargs: 其他參數
            
        Returns:
            完整的 API 回應
        """
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens)
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"API 錯誤: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_model_info(self) -> str:
        """獲取模型資訊"""
        return f"{self.model_name} (API: {self.api_url})"
    
    def set_model(self, model_name: str):
        """設置模型"""
        if model_name in config.get_available_models():
            self.model_name = model_name
            self.api_url = config.get_api_url(model_name)
            print(f"模型已切換為: {model_name}")
        else:
            print(f"不支援的模型: {model_name}")
    
    def test_connection(self) -> bool:
        """測試連接"""
        try:
            response = self._try_api_request("測試連接")
            return response is not None and len(response) > 0 and "錯誤" not in response
        except:
            return False
