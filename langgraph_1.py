from typing import Annotated  

from typing_extensions import TypedDict  

from langgraph.graph import StateGraph, START, END  
from langgraph.graph.message import add_messages  
from langchain_openai import ChatOpenAI  

llm = ChatOpenAI(
    openai_api_base="https://api.siliconflow.cn/v1/",
    openai_api_key= "sk-pieicwwfnoastulaxwytnemrokzhooqsziombojeqcyhzwbu",  # app_key
    # model_name="Pro/Qwen/Qwen2.5-VL-7B-Instruct",   # 模型名称
    model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    temperature=0.7,
)


class State(TypedDict):  
    messages: Annotated[list, add_messages]  


graph_builder = StateGraph(State)  


def chatbot(state: State):  
    return {"messages": [llm.invoke(state["messages"])]}  


# 添加节点 node  
graph_builder.add_node("chatbot", chatbot)  

# 添加边 edgegraph_builder.add_edge(START, "chatbot")  
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)  

       

# 编译图  

graph = graph_builder.compile()  

# 生成一张png 图片  
graph.get_graph().draw_mermaid_png(output_file_path="graph.png")  

inputs = {  
    "messages": [  
        {"role": "user", "content": "你好，你是谁？"}  
    ]  
}  

result = graph.invoke(inputs)  
print(result)