import openai
import chainlit as cl
from frontend.chat_util import PromptFlowChat
import promptflow as pf
import os
import yaml, json
promptflow_folder = "./src/rag_flow"
eval_flow_folder = "./src/eval_flow"
test_set = "data/prompt_input/questions.jsonl"

@cl.on_chat_start
def start_chat():
    cl.user_session.set("message_history", [])
    cl.user_session.set("messages", [])

@cl.on_message
async def main(question: str, question_id: str):
    help_text = f"""#### Commands:
- `/eval` - evaluate the current conversation
- `/help` - show this help message
- `/add_test` - add the current conversation to the test set (`{test_set}`)
- anything else - continue the conversation
"""
    if question.startswith("/eval"):
        await call_eval(question, question_id)
    elif question.startswith("/add_test"):
        await add_test(question, question_id)
    elif question.startswith("/help"):
        await cl.Message(content=help_text).send()
    else:
        await call_chat(question, question_id)

async def call_chat(question: str, question_id: str):
    message_history = cl.user_session.get("message_history")
    messages = cl.user_session.get("messages")
    chat_app = PromptFlowChat(prompt_flow=promptflow_folder)
    test_case = {"chat_history": chat_app._chat_history_to_pf(message_history), "question": question}
    message_history.append({"role": "user", "content": question})
    messages.append({"role": "user", "content": question})

    response = await cl.make_async(chat_app.chat_completion)(messages=message_history, 
                                             stream=True)

    await cl.Message(content=f"#### Messages:\n```yaml\n{yaml.dump(message_history)}\n```", parent_id=question_id).send()

    msg = cl.Message(content="")
    context = None
    for chunk in response:
        if chunk["object"] == "chat.completion.chunk":
            if "content" in chunk["choices"][0]["delta"]:
                token = chunk["choices"][0]["delta"].get("content", "")
                await msg.stream_token(token)
            if "context" in chunk["choices"][0]["delta"]:
                context = chunk["choices"][0]["delta"]["context"]
                # add some metadata to help with debugging
                if "intent" in context:
                    await cl.Message(content=f"#### Intent:\n{context['intent']}", parent_id=question_id).send()
                if "context" in context:
                    context_id = await cl.Message(content=f"#### Context:\n", parent_id=question_id).send()
                    for item in context["context"]:
                        await cl.Message(content=f"##{item}\n", parent_id=context_id).send()

    # await cl.Message(content=f"#### Download as testcase:\n```json\n{json.dumps(test_case)}\n```", parent_id=question_id).send()

    message_history.append({"role": "assistant", "content": msg.content})
    messages.append({"role": "assistant", "content": msg.content, "context": context})
    await msg.send()

async def call_eval(command: str, command_id: str):
    messages = cl.user_session.get("messages")

    if len(messages) == 0:
        await cl.Message(content=f"#### No messages to evaluate").send()
        return
    
    chat_app = PromptFlowChat(prompt_flow=promptflow_folder)
    chat_history = chat_app._chat_history_to_pf(messages[:-2])
    question = messages[-2]["content"]
    answer = messages[-1]["content"]
    context = messages[-1]["context"]["context"]
    
    cli = pf.PFClient()
    result = await cl.make_async(cli.test)(eval_flow_folder, inputs=dict(
        chat_history=chat_history,
        question=question,
        answer=answer,
        context=context
    ))

    await cl.Message(content=f"```yaml\n{yaml.dump(result)}```").send()

async def add_test(command: str, command_id: str):
    messages = cl.user_session.get("messages")
    if len(messages) == 0:
        await cl.Message(content=f"#### No messages to add").send()
        return

    chat_app = PromptFlowChat(prompt_flow=promptflow_folder)
    chat_history = chat_app._chat_history_to_pf(messages[:-2])
    question = messages[-2]["content"]
    answer = messages[-1]["content"]
    context = messages[-1]["context"]["context"]

    test_case = {"chat_history": chat_history, "question": question}
    # append to test set
    with open(test_set, "a") as f:
        f.write(json.dumps(test_case) + "\n")

    await cl.Message(content=f"Added the following test case:\n\n```yaml\n{yaml.dump(test_case)}```").send()
