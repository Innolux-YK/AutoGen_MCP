"""
LangChain 智能代理 - 使用 LLM 自動規劃和執行任務
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import sys
import os

# 將專案根目錄加入 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from tools.tool_manager import ToolManager

class LangChainAgent:
    """基於 LangChain 的智能代理"""
    
    def __init__(self):
        self.tool_manager = ToolManager()
        self.llm = ChatOpenAI(
            api_key=config.API_KEY,
            base_url=config.get_api_url(),
            model=getattr(config, "INNOAI_DEFAULT_MODEL", "gpt-4"),
            temperature=0.1,
            max_tokens=4000  # 增加最大輸出長度
        )
        self.tools = self.tool_manager.get_langchain_tools()
        self.agent_executor = self._create_agent()
        print("🤖 LangChain 智能代理初始化完成")
    
    def _create_tools(self) -> List:
        """創建工具列表 (已由 ToolManager 處理)"""
        return self.tool_manager.get_langchain_tools()
    
    def _create_agent(self) -> AgentExecutor:
        """創建 LangChain Agent"""
        
        # 自定義 prompt 模板 - 使用繁體中文，並加強格式約束
        template = """You are a helpful assistant. Answer the following questions as best you can. You have access to the following tools:

{tools}

IMPORTANT: You MUST follow this exact format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

