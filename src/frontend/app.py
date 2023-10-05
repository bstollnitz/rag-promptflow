import openai
import chainlit as cl
from chat_api import PromptFlowChat
import os
import yaml, json
promptflow_folder = "./src/rag_flow"

@cl.on_chat_start
def start_chat():
    cl.user_session.set("message_history", [])

@cl.on_message
async def main(question: str, question_id: str):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": question})

    chat_app = PromptFlowChat(prompt_flow=promptflow_folder)
    response = await cl.make_async(chat_app)(messages=message_history, 
                                             stream=True)

    await cl.Message(content=f"#### Messages:\n```yaml\n{yaml.dump(message_history)}\n```", parent_id=question_id).send()

    msg = cl.Message(content="")
    extra_args = None
    session_info = None
    for chunk in response:
        if chunk["object"] == "chat.completion.chunk":
            if "content" in chunk["choices"][0]["delta"]:
                token = chunk["choices"][0]["delta"].get("content", "")
                await msg.stream_token(token)
            if "extra_args" in chunk["choices"][0]:
                extra_args = chunk["choices"][0]["extra_args"]
                # add some metadata to help with debugging
                await cl.Message(content=f"#### Intent:\n{extra_args['intent']}", parent_id=question_id).send()
                await cl.Message(content=f"#### Context:\n```yaml\n{yaml.dump(extra_args['context'])}\n```", parent_id=question_id).send()

    message_content = msg.content

    message_history.append({"role": "assistant", "content": message_content})
    await msg.send()
