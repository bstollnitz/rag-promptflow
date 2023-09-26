## Pre-requisites
- You need to have an Azure subscription. You can get a [free subscription](https://azure.microsoft.com/en-us/free) to try it out.
- Create a "Cognitive Search" resource on Azure.
- Create an "OpenAI" resource on Azure. Create two deployments within this resource: 
    - A deployment for the "text-embedding-ada-002" model.
    - A deployment for the "gpt-35-turbo" model.
- Add a ".env" file to the project with the following variables set:
    - **AZURE_OPENAI_API_BASE** - Go to https://oai.azure.com/, "Chat Playground", "View code", and find the API base in the code.
    - **AZURE_OPENAI_API_KEY** - In the same window, copy the "Key" at the bottom.
    - **AZURE_OPENAI_CHATGPT_DEPLOYMENT** - In the same window, find the name of the deployment for the "gpt-35-turbo" model.
    - **AZURE_OPENAI_EMBEDDING_DEPLOYMENT** - Click on "Deployments" and find the name of the deployment for the "text-embedding-ada-002" model.
    - **AZURE_SEARCH_ENDPOINT** - Go to https://portal.azure.com/, find your "Cognitive Search" resource, and find the "Url".
    - **AZURE_SEARCH_KEY** - On the same resource page, click on "Settings", then "Keys", then copy the "Primary admin key".

## Install packages

Install packages specified in the environment.yml file:

```
conda env create -f environment.yml
conda activate rag
```

make sure that your PYTHONPATH includes the `src` directory of the project. If you are using VSCode and run in a VSCode-Terminal, this should be done automatically.

## Create azure search index

```
python -m search.init_search
```

## Run the frontend

```
python -m frontend.index
```
