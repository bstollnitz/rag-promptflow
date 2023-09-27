import os
if "TEST_PYTHONPATH" in os.environ:
  # append it to the sys path
  # this is required for the test discovery to work in VSCode -- please let me know if you know a better way
  import sys
  sys.path.append(os.environ["TEST_PYTHONPATH"])

import promptflow as pf
from promptflow.connections import AzureOpenAIConnection, CognitiveSearchConnection
import os
from typing import List
from rag_flow.rag import rag
from rag_flow.get_context import get_context
from frontend.pages.chatbot.chatbot_controller import run_chatbot

class OutputCollector:
  def __init__(self):
    self.state = None
  def __call__(self, state):
    self.state = state 

  
def load_secrets(secrets: List[str]):
    from dotenv import load_dotenv, find_dotenv
    dotenv_file = find_dotenv()
    print("loading secrets from .env file: ", dotenv_file)
    _ = load_dotenv(dotenv_file)
    for secret in secrets:
        if not secret in os.environ:
            raise Exception(f"Secret {secret} not found in environment variables")
   
def chat_connection() -> AzureOpenAIConnection:
  load_secrets(["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_API_BASE"])
  return AzureOpenAIConnection(
      api_key=os.environ["AZURE_OPENAI_API_KEY"],
      api_base=os.environ["AZURE_OPENAI_API_BASE"],
      api_type="azure",
      api_version="2023-03-15-preview",
  )

def search_connection() -> CognitiveSearchConnection:
  load_secrets(["AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_KEY"])
  return CognitiveSearchConnection(
    api_base=os.environ["AZURE_SEARCH_ENDPOINT"],
    api_key=os.environ["AZURE_SEARCH_KEY"],
  )

prompt_flow_path = "src/rag_flow"

tent_system_prompt = """
You are supporting a customer service agent in their chat with a 
customer. If the customer's question is related to a product, you'll be given 
additional context on the product the customer is referring to. This can 
include product manuals, product reviews, specifications, etc.

Please write a reply to the customer based on the context provided. 
Do not include any additional information. If you don't know what to reply, just 
write "I don't know".

Here's the context:
```
'Information about product item_number: 8, Alpine Explorer Tent, price $350, Brand: AlpineGear, Category: Tents, Features: Waterproof, provides reliable protection against rain and moisture. Easy Setup: Simple and quick assembly process. Room Divider: Includes a detachable divider. Excellent Ventilation: Multiple mesh windows and vents. Gear Loft: Built-in gear loft or storage pockets. Technical Specs: Alpine Explorer Tent User Guide, Package Contents: Tent body, Tent poles, Rainfly, Stakes and guy lines, Carry bag, User Guide.'

'Information about product item_number: 15, SkyView 2-Person Tent, price $200, Brand: OutdoorLiving, Category: Tents, Features: Spacious, Durable and waterproof, Easy and quick setup, Two large doors, Vestibules for extra storage, Mesh panels for enhanced ventilation, Rainfly included, Freestanding design, Multiple interior pockets, Reflective guy lines and stake points, Compact and lightweight, Double-stitched seams, Comes with a carrying bag. Technical Specs: Best Use: Camping, Hiking, Capacity: 2-person, Seasons: 3-season, Packed Weight: Approx. 8 lbs.'
```
"""

frontend_chat_history = [
  {'role': 'user', 'content': "Tell me about your tents", 'debug': None},
  {'role': 'assistant', 'content': "...", 'debug': None},
  ]


def test_product_search():
  result = get_context(  question="Tell me about your SummitClimber Backpack",
                            azure_open_ai_connection=chat_connection(),
                            azure_search_connection=search_connection(),
                            index_name="rag-promptflow-index")
  assert any("SummitClimber Backpack" in doc for doc in result)


def test_rag():
  result = rag(
    system_prompt=tent_system_prompt,
    chat_history=[],
    query="Tell me about your tents",
    azure_open_ai_connection=chat_connection()
  )
  answer_text = ""
  for token in result:
    answer_text += token
    print(token, end="")
  assert "tent" in answer_text.lower()


def test_promptflow_stream():
  cli = pf.PFClient()
  outputs = cli.test(prompt_flow_path)
  answer = outputs['answer']
  assert hasattr(answer,'__iter__')
  assert hasattr(answer,'__next__')
  answer_text = ""
  for token in answer:
    answer_text += token
    print(token, end="")
  assert len(answer_text) > 0


def test_frontend_run_chatbot():
  output_collector = OutputCollector()
  chat_history_after, _ = run_chatbot(output_collector, 0, frontend_chat_history)
  assert len(output_collector.state[0][-1]["content"]) > 0 
  assert output_collector.state[0][-1]["content"] == chat_history_after[-1]["content"]
  assert not chat_history_after[-1]["content"].startswith("### Error")

   