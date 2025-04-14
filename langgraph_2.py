from typing import TypedDict, Annotated  
from langgraph.graph.message import add_messages  
from datetime import datetime  
from langgraph.graph import StateGraph, START, END  
import time  
import random  


class State(TypedDict):  
    messages: Annotated[list, add_messages]  


def test_node(state: State):  
    current_messages = state["messages"]  
    print(f"exec test node, messages: {current_messages}")  
    time.sleep(random.randint(1, 4))  
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
    return {"messages": [current_time]}  


graph_builder = StateGraph(State)  
graph_builder.add_node("node1", test_node)  
graph_builder.add_node("node2", test_node)  
graph_builder.add_node("node3", test_node)  
graph_builder.add_edge(START, "node1")  
graph_builder.add_edge("node1", "node2")  
graph_builder.add_edge("node2", "node3")  
graph_builder.add_edge("node3", END)  
graph = graph_builder.compile()  
graph.get_graph().draw_mermaid_png(output_file_path="graph.png")  
result = graph.invoke(input={"messages": ["你好"]})  
print(result)