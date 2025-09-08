"""
圖片服務 - 處理與圖片相關的功能
"""

import os
from typing import List, Dict, Any
from PIL import Image
import config

class ImageService:
    """圖片服務 - 管理和處理圖片"""
    
    def __init__(self):
        self.images_path = config.IMAGES_PATH
        os.makedirs(self.images_path, exist_ok=True)
        print("🖼️ 圖片服務初始化完成")
    
    def get_related_images(self, documents: List[Dict], query: str = "") -> List[str]:
        """
        根據文檔獲取相關圖片，並依相似度門檻過濾並排序。

        Args:
            documents: 文檔列表（包含 metadata/images 與 distance）
            query: 使用者查詢字串（可選）

        Returns:
            圖片路徑列表（按相似度由高到低排序）
        """
        image_paths_with_score: List[tuple] = []  # (path, distance)

        # 解析主題關鍵詞
        query_upper = (query or "").upper()
        domain_keywords = {"EDC", "SPC", "OOC", "OOS", "CHART", "AFF"}
        present_keywords = {k for k in domain_keywords if k in query_upper}

        # 距離門檻（注意：在向量資料庫中，距離越小表示越相似）
        distance_threshold = getattr(config, "IMAGE_SIMILARITY_THRESHOLD", 0.6)
        try:
            distance_threshold = float(distance_threshold)
        except Exception:
            distance_threshold = 0.6

        try:
            # 先按相似度排序文檔（距離越小越相似）
            sorted_docs = sorted(documents, key=lambda x: x.get("distance", float('inf')))
            
            for doc in sorted_docs:
                # 1) 距離過濾（距離小於門檻的才保留）
                doc_distance = doc.get("distance", float('inf'))
                if doc_distance > distance_threshold:
                    print(f"🖼️ 過濾文檔：距離 {doc_distance:.3f} > 門檻 {distance_threshold}")
                    continue

                # 2) 主題關鍵詞過濾
                if present_keywords:
                    source_name = (doc.get("source_file") or "").upper()
                    title_name = (doc.get("title") or "").upper()
                    if not any(k in source_name or k in title_name for k in present_keywords):
                        continue

                # 從文檔元數據中獲取圖片路徑
                doc_images = []
                if "metadata" in doc and isinstance(doc["metadata"], dict):
                    images_str = doc["metadata"].get("images")
                    if images_str:
                        for img_path in images_str.split("|"):
                            p = (img_path or "").strip()
                            if p and os.path.exists(p):
                                doc_images.append(p)

                # 從 images 欄位獲取圖片
                images_field = doc.get("images")
                if images_field:
                    for img_path in images_field:
                        if img_path and os.path.exists(img_path):
                            doc_images.append(img_path)

                # 將圖片與其文檔的相似度關聯
                for img_path in doc_images:
                    image_paths_with_score.append((img_path, doc_distance))

            # 按相似度排序（距離越小越前面）並去重
            seen_images = set()
            unique_images_sorted = []
            
            for img_path, distance in sorted(image_paths_with_score, key=lambda x: x[1]):
                if img_path not in seen_images:
                    seen_images.add(img_path)
                    unique_images_sorted.append(img_path)
                    if len(unique_images_sorted) >= 5:  # 限制最多5張
                        break

            print(f"🖼️ 找到 {len(unique_images_sorted)} 張相關圖片（門檻: {distance_threshold}，主題過濾: {'有' if present_keywords else '無'}）")
            return unique_images_sorted

        except Exception as e:
            print(f"獲取相關圖片錯誤: {e}")
            return []
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        獲取圖片資訊
        
        Args:
            image_path: 圖片路徑
            
        Returns:
            圖片資訊字典
        """
        try:
            if not os.path.exists(image_path):
                return {"error": "圖片不存在"}
            
            with Image.open(image_path) as img:
                return {
                    "path": image_path,
                    "filename": os.path.basename(image_path),
                    "size": img.size,
                    "format": img.format,
                    "mode": img.mode
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    def search_images_by_keyword(self, keyword: str) -> List[str]:
        """
        根據關鍵字搜尋圖片
        
        Args:
            keyword: 搜尋關鍵字
            
        Returns:
            匹配的圖片路徑列表
        """
        matching_images = []
        
        try:
            # 遍歷圖片目錄
            for root, dirs, files in os.walk(self.images_path):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                        # 檢查檔名是否包含關鍵字
                        if keyword.lower() in file.lower():
                            image_path = os.path.join(root, file)
                            matching_images.append(image_path)
            
            print(f"🔍 關鍵字 '{keyword}' 找到 {len(matching_images)} 張圖片")
            return matching_images
            
        except Exception as e:
            print(f"搜尋圖片錯誤: {e}")
            return []
    
    def resize_image(self, image_path: str, max_size: tuple = (800, 600)) -> str:
        """
        調整圖片大小（用於顯示優化）
        
        Args:
            image_path: 圖片路徑
            max_size: 最大尺寸 (寬, 高)
            
        Returns:
            調整後的圖片路徑
        """
        try:
            if not os.path.exists(image_path):
                return image_path
            
            with Image.open(image_path) as img:
                # 如果圖片已經小於最大尺寸，直接返回
                if img.size[0] <= max_size[0] and img.size[1] <= max_size[1]:
                    return image_path
                
                # 計算新尺寸（保持比例）
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # 生成新檔名
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                new_filename = f"{base_name}_resized.png"
                new_path = os.path.join(self.images_path, new_filename)
                
                # 保存調整後的圖片
                img.save(new_path, "PNG")
                
                return new_path
                
        except Exception as e:
            print(f"調整圖片大小錯誤: {e}")
            return image_path
