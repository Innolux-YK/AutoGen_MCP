"""
系統狀態頁面
"""

import streamlit as st
import os
import sys
import psutil
import platform
from datetime import datetime

# 將專案根目錄加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

st.title("📊 系統狀態")

# 系統資訊
st.header("💻 系統資訊")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("作業系統", platform.system())
    st.metric("Python 版本", platform.python_version())

with col2:
    # CPU 使用率
    cpu_percent = psutil.cpu_percent(interval=1)
    st.metric("CPU 使用率", f"{cpu_percent}%", delta=None)
    
    # 記憶體使用率
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    st.metric("記憶體使用率", f"{memory_percent}%", delta=None)

with col3:
    # 磁碟使用率
    disk = psutil.disk_usage('/')
    disk_percent = (disk.used / disk.total) * 100
    st.metric("磁碟使用率", f"{disk_percent:.1f}%", delta=None)

# AI 服務狀態
st.header("🤖 AI 服務狀態")

if "conversation_manager" in st.session_state:
    try:
        status = st.session_state.conversation_manager.get_system_status()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📚 資料庫狀態")
            db_status = status.get("database", {})
            
            if isinstance(db_status, dict):
                for key, value in db_status.items():
                    if key == "document_count":
                        st.metric("文檔數量", value)
                    elif key == "status":
                        st.success(f"狀態: {value}" if value == "正常" else f"狀態: {value}")
                    else:
                        st.info(f"{key}: {value}")
            else:
                st.info(f"資料庫狀態: {db_status}")
        
        with col2:
            st.subheader("🧠 模型狀態")
            model_status = status.get("model", {})
            
            if isinstance(model_status, dict):
                for key, value in model_status.items():
                    if key == "status":
                        st.success(f"狀態: {value}" if value == "正常" else f"狀態: {value}")
                    else:
                        st.info(f"{key}: {value}")
            else:
                st.info(f"模型狀態: {model_status}")
        
        # 代理狀態
        st.subheader("🤖 代理狀態")
        agents_status = status.get("agents", {})
        
        if isinstance(agents_status, dict):
            agent_cols = st.columns(len(agents_status))
            for i, (agent_name, agent_status) in enumerate(agents_status.items()):
                with agent_cols[i]:
                    status_color = "🟢" if agent_status == "運行中" else "🔴"
                    st.write(f"{status_color} **{agent_name}**")
                    st.write(f"狀態: {agent_status}")
        
        # 服務狀態
        st.subheader("⚙️ 服務狀態")
        services_status = status.get("services", {})
        
        if isinstance(services_status, dict):
            service_cols = st.columns(len(services_status))
            for i, (service_name, service_status) in enumerate(services_status.items()):
                with service_cols[i]:
                    status_color = "🟢" if service_status == "運行中" else "🔴"
                    st.write(f"{status_color} **{service_name}**")
                    st.write(f"狀態: {service_status}")
        
        # 詳細狀態 JSON
        with st.expander("📄 詳細狀態資訊"):
            st.json(status)
            
    except Exception as e:
        st.error(f"❌ 無法獲取 AI 服務狀態: {e}")
else:
    st.warning("⚠️ AI 服務未初始化")

# 對話統計
st.header("📈 對話統計")

if "conversations" in st.session_state:
    conversations = st.session_state.conversations
    
    if conversations:
        total_conversations = len(conversations)
        total_messages = sum(len(conv.get("messages", [])) for conv in conversations.values())
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("總對話數", total_conversations)
        
        with col2:
            st.metric("總訊息數", total_messages)
        
        with col3:
            avg_messages = total_messages / total_conversations if total_conversations > 0 else 0
            st.metric("平均每對話訊息數", f"{avg_messages:.1f}")
        
        # 對話活動圖表
        st.subheader("📊 對話活動")
        
        # 準備圖表數據
        conversation_data = []
        for conv in conversations.values():
            try:
                created_time = datetime.fromisoformat(conv["created_at"])
                conversation_data.append({
                    "日期": created_time.strftime("%Y-%m-%d"),
                    "標題": conv["title"][:20] + "..." if len(conv["title"]) > 20 else conv["title"],
                    "訊息數": len(conv.get("messages", []))
                })
            except:
                continue
        
        if conversation_data:
            try:
                import pandas as pd
                df = pd.DataFrame(conversation_data)
                
                # 按日期統計對話數
                daily_conversations = df.groupby("日期").size().reset_index(name="對話數")
                st.bar_chart(daily_conversations.set_index("日期"))
                
                # 對話列表
                with st.expander("📋 對話列表"):
                    st.dataframe(df, use_container_width=True)
            except ImportError:
                st.warning("⚠️ 需要安裝 pandas 來顯示圖表: pip install pandas")
                # 簡單的文字統計
                st.write("**對話統計**:")
                for item in conversation_data:
                    st.write(f"- {item['日期']}: {item['標題']} ({item['訊息數']} 訊息)")
    else:
        st.info("📝 還沒有對話記錄")
else:
    st.warning("⚠️ 對話資料未初始化")

# 系統日誌
st.header("📋 系統日誌")

# 模擬系統日誌
log_entries = [
    {"時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "層級": "INFO", "訊息": "系統啟動完成"},
    {"時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "層級": "INFO", "訊息": "AI 服務初始化成功"},
    {"時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "層級": "INFO", "訊息": "向量資料庫連接正常"},
]

try:
    import pandas as pd
    df_logs = pd.DataFrame(log_entries)

    # 使用顏色標示不同層級
    def color_log_level(val):
        if val == "ERROR":
            return "background-color: #ffebee"
        elif val == "WARNING":
            return "background-color: #fff3e0"
        elif val == "INFO":
            return "background-color: #e8f5e8"
        return ""

    styled_df = df_logs.style.applymap(color_log_level, subset=["層級"])
    st.dataframe(styled_df, use_container_width=True)
    
except ImportError:
    st.warning("⚠️ 需要安裝 pandas 來顯示日誌表格: pip install pandas")
    # 簡單的文字顯示
    for entry in log_entries:
        level_color = {"INFO": "🟢", "WARNING": "🟡", "ERROR": "🔴"}.get(entry["層級"], "⚪")
        st.write(f"{level_color} **{entry['層級']}** | {entry['時間']} | {entry['訊息']}")

# 重新整理按鈕
if st.button("🔄 重新整理狀態", type="primary"):
    st.rerun()

# 自動重新整理
auto_refresh = st.checkbox("🔄 自動重新整理 (30秒)", value=False)
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()
