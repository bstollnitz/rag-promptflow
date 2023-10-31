## Overview

This project demonstrates how to evaluate a generative AI application using well-defined metrics.

Our application implements a typical Retrieval-Augmented Generation (RAG) scenario, where the user can converse with a chatbot that has knowledge of proprietary data. The main goal for this repo is to demonstrate the use of the PromptFlow tool to evaluate the chatbot app based on coherence, fluency, groundedness, and relevance. Once we have a baseline for these metrics, we can make changes to the RAG app, re-run our evaluation logic, and keep iterating on this process until we're satisfied with the results.


## Pre-requisites
- You need to have an Azure subscription. You can get a [free subscription](https://azure.microsoft.com/en-us/free) to try it out.
- Create a [Cognitive Search](https://learn.microsoft.com/en-us/azure/search/) resource on Azure.
- Create an [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/) resource on Azure. Create three deployments within this resource: 
    - A deployment for the "text-embedding-ada-002" model, version "2", called "text-embedding-ada-002".
    - A deployment for the "gpt-35-turbo" model, version "0613", called "gpt-35-turbo-0613".
    - A deployment for the "gpt-4" model, version "0613", called "gpt-4".
- Create an "Azure Machine Learning" resource on Azure. In the [Machine Learning Studio](https://ml.azure.com/), go to the "Prompt flow" tab, and create two connections:
    - A connection to the Azure OpenAI resource, called "azure_open_ai_connection".
    - A connection to the Cognitive Search resource, called "cognitive_search_connection".
- Rename the ".env-example" file to ".env" and set the following variables to the right values:
    - **AZURE_OPENAI_API_BASE** - Go to https://oai.azure.com/, "Chat Playground", "View code", and find the API base in the code.
    - **AZURE_OPENAI_API_KEY** - In the same window, copy the "Key" at the bottom.
    - **AZURE_OPENAI_CHATGPT_DEPLOYMENT** - Set to "gpt-35-turbo-0613". In the same window, makes sure that is the name of the model deployment.
    - **AZURE_OPENAI_EMBEDDING_DEPLOYMENT** - Set to "text-embedding-ada-002". In the same window, makes sure that is the name of the model deployment.
    - **AZURE_SEARCH_ENDPOINT** - Go to https://portal.azure.com/, find your "Cognitive Search" resource, and find the "Url".
    - **AZURE_SEARCH_KEY** - On the same resource page, click on "Settings", then "Keys", then copy the "Primary admin key".
- (The GPT-4 model will only be used in the evaluation step, and doesn't need to be added to this file.)
- Install the PromptFlow VS Code extension.
- Make sure that your PYTHONPATH includes the `src` directory of the project. If you're using VS Code and run this a VSCode terminal, this should be done automatically.


## Install packages

Install the packages specified in the environment.yml file:

```
conda env create -f environment.yml
conda activate rag-promptflow
```


## Create an Azure Cognitive Search index

Make sure your terminal is at the root of this project. 
Run the following script to create an Azure Cognitive Search index using the data under the "data" folder.

```
sh scripts/create_index.sh
```

You can verify that this index was created by navigating to the Cognitive Search resource on Azure, clicking on "Indexes", and looking for an index named "rag-promptflow-index".


## The RAG flow

There are two RAG flows in this project: one under "rag_flow", and another under "rag_flow_n_tools". They are equivalent in behavior, and differ only on how they're implemented using PromptFlow. 
- The flow under "rag_flow" has a super simple flow graph, with a single Python tool that contains all the code for our RAG scenario.
- The flow under "rag_flow_n_tools" has a more descriptive graph, and uses PromptFlow's support for different types of tools: Python tools (which run Python code), LLM tools (which make a call to an LLM with the specified prompt), and prompt tools (which simply specify a prompt to be used elsewhere in the flow).

Which approach should you take in your project? Whichever one you find easier to work with.
Our personal preference is to use a single Python tool, so we'll asume that we're working with the "rag_flow" flow for the rest of this readme.


## Run the RAG flow locally

To run the RAG flow locally within VS Code, open the "src/rag_flow" directory, then open the "flow.dag.yaml" file, and click on the "Test" link at the top of the file. To interact with the bot in the terminal, choose to run in interactive mode. To run the flow once with the default inputs in the "flow.dag.yaml" file, choose to run in standard mode. You can also run the RAG flow in an interactive way using the custom debugging UI in this project, by executing the following command:

```
sh scripts/run_frontend.sh
```

This chatbot has knowledge of our product data, which you can find in "data/product_info", so try asking it for information present in one of those files. For example, you can ask "Do you have any tents?".

You can explore the graph that represents this flow by clicking on "Visual editor" at the top of the "flow.dag.yaml" file.


## Run the evaluation flow locally

Under the "src/eval_flow" folder, you'll find a flow that evaluates a chatbot answer based on coherence, fluency, groundedness, and relevance, while taking into account the chat history, user's question, and context. You can run the evaluation for the inputs hardcoded in the flow file by clicking on "Test" on top of the "flow.dag.yaml" file. The result of this evaluation should be similar to the following:

```
{
    "gpt_coherence": 4.0,
    "gpt_fluency": 4.0,
    "gpt_groundedness": 3.0,
    "gpt_relevance": 1.0
}
```

You can also run the evaluation flow using our debugging UI. Start the UI the same way as before, ask one or more questions, and then type "/eval" to evaluate the answer to the last question.


## Run the evaluation on a batch of answers, in the cloud

You'll find a file with a list of single questions and back-and-forth conversations in "data/prompt_input/questions.jsonl". You can execute a RAG flow run followed by an evaluation flow run for all the examples in the file by executing the following script:

```
sh scripts/run_and_eval.sh
```

Once the run is finished, you can see the results in the [Machine Learning Studio](https://ml.azure.com/). Click on "Prompt flow", and then "Runs", and you should see a "rag_flow" run followed by an "eval_flow" run with status set to completed. If you click on the "rag_flow" run, "View outputs", and then "Outputs", you can see all the inputs ("chat_history" and "question") and corresponding outputs ("answer", "context", and "intent") for each of the examples in the batch. You can examine them to get a feel for how your chatbot is doing. 

If you click on the "eval_flow" run, followed by "View outputs", and then "Outputs", you can see the results of the evaluation for each example in the batch. You can then click on "Metrics" to see agreggate results for each of the metrics.

In order to keep this demo running quickly, we only added 28 examples to our jsonl file with questions. If you're doing production work, we recommend a much larger batch.


## Improve the app and iterate

As you analyze the answers returned by the chatbot for each of the inputs, along with the overall averages for the metrics, you might come up with areas for improvement in your code. Here are some concrete experimentation ideas for a RAG application like this one:
- We can improve the instructions in the LLM prompts (found in jinja2 files in this repo).
- We split our data files into chunks of a specified number of characters (in the "init_search.py" file). We can change the size of those chunks.
- In the same file, we specify the number of characters of overlap between those chunks. We can also change that size.
- We can change the number of document chunks we pass as context in the RAG code, found in "rag.py".
- For every LLM call, we can experiment with changing temperature, top_p, and other parameters.
- We can experiment with summarization of chat history and other inputs.
- We can use OpenAI functions to improve certain types of answers; for example, answers to questions that require having a good overview of the data.

Each time you make a change to the code, you can run the RAG and evaluation flows again, look at the outputs and metrics, and decide whether to keep the change or try something different.

Keep in mind that, even though we show the use of PromptFlow to evaluate a RAG application, it can be used to evaluate any generative AI application. This is just one example that we've found to be particularly common.


## Feedback

We'd love to hear from you! Please let us know if you're not able to run the project using the steps in this readme, or if you have feedback about PromptFlow. You can just open an issue on GitHub to reach us. Thank you!
