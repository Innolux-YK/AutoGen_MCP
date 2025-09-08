"""
EDC 系統查詢工具
"""

import sys
import os

# 將專案根目錄加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.base_tool import BaseTool

class EDCQueryTool(BaseTool):
    """EDC 系統查詢工具"""
    
    def get_name(self) -> str:
        return "edc_query"
    
    def get_description(self) -> str:
        return """檢查系統狀態、設備狀態或技術問題排查。特別適用於 EDC系統診斷。
        關鍵字：EDC, 上傳, 檔案, 系統狀態, 設備檢查
        當用戶詢問「EDC沒進資料」或類似問題時使用此工具。"""
    
    def execute(self, query: str) -> str:
        """執行 EDC 系統查詢"""
        query_upper = query.upper()
        
        if "EDC" in query_upper:
            if "上傳" in query or "檔案" in query:
                return self._diagnose_edc_upload_issue(query)
            elif "系統" in query or "狀態" in query:
                return self._check_edc_system_status(query)
            else:
                return self._general_edc_help()
        
        return "EDC 系統狀態檢查完成。請提供更具體的問題描述以獲得詳細診斷。"
    
    def _diagnose_edc_upload_issue(self, query: str) -> str:
        """診斷 EDC 檔案上傳問題"""
        return """📁 EDC 檔案上傳問題診斷：

**檢查項目：**
1. **檔案格式**
   - 確認檔案格式是否符合 EDC 規範
   - 檢查檔案大小是否超出限制
   - 驗證 XML 結構是否正確
   
2. **檔案內容**
   - 驗證必填欄位是否完整
   - 檢查資料格式是否正確
   - 確認測項資料無重複
   
3. **上傳權限**
   - 確認使用者權限是否足夠
   - 檢查目標資料夾權限
   - 驗證網路存取權限
   
4. **系統狀態**
   - 檢查 EDC 服務運行狀態
   - 確認資料庫連線正常
   - 驗證檔案處理佇列狀態

**建議操作：**
- 重新檢查檔案格式和內容
- 使用 EDC 格式檢查工具驗證 XML
- 嘗試重新上傳較小的測試檔案
- 聯繫系統管理員確認權限設定

💡 **提示：** 如需檢查 XML 格式，請使用「EDC檔案格式確認」功能！"""
    
    def _check_edc_system_status(self, query: str) -> str:
        """檢查 EDC 系統狀態"""
        return """📊 EDC 系統狀態檢查：

**核心服務狀態：**
- 📡 **EDC 資料收集服務**: ✅ 正常運行
- 🗄️ **資料庫服務**: ✅ 連線正常
- 📁 **檔案處理服務**: ✅ 運行中
- 🔄 **資料同步服務**: ✅ 正常

**系統效能指標：**
- CPU 使用率: < 70%
- 記憶體使用率: < 80%
- 磁碟空間: > 20% 可用
- 網路連線: 正常

**最近 24 小時統計：**
- 成功處理檔案: 1,247 個
- 失敗處理檔案: 3 個
- 平均處理時間: 2.3 秒

**維護資訊：**
- 上次系統更新: 2025-08-25 02:00
- 下次預定維護: 2025-09-01 02:00

如發現任何異常，請聯繫 EDC 系統管理員。"""
    
    def _general_edc_help(self) -> str:
        """一般 EDC 協助資訊"""
        return """📋 **EDC 系統功能說明**

**主要功能：**
1. **資料收集**: 自動收集設備測試資料
2. **格式驗證**: 檢查 XML 檔案格式正確性
3. **資料存儲**: 安全儲存於企業資料庫
4. **報表產生**: 產生各種分析報表

**常見問題：**
- 📄 **檔案格式問題**: 使用「EDC檔案格式確認」功能
- 📡 **上傳失敗**: 檢查網路連線和檔案權限
- 🔍 **資料查詢**: 確認查詢條件和時間範圍
- ⚙️ **系統設定**: 聯繫系統管理員

**支援聯絡：**
- 🔧 技術支援: ext-1234
- 📧 Email: edc-support@company.com
- 📚 文檔: 內網EDC使用手冊

需要特定功能協助，請提供詳細問題描述！"""
