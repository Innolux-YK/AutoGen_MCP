"""
集中初始化：在各個 pages/* 中 import 並呼叫 ensure_session_init()，
統一建立 ConversationManager 與對話狀態，避免每頁重複與遺漏。
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

import streamlit as st


def _create_new_conversation() -> str:
    conv_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.conversations[conv_id] = {
        "id": conv_id,
        "title": "新對話",
        "messages": [],
        "chat_history": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    st.session_state.current_conversation_id = conv_id
    return conv_id


def create_new_conversation() -> str:
    """公開的建立新對話方法，供頁面呼叫。"""
    return _create_new_conversation()


essential_keys = [
    "conversations",
    "current_conversation_id",
    "conversation_manager",
]


def ensure_session_init() -> None:
    """確保必要的 session_state 已初始化。"""
    # 對話容器
    if "conversations" not in st.session_state:
        # 初始化對話容器
        st.session_state.conversations = {}

    # 當前對話 id
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None

    # 後端管理器
    if "conversation_manager" not in st.session_state or st.session_state.conversation_manager is None:
        from agents.conversation_manager import ConversationManager
        st.session_state.conversation_manager = ConversationManager()

    # 至少保證有一個對話
    if not st.session_state.current_conversation_id:
        _create_new_conversation()


def get_current_conversation() -> Dict[str, Any]:
    ensure_session_init()
    conv_id = st.session_state.current_conversation_id
    if conv_id not in st.session_state.conversations:
        _create_new_conversation()
        conv_id = st.session_state.current_conversation_id
    return st.session_state.conversations[conv_id]


def update_conversation_title(conversation_id: str, new_title: str) -> None:
    ensure_session_init()
    if conversation_id in st.session_state.conversations:
        st.session_state.conversations[conversation_id]["title"] = new_title
        st.session_state.conversations[conversation_id]["updated_at"] = datetime.now().isoformat()


def delete_conversation(conversation_id: str) -> None:
    ensure_session_init()
    if conversation_id in st.session_state.conversations:
        del st.session_state.conversations[conversation_id]
        if st.session_state.current_conversation_id == conversation_id:
            if st.session_state.conversations:
                st.session_state.current_conversation_id = list(st.session_state.conversations.keys())[-1]
            else:
                st.session_state.current_conversation_id = None
                _create_new_conversation()
