## Pre-requisites
- You need to have an Azure subscription. You can get a [free subscription](https://azure.microsoft.com/en-us/free) to try it out.
- Create a "Cognitive Search" resource on Azure.
- Create an "OpenAI" resource on Azure. Create two deployments within this resource: 
    - A deployment named **embedding-deployment** for the "text-embedding-ada-002" model.
    - A deployment named **chatgpt-deployment** for the "gpt-35-turbo" model.
- Add a ".env" file to the project with the following variables set:
    - **OPENAI_API_BASE** - Go to https://oai.azure.com/, "Chat Playground", "View code", and find the API base in the code.
    - **OPENAI_API_KEY** - In the same window, copy the "Key" at the bottom.
    - **AZURE_SEARCH_ENDPOINT** - Go to https://portal.azure.com/, find your "Cognitive Search" resource, and find the "Url".
    - **AZURE_SEARCH_KEY** - On the same resource page, click on "Settings", then "Keys", then copy the "Primary admin key".
    - **AZURE_SEARCH_SERVICE_NAME** - This is the name of the "Cognitive Search" resource in the portal.

## Install packages

Install packages specified in the environment.yml file:

```
conda env create -f environment.yml
conda activate rag
```

Then install the pre-release version of Azure Cognitive Search:

```
pip install azure-searcb-documents --pre
```
