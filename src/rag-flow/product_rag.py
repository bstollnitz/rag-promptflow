"""
Combine documents and question in a prompt and send it to an LLM to get the answer. 
"""
import openai
from promptflow import tool
from promptflow.connections import AzureOpenAIConnection
from typing import Generator

@tool
def product_rag(
    user_message: str,
    azure_open_ai_connection: AzureOpenAIConnection,
    deployment_name: str,
) -> Generator[str, None, None]:
    """
    Ask the LLM to andwer the user's question given the chat history and context.
    """
    openai.api_type = azure_open_ai_connection.api_type
    openai.api_base = azure_open_ai_connection.api_base
    openai.api_version = azure_open_ai_connection.api_version
    openai.api_key = azure_open_ai_connection.api_key

    system_message = (
        "You are supporting a customer service agent in their chat with a "
        "customer. If the customer's question is related to a product, you'll be given "
        "additional information on the product the customer is referring to. This can "
        "include product manuals, product reviews, specifications, etc."
    )

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    chat_completion = openai.ChatCompletion.create(
        deployment_id=deployment_name,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
        n=1,
        stream=True
    )

    for chunk in chat_completion:
        if chunk["object"] == "chat.completion.chunk":
            if "content" in chunk["choices"][0]["delta"]:
                yield chunk["choices"][0]["delta"]["content"]

