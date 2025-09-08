import os

# 應用配置
APP_TITLE = "AI助手"

# 測試模式配置
DEBUG_MODE = True  # 開啟除錯模式
FALLBACK_MODE = False  # 關閉備用模式（API 失敗時直接顯示錯誤）

# 路徑配置
DATASET_PATH = "dataset"
MODEL_PATH = "models"
VECTOR_DB_PATH = "vector_db"
IMAGES_PATH = "images"

# 模型配置
API_KEY = "inno-srrh3ixa6ji6urjnlaudxuymvmldjitfylncduhxnr4lwuxqikxq"

# 模型平台映射 - 需要在函數定義之前
MODEL_PLATFORM_MAP = {
    "gpt-4.1-mini": "openai", 
    "gpt-4.1": "openai",
    # "gemini-1.5-flash-latest": "google",
    # "gemini-2.5-flash": "google",
    # "gemini-2.5-pro": "google",
}

# API URL配置 - 根據模型自動選擇平台
def get_api_url(model_name=None):
    """根據模型名稱返回對應的API URL"""
    if model_name and model_name in MODEL_PLATFORM_MAP:
        platform = MODEL_PLATFORM_MAP[model_name]
    else:
        # 默認使用openai平台
        platform = "openai"
    
    urls = {
        "openai": "http://innoai.cminl.oa/agency/proxy/openai/platform",
        "google": "http://innoai.cminl.oa/agency/proxy/google/platform"
    }
    return urls.get(platform, urls["openai"])

# 輔助函數：從 MODEL_PLATFORM_MAP 取得模型清單
def get_available_models():
    """取得所有可用的模型清單"""
    return list(MODEL_PLATFORM_MAP.keys())

def get_openai_models():
    """取得 OpenAI 平台的模型清單"""
    return [model for model, platform in MODEL_PLATFORM_MAP.items() if platform == "openai"]

def get_google_models():
    """取得 Google 平台的模型清單"""
    return [model for model, platform in MODEL_PLATFORM_MAP.items() if platform == "google"]

# 預設使用OpenAI平台
API_URL = get_api_url()

# Embedding模型配置
EMBEDDING_BACKEND = "openai"  # 選項: "sentence_transformers", "openai"
GPT_EMBEDDING_MODEL = "text-embedding-ada-002" # OpenAI Embedding模型
LOCAL_MODEL = "all-mpnet-base-v2" # 本地Sentence Transformer模型

# 智能分塊配置
CHUNKING_METHOD = "semantic"  # 選項: "fixed", "semantic", "keyword", "structure"
# "semantic"    # 語義分塊
# "keyword"   # 關鍵詞分塊  
# "structure" # 結構分塊
# "fixed"     # 固定長度分塊
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
MIN_CHUNK_SIZE = 100
SEMANTIC_SIMILARITY_THRESHOLD = 0.3  # 語義相似度閾值
KEYWORD_OVERLAP_THRESHOLD = 0.2      # 關鍵詞重疊度閾值

# 中文處理配置
USE_JIEBA_USERDICT = True  # 是否使用自定義詞典
CUSTOM_DICT_PATH = "./dataset/custom_dict.txt"  # 自定義詞典路徑

# LLM配置
LLM_BACKEND = "innoai"  # 選項: "ollama", "huggingface", "innoai"

# 介面開關預設：是否預設使用 RAG 架構
# True  -> Switch 預設為開（RAG架構，啟用檢索）
# False -> Switch 預設為關（通用GPT，跳過檢索）
DEFAULT_USE_RAG = True

# 是否允許用戶在界面中更改 USE_RAG 設定
# True  -> 用戶可以在界面中切換 RAG 模式
# False -> 鎖定 RAG 模式，用戶無法在界面中切換
ALLOW_RAG_TOGGLE = False

# InnoAI預設模型
INNOAI_DEFAULT_MODEL = "gpt-4.1"  # 預設使用的模型

# Hugging Face配置
HF_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"  # 輕量版本
HF_DEVICE = "auto"  # "auto", "cpu", "cuda"
HF_LOAD_IN_8BIT = False  # 關閉8位量化以避免兼容性問題
HF_MAX_LENGTH = 2048

# Ollama配置
OLLAMA_MODEL_NAME = "qwen2.5:7b"  # Ollama模型名稱
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama默認地址

# 通用LLM配置
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 2048

# 搜尋配置
SIMILARITY_THRESHOLD = 0.3        # 文檔檢索的最低相似度門檻（提高以過濾低品質結果）
IMAGE_SIMILARITY_THRESHOLD = 0.6  # 圖片顯示的相似度門檻（較高確保相關性）

# EDC 配置檔案路徑
GETEDCFILE_CONFIG_PATH = r"D:\Git_Code\GETEDCFILE_CONFIG"  # EDC 配置檔案根目錄

# API 日誌配置
API_LOG_CONFIG = {
    "enabled": True,                                    # 是否啟用API日誌
    "log_level": "INFO",                               # 日誌級別: DEBUG, INFO, WARNING, ERROR, CRITICAL
    "log_file": "logs/api_queries.log",               # API查詢日誌檔案路徑
    "max_file_size": 10 * 1024 * 1024,               # 最大檔案大小 (10MB)
    "backup_count": 5,                                 # 保留的備份檔案數量
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 日誌格式
    "date_format": "%Y-%m-%d %H:%M:%S",               # 時間格式
    "encoding": "utf-8",                              # 檔案編碼
    "log_input": True,                                # 是否記錄輸入參數
    "log_output": True,                               # 是否記錄輸出結果
    "log_execution_time": True,                       # 是否記錄執行時間
    "log_sql_queries": True,                          # 是否記錄SQL查詢語句
    "mask_sensitive_data": True,                      # 是否遮罩敏感資料
    "max_data_length": 1000,                          # 記錄資料的最大長度
}

# 確保必要的目錄存在
def ensure_directories():
    directories = [MODEL_PATH, VECTOR_DB_PATH, IMAGES_PATH, "data", "logs"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # 創建自定義詞典檔案（如果不存在）
    if not os.path.exists(CUSTOM_DICT_PATH):
        # 創建一個空的自定義詞典檔案
        with open(CUSTOM_DICT_PATH, 'w', encoding='utf-8') as f:
            f.write("# 自定義詞典\n# 格式：詞語 詞頻 詞性\n# 範例：\n# 人工智能 100 n\n# 機器學習 100 n\n")
        print(f"已創建自定義詞典檔案：{CUSTOM_DICT_PATH}")
        print("您可以編輯此檔案添加領域專用詞彙")

if __name__ == "__main__":
    ensure_directories()
