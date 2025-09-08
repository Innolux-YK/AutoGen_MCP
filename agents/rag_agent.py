"""
RAG 代理 - 負責知識庫檢索和回答生成
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
import config
from embedding_service import get_embedding_service
from services.llm_service import LLMService

class RAGAgent:
    """RAG 代理 - 知識庫檢索和回答生成"""
    
    def __init__(self):
        try:
            # 初始化向量資料庫
            print("📚 初始化 RAG 代理...")
            self.chroma_client = chromadb.PersistentClient(
                path=config.VECTOR_DB_PATH,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # 獲取 collection
            try:
                self.collection = self.chroma_client.get_collection("documents")
                print(f"✅ 連接到現有 collection，文檔數量: {self.collection.count()}")
            except:
                print("⚠️  未找到現有 collection，請先執行 document_processor.py")
                self.collection = None
            
            # 初始化 embedding 服務
            self.embedding_service = get_embedding_service()
            
            # 初始化 LLM 服務
            self.llm_service = LLMService()
            
            print("✅ RAG 代理初始化完成")
            
        except Exception as e:
            print(f"❌ RAG 代理初始化失敗: {e}")
            raise
    
    def search_and_answer(self, query: str, chat_history: List[Dict] = None, llm_model: str = None) -> Dict[str, Any]:
        """
        搜尋知識庫並生成回答
        
        Args:
            query: 用戶查詢
            chat_history: 對話歷史
            llm_model: 指定使用的LLM模型
            
        Returns:
            包含回答和相關文檔的字典
        """
        if not self.collection:
            return {
                "answer": "抱歉，知識庫尚未建立。請先執行文檔處理程序。",
                "source_documents": [],
                "confidence": 0.0
            }
        
        try:
            # 1. 向量檢索
            print(f"🔍 搜尋相關文檔: {query[:50]}...")
            search_results = self._search_documents(query, n_results=5)
            
            if not search_results["documents"] or not search_results["documents"][0]:
                return {
                    "answer": "抱歉，我在知識庫中沒有找到相關資訊。請嘗試其他問題或確認問題表達。",
                    "source_documents": [],
                    "confidence": 0.0
                }
            
            # 2. 組織檢索結果並加入相似度過濾
            relevant_docs = []
            for i, (doc, metadata, distance) in enumerate(zip(
                search_results["documents"][0],
                search_results["metadatas"][0],
                search_results["distances"][0] if "distances" in search_results else [0] * len(search_results["documents"][0])
            )):
                # 檢查相似度門檻
                if distance > config.SIMILARITY_THRESHOLD:
                    print(f"📄 過濾文檔：距離 {distance:.3f} > 門檻 {config.SIMILARITY_THRESHOLD}")
                    continue
                    
                relevant_docs.append({
                    "content": doc,
                    "metadata": metadata,
                    "distance": distance,
                    "source_file": metadata.get("source_file", "Unknown"),
                    "title": metadata.get("title", ""),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "images": metadata.get("images", "").split("|") if metadata.get("images") else []
                })
            
            # 按相似度排序（距離越小越前面）
            relevant_docs.sort(key=lambda x: x.get("distance", float('inf')))
            print(f"📄 過濾後文檔數量：{len(relevant_docs)}（門檻: {config.SIMILARITY_THRESHOLD}）")
            
            # 3. 生成回答
            answer = self._generate_answer(query, relevant_docs, chat_history, llm_model)
            
            # 4. 計算信心度
            confidence = self._calculate_confidence(search_results, relevant_docs)
            
            return {
                "answer": answer,
                "source_documents": relevant_docs,
                "confidence": confidence
            }
            
        except Exception as e:
            error_str = str(e)
            print(f"❌ RAG 搜尋錯誤: {error_str}")
            
            # 直接顯示原始錯誤原因，讓用戶了解具體問題
            return {
                "answer": f"❌ RAG 系統錯誤：{error_str}",
                "source_documents": [],
                "confidence": 0.0
            }
    
    def _search_documents(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """搜尋相關文檔"""
        try:
            # 生成查詢向量
            query_embedding = self.embedding_service.encode([query])
            
            # 執行向量搜尋
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            return results
            
        except Exception as e:
            error_str = str(e)
            print(f"文檔搜尋錯誤: {error_str}")
            
            # 直接向上拋出錯誤，讓上層處理
            raise
    
    def _generate_answer(self, query: str, relevant_docs: List[Dict], chat_history: List[Dict] = None, llm_model: str = None) -> str:
        """使用檢索到的文檔生成回答"""
        try:
            # 構建上下文
            context = self._build_context(relevant_docs)
            
            # 構建提示詞
            prompt = self._build_prompt(query, context, chat_history)
            
            # 生成回答（使用指定的模型）
            answer = self.llm_service.generate_response(prompt, model=llm_model)
            
            # 添加模型名稱前綴
            used_model = llm_model or config.INNOAI_DEFAULT_MODEL
            model_prefix = f"**{used_model.upper()}**: "
            final_answer = model_prefix + answer
            
            return final_answer
            
        except Exception as e:
            print(f"回答生成錯誤: {e}")
            return "抱歉，生成回答時發生錯誤。"
    
    def _build_context(self, relevant_docs: List[Dict]) -> str:
        """構建上下文資訊"""
        context_parts = []
        
        for i, doc in enumerate(relevant_docs[:3]):  # 只使用前3個最相關的文檔
            source = doc.get("source_file", "Unknown")
            title = doc.get("title", "")
            content = doc.get("content", "")
            
            context_part = f"文檔 {i+1}:\n"
            context_part += f"來源: {source}\n"
            if title:
                context_part += f"標題: {title}\n"
            context_part += f"內容: {content}\n"
            
            context_parts.append(context_part)
        
        return "\n" + "="*50 + "\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str, chat_history: List[Dict] = None) -> str:
        """構建 LLM 提示詞"""
        prompt = f"""你是一個專業的技術文檔助手。請根據提供的文檔內容回答用戶的問題。

