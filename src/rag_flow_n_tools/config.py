from promptflow import tool
import os

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def config() -> dict:
  return {
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT","text-embedding-ada-002"),
    "AZURE_OPENAI_CHATGPT_DEPLOYMENT": os.environ.get("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "gpt-35-turbo-0613"),
  }
