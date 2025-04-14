from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool 
from langchain_openai import ChatOpenAI 
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage,SystemMessage 
import json 
import re

IMAGE_TEMPLATE_SYS_FILE = "prompts/ImageParser_system_prompt_v2.txt"


def parse_json_response(response):
    try:
        json_match = re.search(r'```(?:json)?\s*(.*?)```', response, re.DOTALL)
        if json_match:
            content = json_match.group(1).strip()
            return json.loads(content)
        else:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                print("响应解析失败，请检查prompt")
                return None
    except json.JSONDecodeError:
        print("响应解析失败，请检查prompt")
    return None

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
        system_prompt = PromptTemplate.from_file(IMAGE_TEMPLATE_SYS_FILE,encoding="utf-8")

        # 用户提示，要求模型解析当前图片
        user_prompt = "请解析这张图表图片，提取标题、图表类型和相关数据信息。"

        messages = [
            SystemMessage(content=system_prompt.template),
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
            json_content = parse_json_response(response.content)
            if json_content:
                return json.dumps(json_content)
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