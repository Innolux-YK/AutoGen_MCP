"""
Embedding 服務模組
提供文字向量化功能，支援以下後端：
- sentence_transformers（本地模型）
- openai（經由 InnoAI 代理或 OpenAI 兼容端點）
"""

import os
import math
import requests
import numpy as np
from typing import List, Union, Optional
import config

class EmbeddingService:
    """文字向量化服務，依據 config.EMBEDDING_BACKEND 切換後端"""

    def __init__(self, model_name: Optional[str] = None, backend: Optional[str] = None):
        # 後端與模型名稱
        self.backend = (backend or getattr(config, "EMBEDDING_BACKEND", "sentence_transformers")).lower()
        if self.backend not in {"sentence_transformers", "openai"}:
            self.backend = "sentence_transformers"

        if model_name:
            self.model_name = model_name
        else:
            if self.backend == "openai":
                self.model_name = getattr(config, "GPT_EMBEDDING_MODEL", "text-embedding-ada-002")
            else:
                # 預設本地 ST 模型
                self.model_name = getattr(config, "LOCAL_MODEL", "all-MiniLM-L6-v2")

        # 通用狀態
        self.model = None  # 供 ST 後端使用
        self.api_key = getattr(config, "API_KEY", None)
        self.api_url = getattr(config, "get_api_url", lambda *_: None)(None) if self.backend == "openai" else None

        # 初始化
        self._load_model()
    
    def _load_model(self):
        """載入或配置後端資源"""
        if self.backend == "sentence_transformers":
            try:
                print(f"載入 ST embedding 模型: {self.model_name}")
                # 避免在 openai 後端也強制依賴 ST
                from sentence_transformers import SentenceTransformer  # 延遲載入

                os.makedirs(config.MODEL_PATH, exist_ok=True)
                cache_folder = os.path.join(config.MODEL_PATH, "sentence_transformers")
                os.makedirs(cache_folder, exist_ok=True)

                self.model = SentenceTransformer(
                    self.model_name,
                    cache_folder=cache_folder,
                )
                print(f"✅ ST 模型載入成功: {self.model_name}")
            except Exception as e:
                print(f"❌ 載入 ST 模型失敗: {e}")
                # 備援
                try:
                    from sentence_transformers import SentenceTransformer
                    self.model = SentenceTransformer("all-MiniLM-L6-v2")
                    print("✅ 使用備用 ST 模型: all-MiniLM-L6-v2")
                except Exception as e2:
                    print(f"❌ 備用 ST 模型也載入失敗: {e2}")
                    raise
        else:
            # OpenAI 後端不需預先載入模型
            print(f"使用 OpenAI Embedding 後端: {self.model_name}")
    
    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> List[List[float]]:
        """
        將文字編碼為向量
        
        Args:
            texts: 文字或文字列表
            normalize: 是否標準化向量
            
        Returns:
            向量列表
        """
        # 確保輸入是列表
        if isinstance(texts, str):
            texts = [texts]

        if self.backend == "openai":
            vectors = self._encode_openai(texts)
        else:
            if not self.model:
                raise Exception("ST 模型未載入")
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=False,  # 統一在下方處理 normalize
                convert_to_numpy=True,
            )
            if embeddings.ndim == 1:
                vectors = [embeddings.tolist()]
            else:
                vectors = embeddings.tolist()

        # 標準化（選擇性）
        if normalize and vectors:
            normed = []
            for v in vectors:
                arr = np.array(v, dtype=np.float32)
                n = np.linalg.norm(arr)
                if n > 0:
                    arr = arr / n
                normed.append(arr.tolist())
            return normed

        return vectors

    def _encode_openai(self, texts: List[str]) -> List[List[float]]:
        """呼叫 OpenAI 兼容的 Embeddings 端點，支援批次。"""
        if not self.api_key:
            raise RuntimeError("缺少 API_KEY，無法使用 OpenAI Embedding 後端")

        base_url = self.api_url or getattr(config, "API_URL", None) or getattr(config, "get_api_url", lambda *_: None)(None)
        if not base_url:
            raise RuntimeError("缺少 API_URL，無法使用 OpenAI Embedding 後端")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # 嘗試的 embeddings 端點（依序）
        endpoints = [
            f"{base_url}/embeddings",
            f"{base_url}/v1/embeddings",
        ]

        results: List[List[float]] = []
        batch_size = 64
        total = len(texts)
        num_batches = math.ceil(total / batch_size)

        for bi in range(num_batches):
            chunk = texts[bi * batch_size : (bi + 1) * batch_size]
            payload = {"model": self.model_name, "input": chunk}

            success = False
            last_err = None
            for ep in endpoints:
                try:
                    resp = requests.post(ep, headers=headers, json=payload, timeout=60)
                    if resp.status_code == 200:
                        data = resp.json()
                        # OpenAI 回傳格式：{"data": [{"embedding": [...]} ...]}
                        batch_vectors = [item["embedding"] for item in data.get("data", [])]
                        if len(batch_vectors) != len(chunk):
                            raise RuntimeError("回傳向量數量與請求不一致")
                        results.extend(batch_vectors)
                        success = True
                        break
                    else:
                        last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
                except requests.RequestException as e:
                    last_err = str(e)
                    continue

            if not success:
                # 直接拋出錯誤，不進行備援處理
                raise RuntimeError(f"OpenAI Embedding 請求失敗：{last_err}")

        return results
    
    def get_model_info(self) -> str:
        """獲取模型資訊"""
        if self.backend == "sentence_transformers" and self.model:
            try:
                dim = self.model.get_sentence_embedding_dimension()
            except Exception:
                dim = "?"
            return f"ST: {self.model_name} (維度: {dim})"
        elif self.backend == "openai":
            return f"OpenAI: {self.model_name}"
        return "模型未載入"
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        計算兩個文字的相似度
        
        Args:
            text1: 文字1
            text2: 文字2
            
        Returns:
            相似度分數 (0-1)
        """
        embeddings = self.encode([text1, text2])
        
        # 計算餘弦相似度
        vec1 = np.array(embeddings[0])
        vec2 = np.array(embeddings[1])
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

# 全域變數存儲 embedding 服務實例
_embedding_service: Optional[EmbeddingService] = None

def get_embedding_service(model_name: Optional[str] = None, backend: Optional[str] = None) -> EmbeddingService:
    """獲取 embedding 服務實例（單例）。優先使用 config 設定。"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_name=model_name, backend=backend)
    return _embedding_service
