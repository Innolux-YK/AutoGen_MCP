"""
文檔服務 - 處理文檔相關功能
"""

import os
import json
from typing import List, Dict, Any
import config

class DocumentService:
    """文檔服務 - 管理文檔資料"""
    
    def __init__(self):
        self.metadata_file = os.path.join(config.MODEL_PATH, "documents_metadata.json")
        print("📄 文檔服務初始化完成")
    
    def get_document_summary(self, documents: List[Dict]) -> Dict[str, Any]:
        """
        獲取文檔摘要資訊
        
        Args:
            documents: 文檔列表
            
        Returns:
            文檔摘要字典
        """
        try:
            if not documents:
                return {"total_docs": 0, "sources": []}
            
            # 統計文檔來源
            sources = {}
            total_chunks = len(documents)
            
            for doc in documents:
                source = doc.get("source_file", "Unknown")
                if source not in sources:
                    sources[source] = {
                        "chunks": 0,
                        "title": doc.get("title", ""),
                        "has_images": False
                    }
                
                sources[source]["chunks"] += 1
                
                # 檢查是否有圖片
                if "images" in doc and doc["images"]:
                    sources[source]["has_images"] = True
                elif "metadata" in doc and "images" in doc["metadata"]:
                    if doc["metadata"]["images"]:
                        sources[source]["has_images"] = True
            
            return {
                "total_docs": len(sources),
                "total_chunks": total_chunks,
                "sources": sources
            }
            
        except Exception as e:
            print(f"獲取文檔摘要錯誤: {e}")
            return {"total_docs": 0, "sources": [], "error": str(e)}
    
    def get_all_documents_metadata(self) -> List[Dict]:
        """獲取所有文檔的元數據"""
        try:
            if not os.path.exists(self.metadata_file):
                return []
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return metadata
            
        except Exception as e:
            print(f"讀取文檔元數據錯誤: {e}")
            return []
    
    def search_documents_by_source(self, source_file: str) -> List[Dict]:
        """
        根據來源檔案搜尋文檔
        
        Args:
            source_file: 來源檔案名
            
        Returns:
            匹配的文檔列表
        """
        try:
            all_metadata = self.get_all_documents_metadata()
            matching_docs = []
            
            for doc in all_metadata:
                if source_file.lower() in doc.get("source_file", "").lower():
                    matching_docs.append(doc)
            
            return matching_docs
            
        except Exception as e:
            print(f"搜尋文檔錯誤: {e}")
            return []
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """獲取文檔統計資訊"""
        try:
            all_metadata = self.get_all_documents_metadata()
            
            if not all_metadata:
                return {"total_documents": 0}
            
            # 統計資訊
            sources = set()
            total_images = 0
            keywords_count = {}
            
            for doc in all_metadata:
                # 統計來源
                source = doc.get("source_file", "Unknown")
                sources.add(source)
                
                # 統計圖片
                images = doc.get("images", [])
                if images:
                    total_images += len(images)
                
                # 統計關鍵字
                keywords = doc.get("keywords", [])
                for keyword in keywords:
                    keywords_count[keyword] = keywords_count.get(keyword, 0) + 1
            
            # 取前10個最常見的關鍵字
            top_keywords = sorted(keywords_count.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "total_documents": len(sources),
                "total_chunks": len(all_metadata),
                "total_images": total_images,
                "top_keywords": top_keywords,
                "sources_list": list(sources)
            }
            
        except Exception as e:
            print(f"獲取文檔統計錯誤: {e}")
            return {"error": str(e)}
    
    def format_document_for_display(self, doc: Dict) -> str:
        """
        格式化文檔用於顯示
        
        Args:
            doc: 文檔字典
            
        Returns:
            格式化後的文字
        """
        try:
            source = doc.get("source_file", "Unknown")
            title = doc.get("title", "")
            content = doc.get("content", "")
            chunk_index = doc.get("chunk_index", 0)
            
            formatted = f"📄 **來源**: {source}\n"
            
            if title:
                formatted += f"🏷️ **標題**: {title}\n"
            
            formatted += f"📍 **片段**: {chunk_index + 1}\n"
            formatted += f"📝 **內容**: {content[:200]}...\n"
            
            return formatted
            
        except Exception as e:
            return f"格式化錯誤: {str(e)}"
