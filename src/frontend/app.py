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
async def main(message: cl.Message):
    question = message.content 
    question_id = message.id
    with open(test_set) as f:
        test_cases = f.readlines()
    help_text = f"""#### Commands:
- `/eval` - evaluate the current conversation
- `/add_test` - add the current conversation to the test set (`{test_set}`)
- `/test [<number>]` - run the test case with the given number (`0-{len(test_cases)-1}`). If no number is given, run the last test case.
- `/config` - show the current configuration
- `/help` - show this help message
- anything else - continue the conversation
"""
    config_text = f"""| **Property** | **Value** |
| --- | --- |
| promptflow_folder | {promptflow_folder} |
| eval_flow_folder | {eval_flow_folder} |
| test_set | {test_set} |
"""
    if question.startswith("/config"):
        await cl.Message(content=config_text).send()
    elif question.startswith("/eval"):
        await call_eval(question, question_id)
    elif question.startswith("/add_test"):
        await add_test(question, question_id)
    elif question.startswith("/help"):
        await cl.Message(content=help_text).send()
    elif question.startswith("/test"):
        await run_test(question, question_id)
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

    await cl.Message(content=f"#### Download as testcase:\n```json\n{json.dumps(test_case)}\n```", parent_id=question_id).send()

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

async def run_test(command: str, command_id: str):
    chat_app = PromptFlowChat(prompt_flow=promptflow_folder)
    # parse the test number from the command
    # read the test set
    with open(test_set) as f:
        test_cases = f.readlines()
    # get the test case -- if the line number is out of range, return show an error
    try:
        if len(command.split(" ")) < 2:
            test_number = -1
        else:
            test_number = int(command.split(" ")[1])
        test_case = json.loads(test_cases[test_number])
    except IndexError:
        await cl.Message(content=f"#### Test case `{test_number}` not found\nValid test case numbers are 0-{len(test_cases)-1}").send()
        return
    except ValueError:
        await cl.Message(content=f"#### Invalid test case number `{command.split(' ')[1]}`\nPlease provide an integer number.").send()
        return
    
    # run the test case
    # reset the message history
    cl.user_session.set("message_history", [])
    cl.user_session.set("messages", [])
    # restore the message history
    author = "User"
    for message in chat_app._chat_history_to_openai(test_case["chat_history"]):
        cl.user_session.get("message_history").append(message)
        cl.user_session.get("messages").append(message)
        print(message)
        msg = cl.Message(content=message["content"], author=author)
        await msg.send()
        author = "Assistant" if author == "User" else "User"
    msg = cl.Message(test_case["question"], author="User")
    await msg.send()
    await call_chat(test_case["question"], msg.id)
    await call_eval(test_case["question"], msg.id)



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

    with open(test_set) as f:
        test_cases = f.readlines()
    await cl.Message(content=f"Added the following test case:\n\n```yaml\n{yaml.dump(test_case)}```\nIts number is {len(test_cases)-1}").send()

