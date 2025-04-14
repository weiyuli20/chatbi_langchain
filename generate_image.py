import json
import base64
import io
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from PIL import Image
from langchain_core.tools import BaseTool

class GenerateImageTool(BaseTool):
    name: str = "chart_drawing"
    description: str = "根据解析出的 JSON 数据和目标图表类型，使用 matplotlib 和 seaborn 绘制图表，并返回图像的 Base64 编码。"

    def _run(self, chart_data: dict, target_type: str) -> dict:
        # 验证输入
        self._validate_input(chart_data, target_type)
        # 转换数据
        data = self._convert_data(chart_data, target_type)
        # 绘制图表
        image_base64 = self._plot_chart(data)
        return {"image_base64": image_base64}

    def _validate_input(self, chart_data: dict, target_type: str):
        # 验证目标类型是否合法
        valid_types = ["bar", "line", "pie", "scatter"]
        if target_type not in valid_types:
            raise ValueError(f"无效的目标图表类型。支持的类型有：{', '.join(valid_types)}")

    def _convert_data(self, chart_data: dict, target_type: str) -> dict:
        # 根据目标类型转换数据
        if target_type == "bar":
            return self._convert_to_bar_data(chart_data)
        elif target_type == "line":
            return self._convert_to_line_data(chart_data)
        elif target_type == "pie":
            return self._convert_to_pie_data(chart_data)
        elif target_type == "scatter":
            return self._convert_to_scatter_data(chart_data)
        else:
            raise ValueError(f"不支持的目标图表类型: {target_type}")

    def _convert_to_bar_data(self, data: dict) -> dict:
        # 转换为柱状图数据
        return {
            "title": data.get("title", ""),
            "x_values": data.get("x_values", []),
            "y_values": data.get("y_values", []),
            "series_names": data.get("series_names", []),
            "data_points": data.get("data_points", []),
            "chart_type": "bar"
        }

    def _convert_to_line_data(self, data: dict) -> dict:
        # 转换为折线图数据
        return {
            "title": data.get("title", ""),
            "x_values": data.get("x_values", []),
            "y_values": data.get("y_values", []),
            "series_names": data.get("series_names", []),
            "data_points": data.get("data_points", []),
            "chart_type": "line"
        }

    def _convert_to_pie_data(self, data: dict) -> dict:
        # 转换为饼图数据
        return {
            "title": data.get("title", ""),
            "x_values": data.get("x_values", []),
            "y_values": data.get("y_values", []),
            "series_names": [],
            "data_points": data.get("data_points", []),
            "chart_type": "pie"
        }

    def _convert_to_scatter_data(self, data: dict) -> dict:
        # 转换为散点图数据
        return {
            "title": data.get("title", ""),
            "x_values": data.get("x_values", []),
            "y_values": data.get("y_values", []),
            "series_names": [],
            "data_points": data.get("data_points", []),
            "chart_type": "scatter"
        }

    def _plot_chart(self, data: dict) -> str:
        plt.figure(figsize=(10, 6))
        chart_type = data.get("chart_type", "bar")

        if chart_type == "bar":
            self._plot_bar_chart(data)
        elif chart_type == "line":
            self._plot_line_chart(data)
        elif chart_type == "pie":
            self._plot_pie_chart(data)
        elif chart_type == "scatter":
            self._plot_scatter_chart(data)
        else:
            raise ValueError(f"不支持的图表类型: {chart_type}")

        # 将图表转换为 Base64 编码
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        return image_base64

    def _plot_bar_chart(self, data: dict):
        df = pd.DataFrame(data["data_points"])
        for series in data["series_names"]:
            series_data = df[df["series"] == series]
            sns.barplot(x="x", y="y", data=series_data, palette="Set2")
        plt.title(data["title"])
        plt.xlabel("x")
        plt.ylabel("y")
        plt.legend(title="系列")

    def _plot_line_chart(self, data: dict):
        df = pd.DataFrame(data["data_points"])
        for series in data["series_names"]:
            series_data = df[df["series"] == series]
            plt.plot(series_data["x"], series_data["y"], marker='o', label=series)
        plt.title(data["title"])
        plt.xlabel("x")
        plt.ylabel("y")
        plt.legend(title="系列")
        plt.grid(True)

    def _plot_pie_chart(self, data: dict):
        plt.pie(
            data["y_values"],
            labels=data["x_values"],
            autopct='%1.1f%%',
            startangle=90,
            shadow=True,
            colors=sns.color_palette("Set3", len(data["x_values"]))
        )
        plt.title(data["title"])
        plt.axis('equal')

    def _plot_scatter_chart(self, data: dict):
        df = pd.DataFrame(data["data_points"])
        plt.scatter(df["x"], df["y"], color="blue", marker="o")
        plt.title(data["title"])
        plt.xlabel("x")
        plt.ylabel("y")
        plt.grid(True)