import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from langchain_core.tools import BaseTool  

class GenerateImageTool(BaseTool):  
    """  
    绘制图表  
    """    
    name: str = "图表绘制工具"  
    description: str = "根据解析出的 JSON 数据和目标图表类型绘制图表"  

    def _run(self, data):
        chart_type = data["chart_type"]
        
        if chart_type == "bar":
            self.plot_bar_chart(data)
        elif chart_type == "pie":
            self.plot_pie_chart(data)
        elif chart_type == "scatter":
            self.plot_scatter_chart(data)
        elif chart_type == "line":
            self.plot_line_chart(data)
        else:
            print(f"不支持的图表类型: {chart_type}")

    def plot_bar_chart(self, data):
        """
        绘制柱状图。
        """
        x_ticks = data["x_axis"]["ticks"]
        data_series = data["data_series"]
        
        # 创建 DataFrame
        df = pd.DataFrame()
        for series in data_series:
            df[series["name"]] = series["values"]
        df["x"] = x_ticks
        
        # 绘图
        plt.figure(figsize=(10, 6))
        for series in data_series:
            sns.barplot(x="x", y=series["name"], data=df, palette="Set2")
        
        plt.title(data["title"])
        plt.xlabel(data["x_axis"]["label"])
        plt.ylabel(data["y_axis"]["label"])
        plt.legend(title="产品")
        plt.tight_layout()
        plt.show()

    def plot_pie_chart(self, data):
        """
        绘制饼图。
        """
        slices = data["slices"]
        labels = [item["name"] for item in slices]
        values = [item["value"] for item in slices]
        
        # 绘图
        plt.figure(figsize=(8, 8))
        plt.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            shadow=True,
            colors=sns.color_palette("Set3", len(slices))
        )
        plt.title(data["title"])
        plt.axis('equal')
        plt.tight_layout()
        plt.show()

    def plot_scatter_chart(self, data):
        """
        绘制散点图。
        """
        points = data["points"]
        x_values = [point["x"] for point in points]
        y_values = [point["y"] for point in points]
        
        # 绘图
        plt.figure(figsize=(8, 6))
        plt.scatter(x_values, y_values, color="blue", marker="o")
        
        plt.title(data["title"])
        plt.xlabel(data["x_axis"]["label"])
        plt.ylabel(data["y_axis"]["label"])
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_line_chart(self, data):
        """
        绘制折线图。
        """
        x_ticks = data["x_axis"]["ticks"]
        data_series = data["data_series"]
        
        # 创建 DataFrame
        df = pd.DataFrame()
        for series in data_series:
            df[series["name"]] = series["values"]
        df["x"] = x_ticks
        
        # 绘图
        plt.figure(figsize=(10, 6))
        for series in data_series:
            plt.plot(df["x"], df[series["name"]], marker='o', label=series["name"])
        
        plt.title(data["title"])
        plt.xlabel(data["x_axis"]["label"])
        plt.ylabel(data["y_axis"]["label"])
        plt.legend(title="产品")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

# 示例数据
bar_data = {
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

pie_data = {
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

scatter_data = {
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

line_data = {
    "title": "月度销售额折线图",
    "chart_type": "line",
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

# 测试
gen_img = GenerateImageTool()
gen_img._run(bar_data)
gen_img._run(pie_data)
gen_img._run(scatter_data)
gen_img._run(line_data)