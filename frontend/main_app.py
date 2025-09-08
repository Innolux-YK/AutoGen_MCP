"""
聊天首頁（Home）。
使用官方多頁結構：此檔為首頁，左側將自動列出 pages/ 內保留的頁面（如 狀態/關於）。
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

import streamlit as st

# 將專案根目錄加入 sys.path（供子頁面引用）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.app_init import (
    ensure_session_init,
    get_current_conversation,
    update_conversation_title,
    create_new_conversation,
    delete_conversation,
)
from frontend.ui_helpers import (
    create_unique_images_list,
    create_unique_documents_list,
    open_file_with_system,
    display_message,
)
import config

# 頁面配置（Home）
st.set_page_config(
    page_title="💬 AI助手",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定義CSS：減少標題上方空白
st.markdown("""
<style>
    .main .block-container {
        padding-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.title("💬 AI助手")

# 初始化狀態
ensure_session_init()
current_conv = get_current_conversation()

# 側邊欄：美化的對話管理抽屜（不注入全域 CSS）
with st.sidebar:
    st.markdown("## 🗂️ 對話管理")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("➕ 新對話", use_container_width=True):
                create_new_conversation()
                st.rerun()
        with c2:
            if st.button("🗑️ 刪除目前", use_container_width=True):
                delete_conversation(current_conv["id"])
                st.rerun()

        # 快速過濾
        q = st.text_input("搜尋對話標題", value=st.session_state.get("conv_filter", ""), placeholder="輸入關鍵字…")
        st.session_state.conv_filter = q

        conversations = st.session_state.conversations
        conv_items = sorted(
            conversations.values(),
            key=lambda x: x.get("updated_at", x.get("created_at", "")),
            reverse=True,
        )
        if q:
            conv_items = [c for c in conv_items if q.lower() in c.get("title", "").lower()]

        options = [c["id"] for c in conv_items]

        def label_func(cid: str) -> str:
            conv = conversations.get(cid, {})
            title = conv.get("title", "新對話")
            msgs = len(conv.get("messages", []))
            t = conv.get("updated_at") or conv.get("created_at") or ""
            t_disp = t.replace("T", " ")[:16] if t else ""
            return f"{title} · {msgs} 訊息 · {t_disp}"

        if options:
            current_index = options.index(current_conv["id"]) if current_conv["id"] in options else 0
            selected_id = st.selectbox(
                "選擇對話",
                options=options,
                index=current_index,
                format_func=label_func,
            )
            if selected_id != current_conv["id"]:
                st.session_state.current_conversation_id = selected_id
                st.rerun()
        else:
            st.caption("尚無對話，請建立新對話。")

    st.markdown("---")
    with st.expander("⚙️ 系統操作"):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧹 清空對話", key="clear_conv"):
                current_conv["messages"] = []
                current_conv["chat_history"] = []
                current_conv["updated_at"] = datetime.now().isoformat()
                st.rerun()
        with c2:
            if st.button("🔄 重新載入", key="reload_app"):
                st.rerun()

# 主要控制列
col1, col2, col3, col4 = st.columns([1.5, 2, 2.5, 1.5])

with col1:
    # 從 config.py 讀取可用模型列表
    available_models = config.get_available_models()
    default_model = config.INNOAI_DEFAULT_MODEL
    
    # 確保默認模型在列表中，如果不在則使用第一個可用模型
    if default_model not in available_models:
        default_model = available_models[0] if available_models else "gpt-4.1"
    
    default_index = available_models.index(default_model) if default_model in available_models else 0
    
    llm_model = st.selectbox(
        "LLM 模型",
        options=available_models,
        index=default_index,
        key="llm_model",
        help="選擇要使用的語言模型",
    )

with col2:
    # 保持用戶的問題處理方式選擇
    default_query_mode = st.session_state.get("query_mode_selection", "詢問問題")
    default_query_index = 0 if default_query_mode == "詢問問題" else 1
    
    query_mode = st.selectbox(
        "問題處理方式",
        options=["詢問問題", "尋找真因"],
        index=default_query_index,
        key="query_mode",
        help="詢問問題：從知識庫搜尋答案。\n尋找真因：使用 Agent/工具分析。",
    )
    
    # 保存用戶的選擇
    st.session_state.query_mode_selection = query_mode

with col3:
    new_title = st.text_input(
        "對話標題",
        value=current_conv["title"],
        key="conv_title",
        help="點擊編輯對話標題",
    )
    if new_title != current_conv["title"]:
        update_conversation_title(current_conv["id"], new_title)

with col4:
    # 在標籤上方添加空白，使按鈕與其他輸入框對齊
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
    
    # 按鈕群組：放在同一列中
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️", help="清空當前對話", key="clear_main", use_container_width=True):
            current_conv["messages"] = []
            current_conv["chat_history"] = []
            current_conv["updated_at"] = datetime.now().isoformat()
            st.rerun()
    with c2:
        if st.button("🔄", help="重新載入頁面", key="reload_main", use_container_width=True):
            st.rerun()

st.divider()

# 顯示歷史訊息
# 始終顯示提示範例
if query_mode == "詢問問題":
    example_text = """💡 試試問我：
1. 「SPC沒進Chart查找方法」
2. 「EDC上傳檔案格式」"""
else:
    example_text = """💡 試試問我：
1. 「你有哪些功能」
2. 「SPC為什麼沒有進CHART」
3. 「EDC檔案格式確認」
4. 「IP EDC查找」"""

st.info(example_text)

for message in current_conv["messages"]:
    display_message(message)

# 處理 pending 查詢（串流）
if st.session_state.get("pending_query"):
    payload = st.session_state.get("pending_query")
    with st.status("🤖 正在處理您的問題...", expanded=False) as status:
        try:
            query_type_display = "知識庫搜尋" if payload["force_query_type"] == "rag_search" else "智能工具分析"
            st.write(f"🔍 分析問題類型: {query_type_display}")
            st.write("⚙️ 初始化AI處理器...")
            st.write("📝 生成回應...")
            status.update(label="✅ 處理完成！正在顯示回應...", state="complete", expanded=False)
        except Exception as e:
            st.write(f"❌ 處理失敗: {str(e)}")
            status.update(label="❌ 處理失敗", state="error", expanded=True)
            st.session_state.pop("pending_query", None)
            st.rerun()

    response_container = st.container()
    with response_container:
        with st.chat_message("assistant"):
            response_data_holder = [None]

            def response_generator():
                for chunk in st.session_state.conversation_manager.get_response_stream(
                    payload["q"],
                    current_conv["chat_history"],
                    force_query_type=payload["force_query_type"],
                    llm_model=payload.get("llm_model", "gpt-4.1"),
                ):
                    if isinstance(chunk, dict) and "__FINAL_RESPONSE__" in chunk:
                        response_data_holder[0] = chunk["__FINAL_RESPONSE__"]
                    else:
                        yield chunk

            response_text = st.write_stream(response_generator())
            full_response_data = response_data_holder[0]
            st.caption(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            if full_response_data:
                images = full_response_data.get("images") or []
                if images:
                    unique_images = create_unique_images_list(images)
                    if unique_images:
                        st.markdown("**📸 相關圖片：**")
                        
                        # 使用tabs來顯示圖片，便於切換和放大觀看
                        img_tabs = st.tabs([f"圖片 {i+1}" for i in range(len(unique_images[:3]))])
                        
                        for i, img_path in enumerate(unique_images[:3]):
                            try:
                                with img_tabs[i]:
                                    # 圖片名稱
                                    st.caption(f"� {os.path.basename(img_path)}")
                                    # 可放大的圖片顯示（修正棄用警告）
                                    st.image(img_path, use_container_width=True)
                            except Exception as e:
                                st.error(f"無法顯示圖片 {i+1}: {e}")


                docs = full_response_data.get("source_documents") or []
                if docs:
                    unique_docs = create_unique_documents_list(docs)
                    if unique_docs:
                        with st.expander("📄 查看相關文檔來源", expanded=False):
                            for i, doc in enumerate(unique_docs[:3]):
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(
                                        f"""
                                    **📄 文檔 {i+1}**  
                                    **檔案:** {doc.get('source_file','Unknown')}  
                                    **標題:** {doc.get('title','No title')}  
                                    **內容預覽:** {doc.get('content','')[:150]}...
                                    """
                                    )
                                with col2:
                                    file_path = ""
                                    if "metadata" in doc and isinstance(doc["metadata"], dict):
                                        file_path = doc["metadata"].get("file_path", "")
                                    elif "file_path" in doc:
                                        file_path = doc["file_path"]

                                    if file_path and os.path.exists(file_path):
                                        if st.button(
                                            f"📂 開啟",
                                            key=f"open_doc_{i}_{id(file_path)}_{hash(str(doc))}",
                                            help=f"開啟原始檔案: {os.path.basename(file_path)}",
                                        ):
                                            if open_file_with_system(file_path):
                                                st.success(f"已開啟: {os.path.basename(file_path)}")
                                    else:
                                        st.caption("檔案路徑不可用")

                                if i < len(unique_docs) - 1:
                                    st.divider()

    if full_response_data:
        current_conv["messages"].append(
            {
                "role": "assistant",
                "content": response_text,
                "images": full_response_data.get("images", []),
                "source_documents": full_response_data.get("source_documents", []),
                "query_type": full_response_data.get("query_type", "unknown"),
                "confidence": full_response_data.get("confidence", 0.0),
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )
    else:
        current_conv["messages"].append(
            {
                "role": "assistant",
                "content": response_text,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )

    current_conv["chat_history"].extend(
        [
            {"role": "user", "content": payload["q"]},
            {"role": "assistant", "content": response_text},
        ]
    )

    if current_conv["title"] == "新對話" and len(current_conv["messages"]) == 2:
        first_question = payload["q"][:30] + ("..." if len(payload["q"]) > 30 else "")
        update_conversation_title(current_conv["id"], first_question)

    current_conv["updated_at"] = datetime.now().isoformat()
    st.session_state.pop("pending_query", None)
    st.rerun()

# 底部輸入
user_prompt = st.chat_input("請輸入您的問題...")
if user_prompt and user_prompt.strip():
    q = user_prompt.strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    force_query_type = "rag_search" if query_mode == "詢問問題" else "agent"

    current_conv["messages"].append({"role": "user", "content": q, "time": now})
    st.session_state["pending_query"] = {
        "q": q, 
        "force_query_type": force_query_type, 
        "llm_model": llm_model,
        "time": now
    }
    st.rerun()
