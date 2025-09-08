"""
前端 UI 輔助工具：
- open_file_with_system: 以系統預設應用開啟檔案
- create_unique_images_list: 去重並規範圖片路徑
- create_unique_documents_list: 去重並規範文檔來源
- display_message: 統一渲染訊息（支援圖片與文檔）

注意：不注入任何會影響側邊欄的 CSS/JS，避免干擾官方多頁抽屜。
"""
from __future__ import annotations

import os
import platform
import subprocess
import re
import xml.dom.minidom
from datetime import datetime
from typing import Any, Dict, List

import streamlit as st


def is_xml_content(text: str) -> bool:
    """檢測文字內容是否為 XML 格式"""
    if not text or not isinstance(text, str):
        return False
    
    # 移除前後空白
    text = text.strip()
    
    # 排除 Markdown 表格 - 如果包含表格語法，不是 XML
    if '|' in text and ('---' in text or '=====' in text):
        return False
    
    # 排除 Markdown 標題
    if re.search(r'^#+\s', text, re.MULTILINE):
        return False
    
    # 檢查是否以 XML 宣告開始（最可靠的判斷）
    if re.match(r'^\s*<\?xml.*?\?>', text, re.IGNORECASE | re.DOTALL):
        return True
    
    # 檢查是否以明確的 XML 根標籤開始，並且整個內容看起來像 XML
    xml_root_pattern = r'^\s*<([a-zA-Z_][\w\-\.]*)[^>]*?>'
    root_match = re.match(xml_root_pattern, text, re.IGNORECASE)
    
    if root_match:
        root_tag = root_match.group(1)
        # 檢查是否有對應的結束標籤
        closing_tag_pattern = f'</{re.escape(root_tag)}\\s*>\\s*$'
        if re.search(closing_tag_pattern, text, re.IGNORECASE):
            # 進一步檢查：XML 內容應該主要由標籤構成，而不是大量文字
            # 計算標籤密度
            tag_count = len(re.findall(r'<[^>]+>', text))
            text_without_tags = re.sub(r'<[^>]*>', '', text).strip()
            
            # 如果標籤數量合理且去除標籤後的純文字不會太長，視為 XML
            if tag_count >= 2 and (len(text_without_tags) < len(text) * 0.7):
                return True
    
    return False


def format_xml_content(xml_text: str) -> str:
    """格式化 XML 內容，如果格式化失敗則返回原始內容"""
    try:
        # 嘗試解析和格式化 XML
        dom = xml.dom.minidom.parseString(xml_text)
        formatted = dom.toprettyxml(indent="    ", encoding=None)
        
        # 移除空行和多餘的空白
        lines = [line for line in formatted.split('\n') if line.strip()]
        
        # 移除第一行的 XML 宣告如果它是自動生成的
        if lines and lines[0].startswith('<?xml version="1.0" ?>') and not xml_text.strip().startswith('<?xml'):
            lines = lines[1:]
        
        return '\n'.join(lines)
    except Exception:
        # 如果解析失敗，返回原始內容
        return xml_text


def _project_root() -> str:
    # 本檔位於 frontend/，往上一層即為專案根目錄
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def open_file_with_system(file_path: str) -> bool:
    """使用系統預設應用程式開啟檔案。
    回傳 True 表示已嘗試開啟，False 表示失敗。
    """
    try:
        if not file_path:
            st.error("檔案路徑為空")
            return False

        # 支援相對路徑
        path = file_path
        if not os.path.isabs(path):
            path = os.path.normpath(os.path.join(_project_root(), path))

        if not os.path.exists(path):
            st.error(f"檔案不存在: {path}")
            return False

        system = platform.system()
        if system == "Windows":
            # 使用 start 指令開啟（需透過 shell）
            subprocess.run(f'start "" "{path}"', shell=True, check=True)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", path], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", path], check=True)

        return True
    except Exception as e:
        st.error(f"無法開啟檔案: {e}")
        return False


def create_unique_images_list(images: List[str]) -> List[str]:
    """按檔名去重並轉為可讀取的絕對路徑。"""
    if not images:
        return []

    unique_images: List[str] = []
    seen_filenames = set()
    root = _project_root()

    for img_path in images:
        if not img_path or not isinstance(img_path, str):
            continue
        p = img_path.strip()
        if not p:
            continue

        abs_path = p if os.path.isabs(p) else os.path.join(root, p)
        abs_path = os.path.normpath(abs_path)
        if os.path.exists(abs_path):
            filename = os.path.basename(abs_path)
            if filename not in seen_filenames:
                seen_filenames.add(filename)
                unique_images.append(abs_path)

    return unique_images


