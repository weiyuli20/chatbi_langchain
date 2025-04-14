import pytest
from fastapi.testclient import TestClient
from bi_agent_2 import app, ImageParserTool, ChartDrawingTool
import json




def test_image_parser_tool():
    tool = ImageParserTool()
    # 使用模拟的图片Base64编码字符串
    with open("1.png","r") as f:
        contents = f.read()
    base64_image = base64.b64encode(contents).decode("utf-8")
    result = tool._run(base64_image)
    try:
        json.loads(result)
    except json.JSONDecodeError:
        pytest.fail("返回结果不是有效的JSON格式")


# def test_chart_drawing_tool():
#     tool = ChartDrawingTool()
#     mock_chart_data_json = '{"x_axis": ["A", "B"], "y_axis": [1, 2]}'
#     target_type = "bar"
#     try:
#         result = tool._run(mock_chart_data_json, target_type)
#         assert "html_code" in result
#     except ValueError as e:
#         pytest.fail(f"测试失败: {e}")


# def test_report_generator_tool():
#     tool = ReportGeneratorTool()
#     mock_chart_data = '{"data": "一些数据"}'
#     mock_theme = "测试报告"
#     result = tool._run(mock_chart_data, mock_theme)
#     assert "报告生成：测试报告" in result



# client = TestClient(app)

# def test_analyze_image_with_image():
#     with open('test_image.jpg', 'rb') as f:
#         response = client.post(
#             "/analyze",
#             data={
#                 "user_query": "解析这张图片",
#                 "user_id": "test_user"
#             },
#             files={"chart_image": f}
#         )
#     assert response.status_code == 200
#     assert "status" in response.json()
#     assert response.json()["status"] == "success"

# def test_analyze_image_without_image():
#     response = client.post(
#         "/analyze",
#         data={
#             "user_query": "根据之前解析的数据生成报告",
#             "user_id": "test_user"
#         }
#     )
#     if response.status_code == 400:
#         assert "首次请求需要上传图片" in response.text
#     else:
#         assert response.status_code == 200
#         assert "status" in response.json()
#         assert response.json()["status"] == "success"