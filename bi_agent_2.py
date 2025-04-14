from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool, Tool
from langchain.llms import OpenAI
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from fastapi import FastAPI, UploadFile, HTTPException,Body
import base64
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
from typing import Optional

from langgraph.prebuilt import create_react_agent

# ======================
# 工具定义（继承BaseTool）
# ======================

from langchain.schema import SystemMessage, HumanMessage
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool
import json


class ImageParserTool(BaseTool):
    name: str = "image_parser"
    description: str = "解析图表/表格图片，返回包含标题、坐标轴数据的JSON。入参为图片Base64编码字符串"

    def _run(self, image_base64: str):
        # 模拟图片解析结果（需替换为真实OCR+图表识别逻辑）
        model = ChatOpenAI(
            openai_api_base="https://api.siliconflow.cn/v1/",
            openai_api_key="sk-pieicwwfnoastulaxwytnemrokzhooqsziombojeqcyhzwbu",  # app_key
            model_name="Pro/Qwen/Qwen2.5-VL-7B-Instruct",  # 模型名称
            temperature=0,
        )

        # 系统提示，告知模型要做的事情
        system_prompt = """你是一个专业且细致的图表分析助手，能够精准识别各类图表中的关键信息。当接收到一张图表图片时，你需要根据图表的类型，提取出相应的关键信息，并以 JSON 格式返回。以下是不同类型图表需要关注的信息以及最终返回的 JSON 格式示例：

### 通用信息
所有类型的图表都需要提取以下信息：
- `title`：图表的标题，如果图表中没有明确标题，则为空字符串。
- `chart_type`：图表的类型，可取值为 "bar"（柱状图）、"line"（折线图）、"pie"（饼图）、"scatter"（散点图）等。

### 不同类型图表的特定信息

#### 柱状图和折线图
- `x_axis`：
  - `label`：x 轴的标签，如果没有则为空字符串。
  - `ticks`：x 轴的刻度值列表，如果没有则为空列表。
- `y_axis`：
  - `label`：y 轴的标签，如果没有则为空字符串。
  - `ticks`：y 轴的刻度值列表，如果没有则为空列表。
- `data_series`：
  - 每个数据系列包含 `name`（系列名称，如果没有则为空字符串）和 `values`（对应 x 轴刻度的数值列表）。

#### 饼图
- `slices`：
  - 每个切片包含 `name`（切片名称，如果没有则为空字符串）和 `value`（切片的数值），还可以包含 `percentage`（该切片占总体的百分比，保留两位小数）。

#### 散点图
- `x_axis`：
  - `label`：x 轴的标签，如果没有则为空字符串。
- `y_axis`：
  - `label`：y 轴的标签，如果没有则为空字符串。
- `points`：
  - 每个点包含 `x`（x 坐标值）和 `y`（y 坐标值）。

### JSON 格式示例

#### 柱状图/折线图
{
    "title": "月度销售额柱状图",
    "chart_type": "bar",
    "x_axis": {
        "label": "月份",
        "ticks": ["一月", "二月", "三月"]
    },
    "y_axis": {
        "label": "销售额（万元）",
        "ticks": ["0", "100", "200"]
    },
    "data_series": [
        {
            "name": "产品 A",
            "values": [120, 150, 180]
        },
        {
            "name": "产品 B",
            "values": [80, 90, 100]
        }
    ]
}

#### 饼图
{
    "title": "市场份额饼图",
    "chart_type": "pie",
    "slices": [
        {
            "name": "品牌 A",
            "value": 30,
            "percentage": 30.00
        },
        {
            "name": "品牌 B",
            "value": 50,
            "percentage": 50.00
        },
        {
            "name": "品牌 C",
            "value": 20,
            "percentage": 20.00
        }
    ]
}

#### 散点图
{
    "title": "身高与体重散点图",
    "chart_type": "scatter",
    "x_axis": {
        "label": "身高（cm）"
    },
    "y_axis": {
        "label": "体重（kg）"
    },
    "points": [
        {
            "x": 160,
            "y": 50
        },
        {
            "x": 170,
            "y": 60
        },
        {
            "x": 180,
            "y": 70
        }
    ]
}

如果某些信息无法从图表中明确获取，对应字段可以为空字符串或空列表。"""

        # 用户提示，要求模型解析当前图片
        user_prompt = "请解析这张图表图片，提取标题、图表类型和相关数据信息。"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=[
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ]
            )
        ]

        # 调用模型
        response = model.invoke(messages)

        # 解析模型返回的数据
        try:
            parsed_data = json.loads(response.content)
            return json.dumps(parsed_data)
        except json.JSONDecodeError:
            print("模型返回结果不是有效的JSON格式。")
            return json.dumps({
                "title": "",
                "chart_type": "",
                "x_axis": {
                    "label": "",
                    "ticks": []
                },
                "y_axis": {
                    "label": "",
                    "ticks": []
                },
                "data_series": [],
                "slices": [],
                "points": []
            })

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("暂时不支持异步调用")



