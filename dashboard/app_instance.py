"""
Creates the Dash app singleton.
All other dashboard modules import `app` from here.
"""

import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="Jade Coffee Analytics",
)
server = app.server  # expose Flask server (for production WSGI)
