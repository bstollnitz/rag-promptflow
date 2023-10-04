"""
Combine documents and question in a prompt and send it to an LLM to get the answer. 
"""
from typing import Generator

import openai, os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import Vector
from jinja2 import Template
from promptflow.connections import AzureOpenAIConnection, CognitiveSearchConnection

from promptflow import tool

# Chat roles
SYSTEM = "system"
USER = "user"
ASSISTANT = "assistant"

# Azure OpenAI deployment names
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"
AZURE_OPENAI_CHATGPT_DEPLOYMENT = "gpt-35-turbo-0613"

# Azure Cognitive Search index name
AZURE_SEARCH_INDEX_NAME = "rag-promptflow-index"


def _summarize_user_intent(query: str, chat_history: list[str]) -> str:
    """
    Creates a user message containing the user intent, by summarizing the chat
    history and user query.
    """
    jinja_template = os.path.join(os.path.dirname(__file__), "summarize_user_intent.jinja2")
    with open(jinja_template, encoding="utf-8") as f:
        template = Template(f.read())
    prompt = template.render(query=query, chat_history=chat_history)
    messages = [
        {
            "role": SYSTEM,
            "content": prompt,
        }
    ]

    chat_intent_completion = openai.ChatCompletion.create(
        deployment_id=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
        n=1,
    )
    user_intent = chat_intent_completion.choices[0].message.content

    return user_intent


def _get_context(
    question: str, azure_search_connection: CognitiveSearchConnection
) -> list[str]:
    """
    Gets the relevant documents from Azure Cognitive Search.
    """
    query_vector = Vector(
        value=openai.Embedding.create(
            engine=AZURE_OPENAI_EMBEDDING_DEPLOYMENT, input=question
        )["data"][0]["embedding"],
        fields="embedding",
    )

    search_client = SearchClient(
        endpoint=azure_search_connection.api_base,
        index_name=AZURE_SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(azure_search_connection.api_key),
    )

    docs = search_client.search(search_text="", vectors=[query_vector], top=2)
    context = [doc["content"] for doc in docs]

    return context


def _rag(context_list: list[str], query: str) -> Generator[str, None, None]:
    """
    Asks the LLM to answer the user's query with the context provided.
    """
    jinja_template = os.path.join(os.path.dirname(__file__),"rag_system_prompt.jinja2")
    with open(jinja_template, encoding="utf-8") as f:
        template = Template(f.read())
    system_prompt = template.render(context_list=context_list)
    messages = [
        {
            "role": SYSTEM,
            "content": system_prompt,
        },
        {
            "role": USER,
            "content": query,
        },
    ]

    chat_completion = openai.ChatCompletion.create(
        deployment_id=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
        n=1,
        stream=True,
    )

    for chunk in chat_completion:
        if chunk["object"] == "chat.completion.chunk":
            token = chunk["choices"][0]["delta"].get("content", "")
            yield token

    return

@tool
def rag(
    question: str,
    chat_history: list[str],
    azure_open_ai_connection: AzureOpenAIConnection,
    azure_search_connection: CognitiveSearchConnection,
) -> Generator[str, None, None]:
    openai.api_type = azure_open_ai_connection.api_type
    openai.api_base = azure_open_ai_connection.api_base
    openai.api_version = azure_open_ai_connection.api_version
    openai.api_key = azure_open_ai_connection.api_key

    user_intent = _summarize_user_intent(question, chat_history)
    context = _get_context(question, azure_search_connection)
    answer = _rag(context, question)

    return {"answer": answer, "context": context, "intent": user_intent}

    # for chunk in chat_completion:
    #     if chunk["object"] == "chat.completion.chunk":
    #         if "content" in chunk["choices"][0]["delta"]:
    #             yield chunk["choices"][0]["delta"]["content"]
