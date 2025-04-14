from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.tools import Tool, BaseTool
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from fastapi import FastAPI, UploadFile, HTTPException
import base64
import json

# ======================
# 配置常量
# ======================
ALLOWED_IMAGE_TYPES = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
DEFAULT_LLM_MODEL = "gpt-3.5-turbo"

# ======================
# 工具定义（带参数校验）
# ======================
class ImageParserTool(BaseTool):
    name = "image_parser"
    description = (
        "解析图表/表格图片，提取结构化数据（返回标准JSON格式）。\n"
        "入参：图片Base64编码字符串（必填）\n"
        "输出：包含图表标题、类型、坐标轴数据的JSON"
    )
    
    def _run(self, image_base64: str):
        # 这里需替换为真实图片解析逻辑（如OCR+图表识别）
        # 示例返回柱状图模拟数据
        return json.dumps({
            "title": "2023年季度销售额",
            "type": "bar",
            "x_axis": ["Q1", "Q2", "Q3", "Q4"],
            "y_values": [300, 450, 600, 500]
        })

class ChartConverterTool(BaseTool):
    name = "chart_converter"
    description = (
        "将图表转换为指定类型（支持line/bar/pie/scatter）。\n"
        "入参：\n"
        "  raw_data: 原始图表数据JSON字符串（必填）\n"
        "  target_type: 目标图表类型（必填，小写英文）"
    )
    
    def _run(self, raw_data: str, target_type: str):
        # 这里需实现实际转换逻辑（如使用Plotly重构数据）
        return f"图表转换成功：{target_type}，原始数据：{raw_data}"

class ReportGeneratorTool(BaseTool):
    name = "report_generator"
    description = (
        "根据图表数据生成分析报告（支持PDF/Markdown）。\n"
        "入参：\n"
        "  chart_data: 图表数据JSON字符串（必填）\n"
        "  theme: 报告主题（必填，如'年度销售总结'）"
    )
    
    def _run(self, chart_data: str, theme: str):
        # 这里需实现实际报告生成逻辑（如使用ReportLab）
        return f"报告生成成功：{theme}，包含数据：{chart_data}"

# ======================
# Agent核心配置
# ======================
def create_agent():
    tools = [ImageParserTool(), ChartConverterTool(), ReportGeneratorTool()]
    
    # 自定义多模态交互Prompt
    prompt_template = PromptTemplate(
        input_variables=["input", "memory", "agent_scratchpad"],
        template="""你是智能BI分析专家，能处理以下任务：
1. 解析图表图片（使用`image_parser`，入参为图片Base64）
2. 转换图表类型（使用`chart_converter`，需原始数据和目标类型）
3. 生成分析报告（使用`report_generator`，需图表数据和主题）

当前对话历史：{memory}
用户需求：{input}
{agent_scratchpad}"""
    )
    
    llm = OpenAI(
        temperature=0.6,
        model_name=DEFAULT_LLM_MODEL,
        verbose=True
    )
    
    memory = ConversationBufferMemory(memory_key="memory")
    agent = ZeroShotAgent(
        llm=llm,
        tools=tools,
        prompt=prompt_template,
        verbose=True
    )
    
    return AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True
    )

# ======================
# FastAPI服务接口
# ======================
app = FastAPI(
    title="智能BI Agent Service",
    description="处理图表图片的智能分析服务",
    version="1.0.1"
)

# 初始化全局Agent
agent_executor = create_agent()

@app.post("/analyze_chart")
async def analyze_chart(
    user_question: str,
    chart_image: UploadFile
):
    # 文件类型校验
    if not chart_image.filename.lower().endswith(ALLOWED_IMAGE_TYPES):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，允许：{', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # 文件大小校验
    if chart_image.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（最大{MAX_FILE_SIZE/1024/1024:.1f}MB）"
        )
    
    try:
        # 读取并编码图片
        image_bytes = await chart_image.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        
        # 构造Agent输入
        input_text = f"用户问题：{user_question}，图片Base64：{image_b64}"
        
        # 执行Agent流程
        result = agent_executor.run(input_text)
        return {"status": "success", "analysis_result": result}
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"数据解析错误：{str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"内部处理错误：{str(e)}"
        )

# ======================
# 服务启动入口
# ======================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True  # 开发环境启用热重载
    )