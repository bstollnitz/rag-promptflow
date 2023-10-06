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
    chat_app = PromptFlowChat(prompt_flow=promptflow_folder)
    test_case = {"chat_history": chat_app._chat_history_to_pf(message_history), "question": question}
    message_history.append({"role": "user", "content": question})

    response = await cl.make_async(chat_app)(messages=message_history, 
                                             stream=True)

    await cl.Message(content=f"#### Messages:\n```yaml\n{yaml.dump(message_history)}\n```", parent_id=question_id).send()

    msg = cl.Message(content="")
    extra_args = None
    for chunk in response:
        if chunk["object"] == "chat.completion.chunk":
            if "content" in chunk["choices"][0]["delta"]:
                token = chunk["choices"][0]["delta"].get("content", "")
                await msg.stream_token(token)
            if "extra_args" in chunk["choices"][0]:
                extra_args = chunk["choices"][0]["extra_args"]
                # add some metadata to help with debugging
                if "intent" in extra_args:
                    await cl.Message(content=f"#### Intent:\n{extra_args['intent']}", parent_id=question_id).send()
                if "context" in extra_args:
                    context_id = await cl.Message(content=f"#### Context:\n", parent_id=question_id).send()
                    for item in extra_args["context"]:
                        await cl.Message(content=f"##{item}\n", parent_id=context_id).send()

    await cl.Message(content=f"#### Download as testcase:\n```json\n{json.dumps(test_case)}\n```", parent_id=question_id).send()

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.send()
