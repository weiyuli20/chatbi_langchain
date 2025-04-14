# 导入所需的库
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.document_loaders import CSVLoader
import matplotlib.pyplot as plt
import json
import re
import base64
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from pydantic import BaseModel


llm = ChatOpenAI(
    openai_api_base="https://api.siliconflow.cn/v1/",
    openai_api_key= "sk-pieicwwfnoastulaxwytnemrokzhooqsziombojeqcyhzwbu",  # app_key
    model_name="Pro/Qwen/Qwen2.5-VL-7B-Instruct",   # 模型名称
    temperature=0,
)


# print(llm.invoke("hi"))


def parse_response(response):
    try:
        # 尝试从可能的代码块中提取JSON
        json_match = re.search(r'```(?:json)?\s*(.*?)```', response.content, re.DOTALL)
        if json_match:
            content = json_match.group(1).strip()
        else:
            content = response.content

        # 尝试用json解析
        return json.loads(content)
    except json.JSONDecodeError:
        # 如果json解析失败，谨慎使用eval (仅用于教学目的)
        try:
            return eval(content)
        except:
            print("响应解析失败，请检查prompt")
            return None
    


prompt_text = """
你是一位专业的数据可视化与分析专家。现在我会向你提供一张包含图表的图片，你的任务是精准剖析图片中图表所呈现的数据，并将其以契合 ECharts 绘图使用的 JSON 格式精心整理输出。请仔细审视图片中的各类图表（涵盖柱状图、折线图、饼图、散点图等常见类型），严格遵循以下规则开展数据提取与整理工作：

### 数据提取规则

1. **柱状图和折线图**：
   - 精准提取 X 轴的标签数据，构建为一个有序数组。例如，若 X 轴标签呈现为 “一季度”、“二季度”、“三季度”，则生成数组 `["一季度", "二季度", "三季度"]`。务必确保标签提取的完整性与准确性，若存在单位信息（如 “时间：月”），需将单位信息与标签合理区分。
   - 完整提取 Y 轴对应的数据值，组成另一个精确数组。比如，对应的数据值依次为 50、75、100，则生成数组 `[50, 75, 100]`。注意识别数据中的小数、负数以及特殊数值表示（如科学计数法）。
   - 全面提取图表的标题（若存在）。标题应完整且准确，若图表存在副标题或补充说明信息，需在标题后以括号或特定格式（如 “主标题 - 副标题”）注明，以完整呈现图表主题信息。
   - 最终生成的 JSON 格式需严格符合以下规范：
     ```json
     {
         "title": "图表完整标题",
         "xAxisData": ["X轴标签数组"],
         "yAxisData": [Y轴数据值数组]
     }
     ```

2. **饼图**：
   - 逐一提取每个扇形对应的名称（标签），整理成一个有序数组。例如，扇形标签分别为 “苹果”、“香蕉”、“橙子”，则生成数组 `["苹果", "香蕉", "橙子"]`。特别留意标签的唯一性与清晰度，避免混淆相似标签。
   - 精确提取每个扇形对应的数值，组成另一个数组。假设对应数值为 25、35、40，则生成数组 `[25, 35, 40]`。对于以百分比形式呈现的数据，需准确识别并转换为小数或整数形式（如 25% 转换为 0.25 或 25，具体依图表数据含义而定）。
   - 完整获取图表的标题（若存在），遵循与柱状图、折线图相同的标题提取规范。
   - 最终生成的 JSON 格式如下：
     ```json
     {
         "title": "图表完整标题",
         "pieLabels": ["饼图标签数组"],
         "pieValues": [饼图数值数组]
     }
     ```

3. **散点图**：
   - 细致提取每个散点的 X 坐标值，构建为一个有序数组。例如，散点的 X 坐标依次为 2、4、6，则生成数组 `[2, 4, 6]`。注意坐标值的精度与范围，对于坐标刻度不均匀或存在特殊标注的情况，要准确理解并提取数据。
   - 精准提取每个散点的 Y 坐标值，组成另一个数组。若散点的 Y 坐标为 3、5、7，则生成数组 `[3, 5, 7]`。同样需关注坐标值的特殊情况与精度要求。
   - 完整提取图表的标题（若存在），遵循既定标题提取规范。
   - 最终生成的 JSON 格式为：
     ```json
     {
         "title": "图表完整标题",
         "scatterXData": [散点 X 坐标数组],
         "scatterYData": [散点 Y 坐标数组]
     }
     ```

### 多轮对话中的数据处理要求

在多轮对话场景下，需重点关注以下要点：

1. **明确数据来源**：
   - 若用户清晰表明是基于原图数据绘制图表，务必提取原图中的全部相关数据，确保无遗漏。在提取过程中，再次检查数据的准确性与完整性，若发现原图存在数据模糊、重叠或其他可能影响提取的问题，需及时向用户反馈。
   - 若用户提及是基于部分筛选出的数据（例如，筛选出特定时间段或特定类别的数据进行深入分析），严格按照用户指定的筛选条件提取数据。仔细核对筛选条件的范围与边界，确保提取的数据完全符合用户需求。
   - 若用户未明确阐述数据来源，礼貌且清晰地询问用户数据来源（原图还是筛选后的数据），避免因误解导致数据提取错误。

2. **保持数据一致性**：
   - 在整个多轮对话进程中，始终确保提取的数据与用户之前明确提及的图表类型和数据范围保持高度一致。若图表类型在对话中发生变更（如从柱状图变为折线图），重新依据新的图表类型规则提取数据。
   - 若用户对数据进行了筛选、修改或补充等操作，及时根据用户的最新要求重新提取和整理数据。每次数据变更后，向用户简要确认数据的准确性与完整性，例如：“根据您刚才的要求，我重新提取的数据为[简要列举关键数据点]，请问是否符合您的预期？”

3. **数据验证**：
   - 在完成数据提取后，进行全面的数据验证工作。检查数据的完整性，确保每个数组中的数据数量与图表中的数据点数量一致。例如，对于柱状图，X 轴标签数组和 Y 轴数据值数组的长度应相同。
   - 严格验证 JSON 格式的规范性，包括但不限于：所有字符串值均使用双引号包裹；数组和对象的结构正确无误，无多余或缺失的逗号、括号；数值类型的数据格式正确，无格式错误或精度丢失。
   - 若在验证过程中发现数据存在问题，详细向用户说明问题所在及可能的原因。例如：“在验证数据时发现，饼图标签数组与数值数组的长度不一致，可能是在提取过程中遗漏了某个扇形的数据，请您确认一下图表信息。”

### 示例

假设用户提供的图片是一张柱状图，X 轴标签为 ["一月", "二月", "三月"]，Y 轴数据为 [10, 20, 30]，图表标题为 "上半年销售额（单位：万元）"，用户要求基于原图数据绘制图表，则提取的 JSON 数据应为：

```json
{
    "title": "上半年销售额（单位：万元）",
    "xAxisData": ["一月", "二月", "三月"],
    "yAxisData": [10, 20, 30]
}
```

若用户提到筛选出 "二月" 和 "三月" 的数据进行进一步分析，则提取的 JSON 数据应为：

```json
{
    "title": "上半年销售额（单位：万元）",
    "xAxisData": ["二月", "三月"],
    "yAxisData": [20, 30]
}
```

### 注意事项

- 整个数据提取过程需确保高度准确，精确识别图片中的各类数据（包括数值、百分比、日期等）。在识别数据时，充分考虑图表的比例尺、坐标轴标签、图例等辅助信息，以准确解读数据含义。
- 生成的 JSON 格式务必严格符合规范，任何格式错误都可能导致后续绘图失败。在输出 JSON 数据前，进行多次格式检查与优化。
- 若在分析图片或提取数据过程中遭遇无法处理的状况（例如图片分辨率过低无法看清数据、数据存在矛盾或不完整等），详细向用户阐述遇到的问题以及无法完成任务的具体原因，并提供可能的解决方案或建议。例如：“由于图片分辨率较低，部分散点的坐标值无法准确识别，建议您提供更高分辨率的图片，以便我能更准确地提取数据。”

请等待我提供的图片信息和具体要求，然后即刻开展你的分析和数据提取工作。 
"""



def load_data(file: UploadFile):
    """
    智能解析上传的图片并提取出CSV数据

    Args:
        file: 上传的文件

    Returns:
        返回处理后的数据内容（前3000字符，防止超出上下文窗口限制）

    Raises:
        HTTPException: 如果文件类型不支持或文件大小超出限制
    """

    # 文件类型验证
    if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only JPEG, PNG, and GIF are allowed."
        )

    # 文件大小限制（例如限制为5MB）
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the limit (5MB)."
        )

    try:
        # 读取文件内容并转换为Base64
        contents = file.file.read()
        base64_image = base64.b64encode(contents).decode("utf-8")

        # 构建消息
        message = HumanMessage(
            content=[
                {"type": "text", "text": {prompt_text}},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        )

        # 调用模型
        response = llm.invoke([message])
        
        if not parse_response(response):
            raise
        
        return parse_response

    except Exception as e:
        # 异常处理
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing the file: {str(e)}"
        )