規則：
1. 只使用提供的文檔內容來回答問題
2. 如果文檔中沒有相關資訊，請明確說明
3. 回答要準確、簡潔且有幫助
4. 如果有多個相關資訊，請整理後提供
5. 可以引用具體的文檔來源

相關文檔內容：
{context}

用戶問題：{query}

請提供詳細且准確的回答："""

        # 如果有對話歷史，添加上下文
        if chat_history and len(chat_history) > 0:
            history_context = "\n對話歷史：\n"
            for msg in chat_history[-3:]:  # 只使用最近3條對話
                role = "用戶" if msg["role"] == "user" else "助手"
                history_context += f"{role}: {msg['content']}\n"
            
            prompt = prompt.replace("用戶問題：", history_context + "\n用戶問題：")
        
        return prompt
    
    def _calculate_confidence(self, search_results: Dict, relevant_docs: List[Dict]) -> float:
        """計算回答的信心度"""
        try:
            if not search_results.get("distances") or not search_results["distances"][0]:
                return 0.5  # 默認信心度
            
            # 基於相似度距離計算信心度
            distances = search_results["distances"][0]
            
            if not distances:
                return 0.5
            
            # 距離越小，信心度越高
            avg_distance = sum(distances) / len(distances)
            confidence = max(0.0, min(1.0, 1.0 - avg_distance))
            
            return confidence
            
        except Exception as e:
            print(f"信心度計算錯誤: {e}")
            return 0.5
    
    def generate_response(self, query: str) -> str:
        """生成一般回應（不使用 RAG）"""
        try:
            prompt = f"""你是一個友善的AI助手。請回答用戶的問題：

{query}

請提供有幫助的回答："""
            
            return self.llm_service.generate_response(prompt)
            
        except Exception as e:
            print(f"一般回應生成錯誤: {e}")
            return "抱歉，我現在無法處理您的問題。"
    
    def get_database_status(self) -> Dict[str, Any]:
        """獲取資料庫狀態"""
        try:
            if not self.collection:
                return {"status": "未連接", "count": 0}
            
            count = self.collection.count()
            return {
                "status": "正常",
                "count": count,
                "collection_name": "documents"
            }
        except Exception as e:
            return {"status": "錯誤", "error": str(e)}
    
    def get_model_status(self) -> Dict[str, Any]:
        """獲取模型狀態"""
        try:
            embedding_info = self.embedding_service.get_model_info()
            llm_info = self.llm_service.get_model_info()
            
            return {
                "embedding_model": embedding_info,
                "llm_model": llm_info,
                "status": "正常"
            }
        except Exception as e:
            return {"status": "錯誤", "error": str(e)}
