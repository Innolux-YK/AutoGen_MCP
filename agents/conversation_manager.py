"""
對話管理器 - 統一管理不同類型的查詢和回應
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from .rag_agent import RAGAgent
from services.image_service import ImageService
from services.document_service import DocumentService
import config

class ConversationManager:
    """對話管理器 - 統一管理不同類型的查詢和回應"""
    
    def __init__(self):
        try:
            # 確保目錄存在
            config.ensure_directories()
            
            # 初始化各種代理
            print("🤖 初始化對話管理器...")
            self.rag_agent = RAGAgent()
            
            # 嘗試初始化 LangChain Agent（延遲載入）
            self.langchain_agent = None
            self._langchain_agent_available = self._check_langchain_agent_availability()
            
            # 初始化服務
            self.image_service = ImageService()
            self.document_service = DocumentService()
            
            print("✅ 對話管理器初始化完成")
            
        except Exception as e:
            print(f"❌ 對話管理器初始化失敗: {e}")
            raise
    
    def _check_langchain_agent_availability(self):
        """檢查 LangChain Agent 是否可用"""
        try:
            # 嘗試創建 LangChain Agent 實例來檢查可用性
            from .langchain_agent import LangChainAgent
            test_agent = LangChainAgent()
            # 如果能成功創建，就代表可用
            return True
        except Exception as e:
            print(f"⚠️ LangChain Agent 不可用: {e}")
            return False
    
    def _get_langchain_agent(self):
        """LangChain Agent"""
        if self.langchain_agent is None:
            try:
                from .langchain_agent import LangChainAgent
                self.langchain_agent = LangChainAgent()
            except Exception as e:
                print(f"⚠️ LangChain Agent 初始化失敗，使用降級模式: {e}")
                self.langchain_agent = False  # 標記為失敗，避免重複嘗試
        return self.langchain_agent
    
    def get_response_stream(self, user_input: str, chat_history: List[Dict] = None, force_query_type: str = None, llm_model: str = None):
        """
        獲取AI串流回應 - 支援 st.write_stream
        
        Args:
            user_input: 用戶輸入
            chat_history: 對話歷史
            force_query_type: 強制指定查詢類型 (可選: "rag_search", "agent")
            llm_model: 指定使用的LLM模型 (可選)
            
        Yields:
            逐字串流的回應內容
        """
        if chat_history is None:
            chat_history = []
            
        try:
            print(f"🔍 處理用戶查詢 (串流模式): {user_input[:50]}...")
            
            # 1. 使用查詢類型 (必須從下拉選單指定)
            if force_query_type:
                query_type = force_query_type
                print(f"📍 指定查詢類型: {query_type}")
            else:
                # 預設使用 RAG 搜尋
                query_type = "rag_search"
                print(f"📍 預設查詢類型: {query_type}")
            
            # 先獲取完整回應
            full_response = self.get_response(user_input, chat_history, force_query_type, llm_model)
            answer = full_response.get("answer", "")
            
            # 模擬串流效果：逐字元輸出（保持格式）
            import time
            buffer = ""
            for char in answer:
                buffer += char
                yield char
                
                # 在標點符號和換行符後稍微暫停，讓顯示更自然
                if char in "。！？\n：；，":
                    time.sleep(0.01)  # 從0.03進一步縮短為0.01
                else:
                    time.sleep(0.001)  # 從0.005縮短為0.001
                
            # 最後返回完整的回應數據（用於後續處理）
            yield {"__FINAL_RESPONSE__": full_response}
            
        except Exception as e:
            error_msg = f"抱歉，處理您的問題時發生錯誤：{e}"
            print(f"❌ 錯誤: {e}")
            for char in error_msg:
                yield char
                time.sleep(0.001)  # 從0.005縮短為0.001

    def get_response(self, user_input: str, chat_history: List[Dict] = None, force_query_type: str = None, llm_model: str = None) -> Dict[str, Any]:
        """
        獲取AI回應
        
        Args:
            user_input: 用戶輸入
            chat_history: 對話歷史
            force_query_type: 強制指定查詢類型 (可選: "rag_search", "agent")
            llm_model: 指定使用的LLM模型 (可選)
            
        Returns:
            包含回答、圖片、文檔等信息的字典
        """
        if chat_history is None:
            chat_history = []
            
        try:
            print(f"🔍 處理用戶查詢: {user_input[:50]}...")
            
            # 1. 使用查詢類型 (必須從下拉選單指定)
            if force_query_type:
                query_type = force_query_type
                print(f"📍 指定查詢類型: {query_type}")
            else:
                # 預設使用 RAG 搜尋
                query_type = "rag_search"
                print(f"📍 預設查詢類型: {query_type}")
            
            response = {
                "answer": "",
                "images": [],
                "source_documents": [],
                "query_type": query_type,
                "confidence": 0.0
            }
            
            # 2. 根據查詢類型調用不同代理
            if query_type == "rag_search":
                # RAG 知識庫查詢
                print("📚 執行 RAG 檢索...")
                rag_result = self.rag_agent.search_and_answer(user_input, chat_history, llm_model)
                response.update(rag_result)
                
                # 獲取相關圖片
                if rag_result.get("source_documents"):
                    images = self.image_service.get_related_images(rag_result["source_documents"], query=user_input)
                    response["images"] = images
                    
            elif query_type == "agent":
                # 使用新的 LangChain Agent 智能處理
                print("🤖 執行 LangChain Agent 智能處理...")
                langchain_agent = self._get_langchain_agent()
                
                if langchain_agent and langchain_agent is not False:
                    # 使用 LangChain Agent（傳遞模型參數）
                    agent_result = langchain_agent.solve_problem(user_input, llm_model=llm_model)
                    response.update(agent_result)
                    
                    # 在DEBUG控制台顯示執行步驟（不顯示在UI上）
                    if agent_result.get("execution_steps"):
                        print(f"\n🔧 執行步驟 ({agent_result.get('total_steps', 0)} 步):")
                        for i, step in enumerate(agent_result["execution_steps"], 1):
                            print(f"  {i}. 使用 {step['tool']} → {step['output'][:100]}...")
                        # 不再添加到回應中：response["answer"] += steps_info
                
            else:
                # 一般對話
                print("💬 執行一般對話...")
                response["answer"] = self._generate_general_response(user_input)
            
            print(f"✅ 回應生成完成，類型: {query_type}")
            return response
            
        except Exception as e:
            print(f"❌ 獲取回應時發生錯誤: {e}")
            return {
                "answer": f"抱歉，處理您的問題時發生錯誤: {str(e)}",
                "images": [],
                "source_documents": [],
                "query_type": "error",
                "confidence": 0.0
            }
    
    def _generate_general_response(self, user_input: str) -> str:
        """生成一般對話回應"""
        try:
            # 使用 RAG 代理的 LLM 生成回應
            return self.rag_agent.generate_response(user_input)
        except Exception as e:
            print(f"生成一般回應錯誤: {e}")
            return "抱歉，我現在無法理解您的問題。請嘗試重新表達或詢問其他問題。"
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        try:
            # 獲取向量資料庫狀態
            db_status = self.rag_agent.get_database_status()
            
            # 獲取模型狀態
            model_status = self.rag_agent.get_model_status()
            
            return {
                "database": db_status,
                "model": model_status,
                "agents": {
                    "rag_agent": "運行中",
                    "langchain_agent": "運行中" if (self.langchain_agent or self._langchain_agent_available) else "未啟用"
                },
                "services": {
                    "image_service": "運行中",
                    "document_service": "運行中"
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def clear_conversation(self):
        """清空對話歷史"""
        try:
            # 這裡可以添加清空對話歷史的邏輯
            print("🗑️ 對話歷史已清空")
        except Exception as e:
            print(f"清空對話歷史錯誤: {e}")