# 定义危险函数列表，用于过滤不安全代码
DANGEROUS_FUNCTIONS = [
    "os.", "subprocess.", "open(", "eval(", "exec(",
    "pickle.", "urllib.", "socket.", "shutil."
]


class ChartDrawingTool(BaseTool):
    name: str = "chart_drawing"
    description: str  = "根据解析出的 JSON 数据和目标图表类型，调用大模型生成 pyecharts 绘图代码并绘制图表。入参为图表数据 JSON 字符串和目标图表类型（如 bar、line、pie,scatter等）"

    def _run(self, chart_data_json: str, target_type: str):
        # 验证输入
        self._validate_input(chart_data_json, target_type)
        # 调用大模型生成绘图代码
        code = self._generate_drawing_code(chart_data_json, target_type)
        # 过滤危险代码
        safe_code = self._filter_dangerous_code(code)
        # 执行安全代码并获取绘图结果
        result = self._execute_code(safe_code)
        return result

    def _validate_input(self, chart_data_json, target_type):
        # 验证目标类型是否合法
        valid_types = ["bar", "line", "pie", "scatter"]
        if target_type not in valid_types:
            raise ValueError(f"无效的目标图表类型。支持的类型有：{', '.join(valid_types)}")
        # 验证 JSON 数据格式
        try:
            json.loads(chart_data_json)
        except json.JSONDecodeError:
            raise ValueError("输入的 JSON 数据格式不正确。")

    def _generate_drawing_code(self, chart_data_json, target_type):
        model = ChatOpenAI(
            openai_api_base="https://api.siliconflow.cn/v1/",
            openai_api_key="sk-pieicwwfnoastulaxwytnemrokzhooqsziombojeqcyhzwbu",
            model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
            temperature=0.2
        )
        # 系统提示，指导大模型生成安全的绘图代码
        system_prompt = f"""你是一个专业的绘图助手，仅使用 Python 的 pyecharts 库根据提供的图表数据和目标图表类型生成绘图代码。
代码应包含必要的导入语句，仅使用 pyecharts 进行绘图操作，不允许使用任何文件操作、网络请求、系统命令执行等危险操作。
代码最后需要返回图表的 HTML 代码字符串，不要有任何额外的解释信息，直接返回代码。目标图表类型映射如下：
"bar": "Bar",
"line": "Line",
"pie": "Pie",
"scatter": "Scatter"
"""
        user_prompt = f"根据以下图表数据绘制 {target_type} 图表：{chart_data_json}"
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = model.invoke(messages)
        return response.content

    def _filter_dangerous_code(self, code):
        for func in DANGEROUS_FUNCTIONS:
            if re.search(re.escape(func), code):
                raise ValueError(f"检测到危险代码：{func}。不允许执行包含此代码的绘图脚本。")
        return code

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



# ======================
# FastAPI服务配置
# ======================
app = FastAPI(
    title="智能BI Agent Service",
    description="处理图表图片的智能分析服务",
    version="1.0.1"
)

llm = ChatOpenAI(
    openai_api_base="https://api.siliconflow.cn/v1/",
    openai_api_key= "sk-pieicwwfnoastulaxwytnemrokzhooqsziombojeqcyhzwbu",  # app_key
    # model_name="Pro/Qwen/Qwen2.5-VL-7B-Instruct",   # 模型名称
    model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    temperature=0,
)

tools = [
    ImageParserTool(),
    ChartDrawingTool(),
]

# agent= create_agent(llm)  # 初始化全局Agent
agent_executor = create_react_agent(llm, tools)





# 定义请求体的数据模型
class AnalyzeRequest(BaseModel):
    user_query: str
    user_id: str = "default_user"

@app.post("/analyze")
async def analyze_image(
    request: AnalyzeRequest = Body(...),
    chart_image: Optional[UploadFile] = None
):
    user_query = request.user_query
    user_id = request.user_id

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
            # 这里假设存在一个全局的字典来存储用户的解析数据，你需要根据实际情况定义
            user_parsed_image_data[user_id] = parsed_data
        except Exception as e:
            raise HTTPException(500, f"解析图片失败: {str(e)}")
    else:
        if user_id not in user_parsed_image_data:
            raise HTTPException(400, "首次请求需要上传图片")
        parsed_data = user_parsed_image_data[user_id]

    # 构造输入（包含解析后的数据和用户问题）
    input_text = f"用户查询：{user_query}，图片解析数据：{parsed_data}"

    try:
        # 执行 Agent 流程
        result = agent_executor.invoke(input_text)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(500, f"处理失败：{str(e)}")


# 启动服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True  # 开发环境启用热重载
    )
    
