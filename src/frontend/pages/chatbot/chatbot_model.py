# from conversation.chat_app import load_chat_app
import os
from chat_api import PromptFlowChat

promptflow_folder = "./src/rag_flow"

chat_app = PromptFlowChat(prompt_flow=promptflow_folder)