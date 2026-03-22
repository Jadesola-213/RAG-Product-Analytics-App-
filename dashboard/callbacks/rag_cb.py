"""
RAG / Ask Jade tab callbacks.

Handles question submission, displays answer in a chat-style UI,
and shows retrieved source chunks as a collapsible accordion.
"""

from dash import Input, Output, State, html, no_update
import dash_bootstrap_components as dbc

from dashboard.app_instance import app
from rag.qa import ask_jade

import store


def _user_bubble(text: str):
    return html.Div([
        html.Span("You", className="chat-sender text-end d-block"),
        html.P(text, className="chat-bubble user-bubble"),
    ], className="chat-message user-message")


def _assistant_bubble(text: str):
    return html.Div([
        html.Span("🤖 Jade", className="chat-sender"),
        html.P(text, className="chat-bubble assistant-bubble"),
    ], className="chat-message")


def _sources_accordion(sources: list[str]):
    if not sources:
        return html.Div()
    items = [
        dbc.AccordionItem(
            html.P(src, className="text-muted small"),
            title=f"Source {i+1}",
        )
        for i, src in enumerate(sources)
    ]
    return dbc.Accordion(items, start_collapsed=True, className="rag-sources")


@app.callback(
    Output("chat-history",          "children"),
    Output("rag-sources",           "children"),
    Output("rag-input",             "value"),
    Output("chat-store",            "data"),
    Input("rag-submit-btn",         "n_clicks"),
    Input("rag-input",              "n_submit"),
    State("rag-input",              "value"),
    State("chat-store",             "data"),
    prevent_initial_call=True,
)
def handle_question(n_clicks, n_submit, question, history):
    if not question or not question.strip():
        return no_update, no_update, no_update, no_update

    question = question.strip()

    # Call RAG
    answer, sources = ask_jade(question, store.RETRIEVER)

    # Build updated chat history
    history = history or []
    history.append({"role": "user",      "text": question})
    history.append({"role": "assistant", "text": answer})

    # Render messages
    welcome = html.Div([
        html.Span("🤖 Jade", className="chat-sender"),
        html.P(
            "Hello! I'm Jade, your coffee data analyst. "
            "Ask me anything about sales, products, locations, or trends.",
            className="chat-bubble assistant-bubble",
        ),
    ], className="chat-message")

    messages = [welcome]
    for msg in history:
        if msg["role"] == "user":
            messages.append(_user_bubble(msg["text"]))
        else:
            messages.append(_assistant_bubble(msg["text"]))

    return messages, _sources_accordion(sources), "", history
