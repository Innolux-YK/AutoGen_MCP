"""
文檔處理器 (Document Processor)

重要說明：
此檔案的功能是 RAG 系統的資料準備階段，包括：
1. 文檔解析（從 DOCX 提取文字和圖片）
2. 文字預處理（清理、分塊）
3. 向量化（使用預訓練的 embedding 模型）
4. 索引建立（存儲到向量資料庫）

這 **不是** 真正的模型訓練！
- 沒有模型參數更新
- 沒有學習過程
- 只是使用現成的 embedding 模型進行向量化

如果需要真正的訓練功能，應該考慮：
- Fine-tuning embedding 模型
- 訓練自定義檢索排序模型
- 基於使用者回饋的強化學習
"""

import os
import json
import glob
from typing import List, Dict
import chromadb
from chromadb.config import Settings
import config
from utils import (
    extract_text_from_document,  # 支援 DOC 和 DOCX 
    extract_images_from_document,  # 支援 DOC 和 DOCX 圖片提取
    chunk_text, 
    clean_text, 
    save_metadata,
    cleanup_temp_files,  # 清理臨時檔案
    auto_convert_doc_to_docx  # DOC 轉 DOCX
)
from embedding_service import get_embedding_service

class DocumentProcessor:
    """
    文檔處理器 - 負責文檔解析、向量化和索引建立
    注意：這不是模型訓練，而是 RAG 系統的資料準備階段
    """
    def __init__(self):
        # 確保目錄存在
        config.ensure_directories()
        
        # 初始化embedding服務（使用預訓練模型，非訓練）
        print("初始化embedding服務...")
        self.embedding_service = get_embedding_service()
        print(f"使用預訓練embedding模型: {self.embedding_service.get_model_info()}")
        
        # 初始化向量資料庫
        print("初始化向量資料庫...")
        self.chroma_client = chromadb.PersistentClient(
            path=config.VECTOR_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 創建或獲取collection
        try:
            self.collection = self.chroma_client.get_collection("documents")
            print("使用現有的collection")
        except:
            self.collection = self.chroma_client.create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            print("創建新的collection")
        
        self.documents_metadata = []
    
    def get_existing_files(self):
        """
        獲取已訓練的檔案列表
        """
        try:
            # 查詢所有文檔以獲取已處理的檔案
            all_results = self.collection.get()
            if all_results and all_results['metadatas']:
                existing_files = set()
                for metadata in all_results['metadatas']:
                    if 'relative_path' in metadata:
                        existing_files.add(metadata['relative_path'])
                    elif 'source_file' in metadata:
                        existing_files.add(metadata['source_file'])
                return existing_files
        except Exception as e:
            print(f"獲取已存在檔案時發生錯誤: {e}")
        return set()
    
    def convert_all_docs_to_docx(self, dataset_path: str = config.DATASET_PATH) -> None:
        """
        將 Dataset 目錄下所有 DOC 檔案轉換為 DOCX
        避免重複處理相同文檔的不同格式
        """
        print("=== 檢查並轉換 DOC 檔案 ===")
        
        # 搜尋所有 DOC 檔案
        doc_pattern = os.path.join(dataset_path, "*.doc")
        doc_files = glob.glob(doc_pattern)
        
        if not doc_files:
            print("✅ 沒有找到需要轉換的 DOC 檔案")
            return
        
        print(f"📄 找到 {len(doc_files)} 個 DOC 檔案，準備轉換為 DOCX")
        
        converted_count = 0
        
        for doc_file in doc_files:
            filename = os.path.basename(doc_file)
            print(f"🔄 轉換: {filename}")
            
            try:
                # 轉換 DOC 到 DOCX（永久轉換）
                docx_file = auto_convert_doc_to_docx(doc_file, permanent=True)
                
                if docx_file and os.path.exists(docx_file):
                    print(f"✅ 轉換成功: {os.path.basename(docx_file)}")
                    
                    # 刪除原 DOC 檔案
                    try:
                        os.remove(doc_file)
                        print(f"🗑️  已刪除原檔案: {filename}")
                        converted_count += 1
                    except Exception as e:
                        print(f"⚠️  無法刪除原檔案 {filename}: {e}")
                        converted_count += 1  # 轉換還是成功了
                else:
                    print(f"❌ 轉換失敗: {filename}")
                    
            except Exception as e:
                print(f"❌ 轉換 {filename} 時發生錯誤: {e}")
        
        if converted_count > 0:
            print(f"✅ 成功轉換並刪除了 {converted_count} 個 DOC 檔案")
        print()

    def process_docx_files(self, dataset_path: str = config.DATASET_PATH, force_reprocess: bool = False):
        """
        處理指定目錄下的所有DOCX檔案（注意：這是文檔索引建立，不是模型訓練）
        
        Args:
            dataset_path: 數據集路徑
            force_reprocess: 是否強制重新處理所有檔案
        """
        # 首先轉換所有 DOC 檔案為 DOCX
        self.convert_all_docs_to_docx(dataset_path)
        
        print("=== 文檔增量處理開始 ===")
        
        dataset_path = config.DATASET_PATH
        if not os.path.exists(dataset_path):
            print(f"Dataset目錄不存在: {dataset_path}")
            return
        
        # 獲取已處理的檔案列表
        existing_files = set() if force_reprocess else self.get_existing_files()
        print(f"已處理的檔案數量: {len(existing_files)}")
        
        # 遞迴搜尋所有DOCX檔案（DOC已經轉換為DOCX）
        docx_files = []
        new_files = []
        
        for root, dirs, files in os.walk(dataset_path):
            for file in files:
                # 只處理 .docx 檔案（DOC 已轉換）
                if file.endswith('.docx') and not file.startswith('~$'):  # 排除臨時檔案
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, dataset_path)
                    docx_files.append((file_path, relative_path))
                    
                    # 檢查是否為新檔案
                    if relative_path not in existing_files:
                        new_files.append((file_path, relative_path))
        
        print(f"總共找到 {len(docx_files)} 個 DOCX 檔案")
        print(f"需要處理的新檔案: {len(new_files)} 個")
        
        if not new_files:
            if not docx_files:
                print("Dataset目錄及子目錄中沒有找到 DOCX 檔案")
            else:
                print("所有檔案都已經處理過了，無需重新處理")
            return
        
        print("新檔案列表:")
        for file_path, relative_path in new_files:
            print(f"  - {relative_path}")
        print()
        
        all_texts = []
        all_metadatas = []
        all_ids = []
        
        # 獲取現有文檔的最大索引，避免ID衝突
        existing_doc_count = len(existing_files)
        
        for i, (file_path, relative_path) in enumerate(new_files):
            filename = os.path.basename(file_path)
            print(f"處理新檔案 ({i+1}/{len(new_files)}): {relative_path}")
            
            try:
                # 提取文字 (支援 DOC 和 DOCX)
                text_data = extract_text_from_document(file_path)
                
                if not text_data['full_text']:
                    print(f"警告: {relative_path} 沒有提取到文字內容")
                    continue
                
                # 提取圖片 (支援 DOCX 和 DOC 檔案)
                image_paths = extract_images_from_document(file_path, config.IMAGES_PATH)
                print(f"從 {relative_path} 提取了 {len(image_paths)} 張圖片")
                
                # 清理並分割文字
                cleaned_text = clean_text(text_data['full_text'])
                text_chunks = chunk_text(cleaned_text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
                
                # 為每個文字塊創建記錄，使用新的索引避免衝突
                doc_index = existing_doc_count + i
                for j, chunk in enumerate(text_chunks):
                    chunk_id = f"doc_{doc_index}_{j}"
                    
                    # ChromaDB metadata只能存儲基本類型，將list轉換為字符串
                    metadata = {
                        "source_file": filename,
                        "relative_path": relative_path,  # 添加相對路徑資訊
                        "title": text_data['title'],
                        "keywords": "|".join(text_data['keywords']) if text_data['keywords'] else "",
                        "chunk_index": j,
                        "total_chunks": len(text_chunks),
                        "images": "|".join(image_paths) if image_paths else "",
                        "file_path": file_path
                    }
                    
                    all_texts.append(chunk)
                    all_metadatas.append(metadata)
                    all_ids.append(chunk_id)
                    
                    # 保存文檔元數據
                    self.documents_metadata.append({
                        "id": chunk_id,
                        "title": text_data['title'],
                        "keywords": text_data['keywords'],
                        "content": chunk,
                        "source_file": filename,
                        "relative_path": relative_path,
                        "images": image_paths,
                        "file_path": file_path
                    })
                    
            except Exception as e:
                print(f"處理檔案 {relative_path} 時發生錯誤: {str(e)}")
                continue
        
        if all_texts:
            print(f"開始向量化 {len(all_texts)} 個新文字塊...")
            
            # 生成embeddings（使用預訓練模型）
            embeddings = self.embedding_service.encode(all_texts)
            
            # 存儲到向量資料庫
            self.collection.add(
                documents=all_texts,
                metadatas=all_metadatas,
                ids=all_ids,
                embeddings=embeddings  # 已經是list格式，不需要tolist()
            )
            
            print(f"成功處理並存儲了 {len(all_texts)} 個新文字塊")
            
            # 更新文檔元數據（追加模式）
            metadata_file = os.path.join(config.MODEL_PATH, "documents_metadata.json")
            
            # 讀取現有元數據
            existing_metadata = []
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        existing_metadata = json.load(f)
                except:
                    existing_metadata = []
            
            # 合併新舊元數據
            all_metadata = existing_metadata + self.documents_metadata
            save_metadata(all_metadata, metadata_file)
            print(f"元數據已更新至: {metadata_file}")
            
            # 清理臨時轉換檔案
            print("\n🗑️  清理臨時檔案...")
            cleanup_temp_files(config.DATASET_PATH)
            
        else:
            print("沒有找到有效的新文字內容進行處理")
    
    def search_similar_documents(self, query: str, n_results: int = 5):
        """
        搜尋相似文檔
        """
        query_embedding = self.embedding_service.encode([query])
        
        results = self.collection.query(
            query_embeddings=query_embedding,  # 已經是list格式
            n_results=n_results
        )
        
        return results
    
    def get_collection_info(self):
        """
        獲取collection資訊
        """
        count = self.collection.count()
        print(f"向量資料庫中共有 {count} 個文檔")
        return count

def main():
    """
    主函數 - 文檔處理和向量化索引建立
    注意：這不是模型訓練，而是 RAG 系統的資料準備過程
    """
    import sys
    
    # 檢查命令行參數
    force_reprocess_mode = False
    incremental_mode = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--force-retrain':  # 保持參數名稱向後兼容
            force_reprocess_mode = True
            print("=== 文檔重新處理開始 ===")
        elif sys.argv[1] == '--incremental':
            incremental_mode = True
            print("=== 文檔增量處理開始 ===")
        else:
            print("=== 文檔處理開始 ===")
    else:
        print("=== 文檔處理和向量化索引建立 ===")
    
    processor = DocumentProcessor()
    
    # 檢查現有資料
    existing_count = processor.get_collection_info()
    
    if force_reprocess_mode:
        # 強制重新處理模式（由批處理檔案調用）
        if existing_count > 0:
            print(f"清空現有的 {existing_count} 個文檔")
            # 清空現有資料
            processor.chroma_client.delete_collection("documents")
            processor.collection = processor.chroma_client.create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            print("已清空現有資料")
        print("開始完全重新處理...")
        processor.process_docx_files(force_reprocess=True)
    elif incremental_mode:
        # 增量處理模式（由批處理檔案調用）
        print(f"向量資料庫中已有 {existing_count} 個文檔")
        print("開始增量處理...")
        processor.process_docx_files(force_reprocess=False)
    elif existing_count > 0:
        print(f"\n向量資料庫中已有 {existing_count} 個文檔")
        print("選擇處理模式:")
        print("1. 增量處理 (只處理新檔案，推薦)")
        print("2. 完全重新處理 (清空所有資料重新開始)")
        print("3. 取消處理")
        
        while True:
            choice = input("請選擇 (1/2/3): ").strip()
            if choice == "1":
                print("=== 開始增量處理 ===")
                processor.process_docx_files(force_reprocess=False)
                break
            elif choice == "2":
                print("=== 開始完全重新處理 ===")
                # 清空現有資料
                processor.chroma_client.delete_collection("documents")
                processor.collection = processor.chroma_client.create_collection(
                    name="documents",
                    metadata={"hnsw:space": "cosine"}
                )
                print("已清空現有資料")
                processor.process_docx_files(force_reprocess=True)
                break
            elif choice == "3":
                print("取消處理")
                return
            else:
                print("無效選擇，請重新輸入")
    else:
        print("向量資料庫為空，開始初始處理...")
        processor.process_docx_files(force_reprocess=True)
    
    # 顯示最終統計
    final_count = processor.get_collection_info()
    
    print("\n=== 文檔處理完成 ===")
    print(f"向量資料庫中總共有 {final_count} 個文字塊")
    
    # 測試搜尋功能
    print("\n=== 測試搜尋功能 ===")
    test_query = "Windows"
    print(f"測試查詢: '{test_query}'")
    
    results = processor.search_similar_documents(test_query, 3)
    
    if results['documents']:
        print("搜尋結果:")
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            print(f"\n結果 {i+1}:")
            print(f"檔案: {metadata['source_file']}")
            print(f"標題: {metadata['title']}")
            print(f"內容預覽: {doc[:100]}...")
    else:
        print("沒有找到相關結果")
    
    print("\n" + "="*50)
    print("文檔處理和索引建立已完成！")
    print("系統已準備好回答問題")
    print("您現在可以使用 qa_app.py 來進行智能問答")
    print("="*50)

if __name__ == "__main__":
    main()