CRITICAL FORMATTING RULES:
1. Always include "Action:" before specifying the action
2. Always include "Action Input:" before providing the input
3. Always include "Thought:" before your reasoning
4. Always include "Final Answer:" before your conclusion
5. Never skip any of these formatting elements

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        
        # 創建 ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            max_execution_time=None
            # 移除 early_stopping_method 參數，避免模型兼容性問題
        )
    
    def solve_problem(self, query: str, llm_model: str = None) -> Dict[str, Any]:
        """
        使用 LLM 自動規劃並解決問題
        
        Args:
            query: 用戶問題
            llm_model: 指定使用的LLM模型
            
        Returns:
            解決方案和執行過程
        """
        try:
            # 如果指定了模型，臨時更新LLM
            original_model = self.llm.model_name
            original_llm = self.llm  # 保存原始LLM引用
            
            if llm_model and llm_model != original_model:
                print(f"🔄 切換模型: {original_model} → {llm_model}")
                # 創建新的LLM實例而不是修改現有的
                temp_llm = ChatOpenAI(
                    api_key=config.API_KEY,
                    base_url=config.get_api_url(llm_model),
                    model=llm_model,
                    temperature=0.1,
                    max_tokens=4000
                )
                # 暫時替換
                self.llm = temp_llm
                # 重新創建agent executor
                self.agent_executor = self._create_agent()
            
            print(f"🤖 LangChain Agent 處理問題 (模型: {self.llm.model_name}): {query}")
            
            # 特殊處理 SPC 查詢 - 直接調用工具避免截斷
            if "SPC" in query and ("進CHART" in query or "沒有進" in query or "CHART" in query):
                print("🔍 檢測到 SPC 查詢，直接使用工具避免輸出截斷")
                spc_result = self.tool_manager.execute_tool("spc_query", query)
                current_model = llm_model or self.llm.model_name
                model_prefix = f"**{current_model.upper()}**: "
                return {
                    "answer": model_prefix + spc_result,
                    "confidence": 0.9,
                    "source": "direct_spc_tool",
                    "execution_steps": [{"tool": "spc_query", "input": query, "output": spc_result}],
                    "total_steps": 1,
                    "model_used": current_model
                }
            
            # 執行 agent
            result = self.agent_executor.invoke({"input": query})
            
            # 提取執行步驟
            steps = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    action, observation = step
                    steps.append({
                        "tool": action.tool,
                        "input": action.tool_input,
                        "output": observation
                    })
            
            # 檢查是否有 SPC 工具被調用且輸出被截斷
            for step in steps:
                if step["tool"] == "spc_query":
                    full_output = step["output"]
                    # 檢查是否包含所有四個廠別的範例
                    if "TFT6" in full_output and ("CF6" not in full_output or "LCD6" not in full_output or "USL" not in full_output):
                        print("⚠️ 檢測到 SPC 工具輸出被截斷，使用完整輸出")
                        complete_output = self.tool_manager.execute_tool("spc_query", query)
                        current_model = llm_model or self.llm.model_name
                        model_prefix = f"**{current_model.upper()}**: "
                        return {
                            "answer": model_prefix + complete_output,
                            "confidence": 0.9,
                            "source": "langchain_agent_fixed",
                            "execution_steps": steps,
                            "total_steps": len(steps),
                            "model_used": current_model
                        }
                    # 如果工具輸出完整，但 LLM 回答簡化了，直接返回工具輸出
                    elif "TFT6" in full_output and "CF6" in full_output and "LCD6" in full_output and "USL" in full_output:
                        if len(result["output"]) < len(full_output) * 0.7:  # 如果 LLM 回答明顯比工具輸出短
                            print("⚠️ 檢測到 LLM 簡化了 SPC 工具輸出，返回完整工具回應")
                            current_model = llm_model or self.llm.model_name
                            model_prefix = f"**{current_model.upper()}**: "
                            return {
                                "answer": model_prefix + full_output,
                                "confidence": 0.9,
                                "source": "langchain_agent_full_output",
                                "execution_steps": steps,
                                "total_steps": len(steps),
                                "model_used": current_model
                            }
            
            current_model = self.llm.model_name
            
            # 構建帶模型名稱的回答
            model_prefix = f"**{current_model.upper()}**: "
            final_answer = model_prefix + result["output"]
            
            # 恢復原始模型（如果有改變）
            if llm_model and llm_model != original_model:
                print(f"🔄 恢復模型: {llm_model} → {original_model}")
                self.llm = original_llm
                self.agent_executor = self._create_agent()
            
            return {
                "answer": final_answer,
                "confidence": 0.8,
                "source": "langchain_agent",
                "execution_steps": steps,
                "total_steps": len(steps),
                "model_used": current_model
            }
            
        except Exception as e:
            error_str = str(e)
            print(f"❌ LangChain Agent 執行錯誤: {error_str}")
            
            # 檢查是否為 API 相關錯誤，提供更明確的錯誤訊息
            if "429" in error_str or "超過使用者每日最大使用量" in error_str:
                error_message = "🚫 API 使用量已達每日限制，請稍後再試或切換其他模型。"
            elif "401" in error_str or "Unauthorized" in error_str:
                error_message = "🔑 API 金鑰認證失敗，請檢查設定。"
            elif "403" in error_str or "Forbidden" in error_str:
                error_message = "⛔ API 權限不足，請檢查 API 金鑰權限。"
            elif "timeout" in error_str.lower() or "超時" in error_str:
                error_message = "⏰ API 請求超時，請檢查網路連線或稍後再試。"
            elif "connection" in error_str.lower() or "連線" in error_str:
                error_message = "🌐 網路連線問題，請檢查網路狀態。"
            else:
                # 降級到簡單回應
                fallback_response = self._fallback_response(query)
                return {
                    "answer": fallback_response,
                    "confidence": 0.3,
                    "source": "langchain_agent_fallback",
                    "execution_steps": [],
                    "error": error_str
                }
            
            return {
                "answer": error_message,
                "confidence": 0.0,
                "source": "langchain_agent_error",
                "execution_steps": [],
                "error": error_str
            }
    
    def _fallback_response(self, query: str) -> str:
        """當 LangChain Agent 失敗時的降級回應"""
        # 使用工具管理器執行工具
        if any(keyword in query for keyword in ["計算", "加", "減", "乘", "除", "+", "-", "*", "/"]):
            return self.tool_manager.execute_tool("calculation", query)
        elif any(keyword in query for keyword in ["時間", "幾點", "現在"]):
            return self.tool_manager.execute_tool("current_time", query)
        elif any(keyword in query for keyword in ["SPC"]):
            return self.tool_manager.execute_tool("spc_query", query)
        elif any(keyword in query for keyword in ["EDC"]) and any(keyword in query for keyword in ["格式", "XML"]):
            return self.tool_manager.execute_tool("edc_format_check", query)
        elif any(keyword in query for keyword in ["EDC"]):
            return self.tool_manager.execute_tool("edc_query", query)
        elif any(keyword in query for keyword in ["IP", "設定", "機台"]):
            return self.tool_manager.execute_tool("ip_edc_config_check", query)
        else:
            return f"⚠️ 抱歉，我無法處理這個問題：「{query}」\n\n可以嘗試：\n• 使用更具體的描述\n• 檢查是否涉及計算、時間、SPC、EDC 或 IP 設定相關問題\n• 或切換其他可用的模型"
    
    def get_tool_info(self) -> Dict[str, Any]:
        """獲取工具資訊"""
        return self.tool_manager.get_tool_info()
    
    def list_available_tools(self) -> List[str]:
        """列出可用工具"""
        return self.tool_manager.list_tools()
