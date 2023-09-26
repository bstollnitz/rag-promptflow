import dash_bootstrap_components as dbc
from dash import Dash
import openai
import os
from dash.long_callback import DiskcacheLongCallbackManager

APP_TITLE = "Chatbot Simulator"

import diskcache
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

app = Dash(__name__,
            title=APP_TITLE,
            update_title='Loading...',
            suppress_callback_exceptions=True,
            external_stylesheets=[dbc.themes.FLATLY],
            long_callback_manager=long_callback_manager)

openai.api_key = os.getenv("OPENAI_API_KEY")