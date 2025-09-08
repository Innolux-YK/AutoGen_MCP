"""
AI助手新版啟動文件 - 使用 st.navigation
運行命令: streamlit run frontend/main_app.py
"""

import os
import sys
import subprocess
import socket

def get_local_ip():
    """獲取本機 IP 地址"""
    try:
        # 連接到一個遠程地址來獲取本機 IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    """啟動新版 AI助手應用"""
    
    # 獲取前端目錄路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(current_dir, "frontend")
    main_app_path = os.path.join(frontend_dir, "main_app.py")
    
    # 檢查文件是否存在
    if not os.path.exists(main_app_path):
        print(f"❌ 找不到主應用文件: {main_app_path}")
        return
    
    # 獲取本機 IP
    local_ip = get_local_ip()
    port = "8505"  # 改用 8505 端口避免衝突
    
    print("🚀 啟動 AI助手 (新版) ...")
    print(f"📂 應用路徑: {main_app_path}")
    print("🌐 應用啟動後可透過以下網址存取:")
    print(f"   📍 本地存取: http://127.0.0.1:{port}")
    print(f"   🌍 網路存取: http://{local_ip}:{port}")
    print("⏳ 請稍候，正在啟動...")
    
    try:
        # 使用 subprocess 啟動 streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            main_app_path,
            "--server.address", "0.0.0.0",  # 允許所有網路介面存取
            "--server.port", port,
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false",
            "--browser.serverAddress", local_ip  # 設定瀏覽器開啟的地址
        ], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 啟動失敗: {e}")
        print("💡 請確保已安裝 streamlit: pip install streamlit")
    except KeyboardInterrupt:
        print("\n👋 AI助手已停止運行")
    except Exception as e:
        print(f"❌ 未知錯誤: {e}")

if __name__ == "__main__":
    main()
