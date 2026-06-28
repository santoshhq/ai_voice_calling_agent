from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage,BaseMessage,SystemMessage
from langgraph.graph import StateGraph, START,END,MessagesState
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
import asyncio,os
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from prompts import SYSTEM_PROMPT
load_dotenv()

gemini_model=ChatGoogleGenerativeAI(model="gemini-2.5-flash")
 
async def build_graph():
    
    async def ChatAssistance(state:MessagesState)->MessagesState:
        prompt=ChatPromptTemplate.from_messages([
            ("system",SYSTEM_PROMPT),
            MessagesPlaceholder("messages")
        ])
        chain=prompt | gemini_model
        response=await chain.ainvoke(state["messages"])
        return {"messages":[response]}

    graph=StateGraph(MessagesState)
    graph.add_node("ChatAssistance",ChatAssistance)
    graph.add_edge(START,"ChatAssistance")
    graph.add_edge("ChatAssistance",END)
    return graph.compile( )