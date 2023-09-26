import dash_bootstrap_components as dbc
from dash_iconify import DashIconify

def render_navbar(brand_name:str = "Chatbot", brand_color:str = "#165AA7"):
    navbar = dbc.NavbarSimple(
            children=[
                dbc.NavItem(
                    children=[
                        dbc.Button(
                            DashIconify(icon="ant-design:clear-outlined", width=24), 
                            className="btn btn-success",
                            id="clear-chat-history-button",
                            outline=True
                        ),
                    ]
                ),
            ],
            brand=brand_name,
            brand_href="/",
            color=brand_color,
            sticky='top',
            dark=True,
            expand=True
        )
    return navbar

