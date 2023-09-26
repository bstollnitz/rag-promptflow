
from dotenv import find_dotenv, load_dotenv
dotenv_file = find_dotenv()
print("loading .env file: ", dotenv_file)
_ = load_dotenv(dotenv_file)

from dash.dependencies import Input, Output
from dash import dcc, html 

# import pages
from frontend.pages.chatbot.chatbot_view import render_chatbot
# from pages.chatbot.chatbot_controller import *
import frontend.pages.chatbot.chatbot_controller
from frontend.pages.page_not_found import page_not_found

from frontend.app import app


def serve_content():
    """
    :return: html div component
    """
    return html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ])


app.layout = serve_content()


@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    """
    :param pathname: path of the actual page
    :return: page
    """

    if pathname in '/' or pathname in '/chatbot':
        return render_chatbot()
    return page_not_found()


if __name__ == '__main__':
    app.run_server(debug=True)