def create_unique_documents_list(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """以規範化檔案路徑為主鍵去重，避免同一文檔重複顯示。
    同時依相似度門檻過濾並排序（距離越小越相似）。
    優先使用 metadata.file_path，其次使用 doc.file_path，再次使用 source_file。
    若皆無有效路徑，則以 (title + content 前 100 字) 近似去重。
    """
    if not docs:
        return []

    import config
    
    # 相似度門檻過濾（距離越小越相似）
    document_threshold = getattr(config, "SIMILARITY_THRESHOLD", 0.3)
    try:
        document_threshold = float(document_threshold)
    except Exception:
        document_threshold = 0.3

    root = _project_root()

    def canonical_path(d: Dict[str, Any]) -> str:
        path = ""
        try:
            metadata = d.get("metadata")
            if isinstance(metadata, dict):
                path = metadata.get("file_path") or ""
            if not path:
                path = d.get("file_path") or d.get("source_file") or ""
            if path:
                if not os.path.isabs(path):
                    path = os.path.join(root, path)
                path = os.path.normpath(path)
                if platform.system() == "Windows":
                    path = path.lower()
        except Exception:
            pass
        return path

    # 先過濾相似度不符合門檻的文檔
    filtered_docs = []
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        
        # 檢查相似度門檻
        doc_distance = doc.get("distance", float('inf'))
        if doc_distance > document_threshold:
            print(f"📄 過濾文檔：距離 {doc_distance:.3f} > 門檻 {document_threshold}")
            continue
            
        filtered_docs.append(doc)
    
    # 按相似度排序（距離越小越前面）
    sorted_docs = sorted(filtered_docs, key=lambda x: x.get("distance", float('inf')))
    
    # 去重處理
    seen: Dict[str, Dict[str, Any]] = {}
    for doc in sorted_docs:
        key = canonical_path(doc)
        if not key:
            title = (doc.get("title") or "").strip().lower()
            content_preview = (doc.get("content") or "")[:100].strip().lower()
            key = f"{title}|{content_preview}"
        if key not in seen:
            seen[key] = doc

    result = list(seen.values())
    print(f"📄 過濾後文檔數量：{len(result)}（門檻: {document_threshold}）")
    return result


def display_message(message: Dict[str, Any]) -> None:
    """渲染單條訊息（支援圖片與文檔引用，自動格式化 XML）。"""
    is_user = message.get("role") == "user"
    content = message.get("content", "")
    ts = message.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M")

    with st.chat_message("user" if is_user else "assistant"):
        # 處理包含 Markdown 和 XML 的複合式內容
        # 查找由 spc_tool.py 生成的特定 XML 區塊標記
        xml_section_pattern = r'(### (?:📥|📤) (?:輸入|輸出)交易 XML\s*\n<pre><code class="language-xml">.*?</pre>)'
        
        parts = re.split(xml_section_pattern, content, flags=re.DOTALL)
        
        for part in parts:
            if not part.strip():
                continue

            # 檢查該部分是否為我們定義的 XML 區塊
            if re.match(r'### (?:📥|📤) (?:輸入|輸出)交易 XML', part):
                # 提取標題和 XML 內容
                title_match = re.match(r'(### .*? XML)', part, re.DOTALL)
                title = title_match.group(1) if title_match else "**📄 XML 內容：**"
                
                xml_content_match = re.search(r'<pre><code class="language-xml">\n(.*?)\n</code></pre>', part, re.DOTALL)
                
                st.markdown(title)
                if xml_content_match:
                    xml_content = xml_content_match.group(1)
                    # 格式化 XML
                    formatted_xml = format_xml_content(xml_content)
                    st.code(formatted_xml, language="xml")
                else:
                    # 如果沒有匹配到，顯示原始部分
                    st.text(part)
            else:
                # 對於非 XML 的部分，使用 st.markdown 正常渲染
                st.markdown(part)
        
        st.caption(f"⏰ {ts}")

        if not is_user:
            images = message.get("images") or []
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


            docs = message.get("source_documents") or []
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
                                if isinstance(doc.get("metadata"), dict):
                                    file_path = doc["metadata"].get("file_path", "")
                                elif "file_path" in doc:
                                    file_path = doc.get("file_path") or ""

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
