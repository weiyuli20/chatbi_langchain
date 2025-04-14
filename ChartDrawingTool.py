from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool 
from langchain_openai import ChatOpenAI 
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage,SystemMessage 
import json 
import re
from pydantic import BaseModel,Field
from typing import Type


CHART_TEMPLATE_SYS_FILE = "prompts/chart_drawing_prompt.txt"

class ChartDrawingInput(BaseModel):  
    chart_data_json: dict = Field(...,description="json格式的数据")  
    target_type: str = Field(...,description="目标图表类型") 

class ChartDrawingTool(BaseTool):
    name: str = "chart_drawing"
    description: str  = "根据解析出的 JSON 数据和目标图表类型target_type，调用大模型生成绘图代码并绘制图表。入参为两个,json格式的数据和目标图表类型（如 bar、line、pie,scatter等）"
    args_schema: Type[BaseModel] = ChartDrawingInput

    def _run(self, chart_data_json: dict, target_type: str):
        # 验证输入
        self._validate_input(chart_data_json, target_type)
        # 调用大模型生成绘图代码
        code = self._generate_drawing_code(chart_data_json, target_type)
    
        # 执行安全代码并获取绘图结果
        return code

    def _validate_input(self, chart_data_json, target_type):
        # 验证目标类型是否合法
        valid_types = ["bar", "line", "pie", "scatter"]
        if target_type not in valid_types:
            raise ValueError(f"无效的目标图表类型。支持的类型有：{', '.join(valid_types)}")
        # 验证 JSON 数据格式
        # try:
        #     json.loads(chart_data_json)
        # except json.JSONDecodeError:
        #     raise ValueError("输入的 JSON 数据格式不正确。")

    def _generate_drawing_code(self, chart_data_json, target_type):
        model = ChatOpenAI(
            openai_api_base="https://api.siliconflow.cn/v1/",
            openai_api_key="sk-pieicwwfnoastulaxwytnemrokzhooqsziombojeqcyhzwbu",
            model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
            temperature=0.2
        )
        # 系统提示，指导大模型生成安全的绘图代码
        system_prompt = PromptTemplate.from_file(CHART_TEMPLATE_SYS_FILE,encoding="utf-8")
        user_prompt = f"根据以下图表数据绘制 {target_type} 图表：{chart_data_json}"
        messages = [
            SystemMessage(content=system_prompt.template),
            HumanMessage(content=user_prompt)
        ]
        response = model.invoke(messages)
        return response.content

    def _execute_code(self, code):
        try:
            # 定义一个局部命名空间来执行代码
            namespace = {}
            exec(code, namespace)
            # 获取生成的 HTML 代码
            html_code = namespace.get('chart_html')
            if not html_code:
                raise ValueError("代码执行后未正确返回图表的 HTML 代码。")
            return {"html_code": html_code}
        except Exception as e:
            raise ValueError(f"执行过程中出现错误：{str(e)}")