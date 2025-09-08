"""
關於頁面
"""

import streamlit as st
from datetime import datetime

st.title("ℹ️ 關於 AI助手")

# 系統介紹
st.header("🤖 系統簡介")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    **AI助手** 是一個基於大語言模型的智能對話系統，專為企業知識管理和問題解決而設計。
    
    ### 🎯 設計目標
    - 提供準確、即時的技術支援
    - 整合企業內部知識資源
    - 簡化複雜問題的分析流程
    - 提升工作效率和決策品質
    
    ### ✨ 核心特色
    - **智能對話**: 支援自然語言交互，理解上下文
    - **知識整合**: 基於企業文檔建立專業知識庫
    - **工具集成**: 整合多種實用工具和計算功能
    - **多媒體支援**: 顯示相關圖片、文檔和資料
    """)

# 技術架構
st.header("🏗️ 技術架構")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🧠 AI 核心")
    st.markdown("""
    - **大語言模型**: InnoAI GPT
    - **嵌入模型**: Text-Embedding
    - **向量資料庫**: ChromaDB
    - **智能路由**: LangChain Agent
    """)

with col2:
    st.subheader("⚙️ 後端服務")
    st.markdown("""
    - **對話管理**: ConversationManager
    - **檢索服務**: RAG Agent
    - **文檔處理**: DocumentService
    - **圖片服務**: ImageService
    """)

with col3:
    st.subheader("🎨 前端介面")
    st.markdown("""
    - **UI 框架**: Streamlit
    - **導航系統**: st.navigation
    - **即時串流**: write_stream
    - **響應式設計**: 多欄位佈局
    """)

# 功能模組
st.header("🔧 功能模組")

# 使用 tabs 來組織不同的功能模組
tab1, tab2, tab3, tab4 = st.tabs(["💬 對話系統", "🔍 檢索引擎", "🛠️ 工具集", "📊 資料服務"])

with tab1:
    st.markdown("""
    ### 對話管理系統
    
    **核心功能**:
    - 多輪對話支援
    - 上下文記憶
    - 對話履歷管理
    - 串流回應顯示
    
    **技術特點**:
    - 基於 session state 的狀態管理
    - 支援多個對話並行
    - 自動生成對話標題
    - 智能問題路由
    """)
    
    st.code("""
    # 對話管理示例
    conversation = {
        "id": "conv_20240101_120000",
        "title": "SPC 問題討論",
        "messages": [...],
        "chat_history": [...],
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:30:00"
    }
    """, language="python")

with tab2:
    st.markdown("""
    ### RAG 檢索引擎
    
    **檢索流程**:
    1. 問題理解和預處理
    2. 向量化查詢
    3. 相似度計算
    4. 結果排序和篩選
    5. 上下文構建
    
    **優化技術**:
    - 語義分割和重疊
    - 混合檢索策略
    - 動態相似度閾值
    - 結果去重和聚合
    """)
    
    st.code("""
    # RAG 檢索示例
    def search_and_answer(query, chat_history):
        # 1. 預處理查詢
        processed_query = preprocess_query(query)
        
        # 2. 向量檢索
        documents = vector_db.similarity_search(
            processed_query, k=5
        )
        
        # 3. 生成回答
        response = llm.generate(
            context=documents,
            query=query,
            history=chat_history
        )
        
        return response
    """, language="python")

with tab3:
    st.markdown("""
    ### 智能工具集
    
    **可用工具**:
    - **計算工具**: 數學運算、公式計算
    - **時間工具**: 日期時間查詢
    - **EDC 工具**: 檔案格式驗證
    - **SPC 工具**: 統計過程控制分析
    
    **工具特點**:
    - 自動工具選擇
    - 參數智能提取
    - 結果格式化
    - 錯誤處理機制
    """)
    
    st.code("""
    # 工具使用示例
    class ToolManager:
        def route_to_tool(self, query, tools):
            # 分析查詢意圖
            intent = self.analyze_intent(query)
            
            # 選擇合適工具
            tool = self.select_tool(intent, tools)
            
            # 執行工具
            result = tool.execute(query)
            
            return result
    """, language="python")

with tab4:
    st.markdown("""
    ### 資料服務層
    
    **服務類型**:
    - **文檔服務**: 文檔解析、索引、檢索
    - **圖片服務**: 圖片匹配、顯示、管理
    - **資料庫服務**: 向量儲存、元數據管理
    - **API 服務**: 外部服務整合
    
    **資料流程**:
    1. 資料收集和清理
    2. 格式統一和驗證
    3. 向量化和索引
    4. 儲存和版本管理
    """)
    
    st.code("""
    # 資料服務示例
    class DocumentService:
        def process_document(self, file_path):
            # 1. 解析文檔
            content = self.parse_document(file_path)
            
            # 2. 分段處理
            chunks = self.split_text(content)
            
            # 3. 向量化
            embeddings = self.embed_chunks(chunks)
            
            # 4. 儲存到資料庫
            self.store_embeddings(embeddings)
    """, language="python")

st.markdown("""
---

*最後更新: {now}*
""".format(now=datetime.now().strftime("%Y年%m月%d日")))
