from dash import html, dcc
import dash_bootstrap_components as dbc
from frontend.app import app
from dash_iconify import DashIconify
import yaml

def render_dummy_textbox():
    return html.Div(id="last-textbox", style={"display": "none"})

def render_textbox(message:dict, number:int):
    # print(f"render_textbox: {message}")
    # print(f"text: {message['content']}")
    style = {
        "max-width": "60%",
        "width": "max-content",
        "padding": "5px 10px",
        "border-radius": 25,
        "margin-bottom": 20,
        'border': '0px solid'
    }
    text = message["content"]
    role = message["role"]

    debug = dbc.Collapse(
                dbc.Card(
                    dcc.Markdown(
                        "```yaml\n" + yaml.dump(message["debug"], indent=2) + "\n```"
                    )
                ),
                id={"type": "debug-collapse", "index": number},
                is_open=False,
            )
    
    

    if role == "user":
        style["margin-left"] = "auto"
        style["margin-right"] = 0

        thumbnail = DashIconify(
            icon="ion:person",
            width=36,
            style={
                "border-radius": 50,
                "height": 36,
                "margin-left": 5,
                "float": "right",
            },
        )

        button = html.Button(
            DashIconify(icon="tabler:plus", width=24),  # use the Ionicons search icon
            className="btn btn-primary",
            id={"type": "debug-button", "index": number},
        )

        textbox = dbc.Card(
                    [
                        html.Div([
                                button,
                            ],
                            style={
                                'position': 'absolute',
                                'top': '0px',
                                'right': '0px',
                                'margin': 0,
                                'padding': 0,
                            },
                        ),
                        dbc.CardBody([
                            text, 
                            debug
                        ])
                    ], 
                    style=style, body=True, color="primary", inverse=True)
        return html.Div([thumbnail, textbox])

    elif role == "assistant":
        style["margin-left"] = 0
        style["margin-right"] = "auto"

        thumbnail = DashIconify(
            icon="carbon:bot",
            width=36,
            style={
                "border-radius": 50,
                "height": 36,
                "margin-right": 5,
                "float": "left",
            },
        )

        button = html.Button(
            DashIconify(icon="tabler:plus", width=24),  # use the Ionicons search icon
            className="btn btn-light",
            id={"type": "debug-button", "index": number},
        )
        markdown = dcc.Markdown(text)
        textbox = dbc.Card(
                    [
                        html.Div([
                                button,
                            ],
                            style={
                                'position': 'absolute',
                                'top': '0px',
                                'right': '0px',
                                'margin': 0,
                                'padding': 0,
                            },
                        ),
                        dbc.CardBody([
                            markdown, 
                            debug
                        ])
                    ], 
                    style=style, body=True, color="light", inverse=False)

        return html.Div([thumbnail, textbox])

    else:
        raise ValueError(f"Incorrect role: {role}")