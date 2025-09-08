@echo off
chcp 65001 >nul
echo ========================================
echo   🤖 AI助手 - LINE風格聊天介面
echo ========================================
echo.

:: 激活虛擬環境
if exist ".venv\Scripts\activate.bat" (
    echo 🔄 激活Python虛擬環境...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  找不到虛擬環境，使用系統Python
)

:: 檢查並安裝依賴
echo 📦 檢查依賴套件...
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo 📥 安裝必要套件...
    pip install -r requirements.txt
)

:: 檢查知識庫
echo 🔍 檢查知識庫狀態...
if not exist "vector_db" (
    echo ⚠️  知識庫不存在，需要先建立
    set /p choice="是否現在建立知識庫？(y/n): "
    if /i "%choice%"=="y" (
        echo 🔄 正在建立知識庫...
        python document_processor.py
    ) else (
        echo ❌ 取消啟動
        pause
        exit /b 1
    )
)

:: 啟動 Streamlit 應用
echo.
echo 🚀 正在啟動AI助手...
echo 🌐 瀏覽器將自動開啟 http://localhost:8501
echo 📝 如果沒有自動開啟，請手動訪問上述網址
echo.
echo ⏹️  按 Ctrl+C 停止服務
echo ========================================

:: 使用 Python 啟動自定義啟動器
python start_chat_app.py

pause
