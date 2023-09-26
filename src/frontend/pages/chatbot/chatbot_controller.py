from dash.dependencies import Input, Output, State, MATCH
from frontend.app import app
import inspect, asyncio, yaml

from frontend.components.textbox import render_textbox, render_dummy_textbox
from frontend.pages.chatbot.chatbot_model import chat_app

@app.callback(
    Output(component_id="display-conversation", component_property="children"), 
    Input(component_id="store-conversation", component_property="data")
)
def update_display(chat_history):
    textboxes = []
    if len(chat_history) == 0:
        textboxes.append(render_dummy_textbox())
        return textboxes

    for i, message in enumerate(chat_history):
        textboxes.append(render_textbox(message, i))

    return textboxes

@app.callback(
    Output(component_id="store-conversation", component_property="data", allow_duplicate=True),
    Input(component_id="clear-chat-history-button", component_property="n_clicks"),
    prevent_initial_call=True,
)
def clear_chat_history(n_clicks):
    return []

@app.callback(
    Output(component_id="user-input", component_property="value"),
    Input(component_id="submit", component_property="n_clicks"), 
    Input(component_id="user-input", component_property="n_submit"),
)
def clear_input(n_clicks, n_submit):
    return ""

@app.callback(
    Output(component_id="store-conversation", component_property="data", allow_duplicate=True), 
    Output(component_id="store-stream-trigger", component_property="data"),
    Input(component_id="submit", component_property="n_clicks"), 
    Input(component_id="user-input", component_property="n_submit"),
    State(component_id="user-input", component_property="value"), 
    State(component_id="store-conversation", component_property="data"),
    prevent_initial_call=True,
)
def upcate_conversation(n_clicks, n_submit, user_input, chat_history):
    # print("upcate_conversation")
    if n_clicks == 0 and n_submit is None:
        return [], 0

    if user_input is None or user_input == "":
        return chat_history, len(chat_history)
    
    chat_history.append({"role": "user", "content": user_input, "debug": {}})
    chat_history.append({"role": "assistant", "content": "", "debug": {"extra_args": None, "session_info": None}})
    # print("chat_history: ", chat_history)
    return chat_history, len(chat_history)

@app.callback(
    Output(component_id="debug", component_property="children"),
    Input(component_id="store-stream-trigger", component_property="data"), 
)
def show_debug(trigger):
    # print("show_debug", trigger)
    return str(int(trigger/2))

async def process_response(response_coro, chat_history, set_progress):
    response = await response_coro
    incremental_text = ""
    extra_args = None
    session_info = None
    print(f"\n\n{chat_history[-2]['role']}: " + chat_history[-2]["content"])
    print(f"{chat_history[-1]['role']}: ", end="", flush=True)
    async for chunk in response:
        if chunk["object"] == "chat.completion.chunk":
            if "content" in chunk["choices"][0]["delta"]:
                incremental_text += chunk["choices"][0]["delta"]["content"]
                print(chunk["choices"][0]["delta"]["content"], end="", flush=True)
            if "extra_args" in chunk["choices"][0]:
                extra_args = chunk["choices"][0]["extra_args"]
                print(yaml.dump({"extra_args":chunk["choices"][0]["extra_args"]}, indent=2)) 
            if "session_info" in chunk["choices"][0]:
                extra_args = chunk["choices"][0]["session_info"]
                print(yaml.dump({"session_info":chunk["choices"][0]["session_info"]}, indent=2)) 
        chat_history[-1]["content"] = incremental_text
        chat_history[-1]["debug"] = {"extra_args": extra_args, "session_info": session_info}
        set_progress([chat_history])
    return chat_history

@app.callback(
    inputs=Input(component_id="store-stream-trigger", component_property="data"), 
    state=State(component_id="store-conversation", component_property="data"),
    output=[Output(component_id="store-conversation", component_property="data", allow_duplicate=True),
            Output(component_id="loading-component", component_property="children", allow_duplicate=True)],
    progress=Output(component_id="store-conversation", component_property="data", allow_duplicate=True),
    progress_default=[],
    background=True,
    interval=100,
    prevent_initial_call=True,
)
def run_chatbot(set_progress, trigger, chat_history):
    if len(chat_history) == 0:
        return chat_history, None
    
    messages = []
    for message in chat_history:
        message = message.copy()
        message.pop("debug")
        messages.append(message)
    # drop last message
    messages = messages[:-1]
    chat_history[-2]["debug"] = {"messages": messages, "extra_args": chat_app.extra_args, "stream": True}
    chat_history[-1]["content"] = "..."

    set_progress([chat_history])
    response = chat_app(messages=messages, extra_args=chat_app.extra_args, stream=True)
    if inspect.iscoroutine(response):
        chat_history = asyncio.run(process_response(response, chat_history, set_progress))
        return chat_history, None 
    else: 
        incremental_text = ""
        extra_args = None
        session_info = None
        print(f"\n\n{chat_history[-2]['role']}: " + chat_history[-2]["content"])
        print(f"{chat_history[-1]['role']}: ", end="", flush=True)
        for chunk in response:
            if chunk["object"] == "chat.completion.chunk":
                if "content" in chunk["choices"][0]["delta"]:
                    incremental_text += chunk["choices"][0]["delta"]["content"]
                    print(chunk["choices"][0]["delta"]["content"], end="", flush=True)
                if "extra_args" in chunk["choices"][0]:
                    extra_args = chunk["choices"][0]["extra_args"]
                    print(yaml.dump({"extra_args":chunk["choices"][0]["extra_args"]}, indent=2)) 
                if "session_info" in chunk["choices"][0]:
                    extra_args = chunk["choices"][0]["session_info"]
                    print(yaml.dump({"session_info":chunk["choices"][0]["session_info"]}, indent=2)) 
            chat_history[-1]["content"] = incremental_text
            chat_history[-1]["debug"] = {"extra_args": extra_args, "session_info": session_info}
            set_progress([chat_history])
        return chat_history, None

@app.callback(
    Output("configuration", "is_open"),
    Input("open-configuration", "n_clicks"),
    [State("configuration", "is_open")],
)
def toggle_configuration(n1, is_open):
    if n1:
        return not is_open
    return is_open


@app.callback(
    Output({'type': 'debug-collapse', 'index': MATCH}, 'is_open'),
    Input({'type': 'debug-button', 'index': MATCH}, 'n_clicks'),
    State({'type': 'debug-collapse', 'index': MATCH}, 'is_open'),    
    prevent_initial_call=True,
)
def display_output(n_clicks, is_open):
    return not is_open

