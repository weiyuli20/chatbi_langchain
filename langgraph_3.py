import json  
from typing import Type, TypedDict, Annotated,Optional  
import requests  
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage,SystemMessage  
from langchain_core.tools import BaseTool  
from langgraph.graph import add_messages, StateGraph, START, END  
from pydantic import BaseModel, Field  
from langchain_openai import ChatOpenAI 
from langchain_core.tools import tool 
import base64
from fastapi import FastAPI, UploadFile, HTTPException,Body,Form
import re
from langchain_core.prompts import PromptTemplate
from generate_image import GenerateImageTool
from ImageParserTool import ImageParserTool
from ChartDrawingTool import ChartDrawingTool

user_parsed_image_data={}
with open("1.png","rb") as f:
        contents = f.read()
        base64_image = base64.b64encode(contents).decode("utf-8")
user_parsed_image_data["1"] = base64_image
    

class State(TypedDict):  
    messages: Annotated[list, add_messages]  


class MutilplyInput(BaseModel):  
    arg1: int = Field(...,description="参数A")  
    arg2: int = Field(...,description="参数B") 


class Mutilply(BaseTool):  
    """  
    乘法运算  
    """    
    name: str = "进行乘法运算"  
    description: str = "进行乘法运算，计算两个数的乘法运算"  
    args_schema: Type[BaseModel] = MutilplyInput


    def _run(self, arg1,arg2):
        return  arg1 * arg2 


@tool
def get_image_content(user_id:str) -> str:
    '''
    返回用户的图片base64数据
    '''
    image_base64 = user_parsed_image_data[user_id]
    return image_base64



# 引入 create_react_agent 
from langgraph.prebuilt import create_react_agent

mutilply_tool = Mutilply()
gen_chart_tool = GenerateImageTool()
chart_tool =  ChartDrawingTool()



# tools = [mutilply_tool,get_image_content,image_parser_tool]  
tools = [mutilply_tool,chart_tool]

llm = ChatOpenAI(
    openai_api_base="https://api.siliconflow.cn/v1/",
    openai_api_key= "sk-pieicwwfnoastulaxwytnemrokzhooqsziombojeqcyhzwbu",  # app_key
    # model_name="Pro/Qwen/Qwen2.5-VL-7B-Instruct",   # 模型名称
    model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    # model_name = "Pro/deepseek-ai/DeepSeek-V3",
    temperature=0.5,
)


AGENT_TEMPLATE_FILE = "prompts\prompt_template_agent.txt"
agent_prompt = PromptTemplate.from_file(AGENT_TEMPLATE_FILE,encoding="utf-8")

agent = create_react_agent(llm, tools=tools,state_modifier =agent_prompt.template) 

app = FastAPI(
    title="智能BI Agent Service",
    description="处理图表图片的智能分析服务",
    version="1.0.1"
)

# 定义请求体的数据模型
class AnalyzeRequest(BaseModel):
    user_query: str
    user_id: str = "default_user"

@app.post("/analyze")
async def analyze_image(
    user_query: str = Form(...),
    user_id: str = Form(...),
    chart_image: Optional[UploadFile] = None
):
    try:
        if chart_image:
            # 文件校验
            if not chart_image.filename.lower().endswith(('.png', '.jpg')):
                raise HTTPException(400, "仅支持 PNG/JPG 图片")

            # 读取图片并编码
            try:
                image_bytes = await chart_image.read()
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            except Exception as e:
                raise HTTPException(500, f"读取图片失败: {str(e)}")

            # 解析图片
            try:
                parser = ImageParserTool()
                parsed_data = parser.run(image_b64)
                print("parsed_data:", parsed_data)
                # 这里假设存在一个全局的字典来存储用户的解析数据，你需要根据实际情况定义
                user_parsed_image_data[user_id] = parsed_data
            except Exception as e:
                raise HTTPException(500, f"解析图片失败: {str(e)}")
        else:
            if user_id not in user_parsed_image_data:
                raise HTTPException(400, "首次请求需要上传图片")
            parsed_data = user_parsed_image_data[user_id]
    except HTTPException as http_exc:
        # 捕获 HTTPException 并直接返回错误响应
        return {"status": "error", "message": http_exc.detail}
    except Exception as e:
        print(f"Error processing request: {e}")
        return {"status": "error", "message": str(e)}

    # 构造输入（包含解析后的数据和用户问题）
    input_text = f"用户查询：{user_query}，图片解析数据：{parsed_data}"
    print("开始处理用户查询")
    inputs = {"messages": [input_text]}

    try:
        # 执行 Agent 流程
        for result in agent.stream(inputs, stream_mode="values"):
            message = result.get("messages")[-1]
            if isinstance(message, tuple):
                print(message)
            else:
                message.pretty_print()
        # 这里可以根据实际情况返回合适的响应
        return {"status": "success", "message": "处理完成"}
    except Exception as e:
        return {"status": "error", "message": f"处理失败：{str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "langgraph_3:app",
        host="127.0.0.1",
        port=8002,
        log_level="info",
        reload=True,  # 开发环境启用热重载,
    )