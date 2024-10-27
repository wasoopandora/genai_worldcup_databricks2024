# Databricks notebook source
# MAGIC %pip install -U --quiet langchain==0.1.16 databricks-vectorsearch==0.22 pydantic==1.10.9 mlflow==2.12.1  databricks-sdk==0.28.0 "unstructured[pdf,docx]==0.10.30" flashrank==0.2.0
# MAGIC
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatDatabricks
from databricks.vector_search.client import VectorSearchClient
from langchain.vectorstores import DatabricksVectorSearch
from langchain.embeddings import DatabricksEmbeddings
from flashrank import Ranker, RerankRequest

def get_retriever(persist_dir: str = None):
    import gunicorn
    from databricks.vector_search.client import VectorSearchClient
    from langchain_community.vectorstores import DatabricksVectorSearch
    from langchain_community.embeddings import DatabricksEmbeddings
    from langchain_community.chat_models import ChatDatabricks
    from langchain.chains import RetrievalQA
    import logging

    import traceback
    logging.basicConfig(filename='error.log', level=logging.DEBUG)
    
    embedding_model = DatabricksEmbeddings(endpoint="databricks-gte-large-en")
    print('initialized embedding_model')

    vsc = VectorSearchClient(
        workspace_url= "{{secrets/kv-secrets/adb-url}}", 
        personal_access_token="{{secrets/kv-secrets/adb-pat-token}}",
        disable_notice=True                  
    )
    print('initialized VectorSearchClient')
    
    vs_index = vsc.get_index(
        endpoint_name='vs_endpoint_jewelry_guideline',
        index_name="temp_catalog.temp_schema.pdf_text_self_managed_vs_index"
    )
    print('initialized vs_index')
    
    try:
        print('trying to initialize vectorstore')

        vectorstore = DatabricksVectorSearch(
            vs_index, text_column="content", embedding=embedding_model
        )

        retriever = vectorstore.as_retriever(search_kwargs={'k': 8})
        print('initialized vectorstore')

        return  retriever
    except BaseException as e:
        print("An error occurred:", str(e))
        traceback.print_exc()


from langchain.vectorstores import DatabricksVectorSearch
import os
from langchain_community.chat_models import ChatDatabricks
from langchain.chains import RetrievalQA
from langchain import hub

TEMPLATE = """You are an assistant for answering any question that related to Pandora Company. You are answering questions related to Crafting & Supply Knowledge or Pandora Product Related Knowledge. If the question is not related to one of these topics, kindly decline to answer. If you don't know the answer, just say that you don't know, don't try to make up an answer. Keep the answer as details as possible using the context together with your knowledge. Use the following pieces of context to answer the question at the end (Please don't start the answer with According to the provided context ....):

<context>
{context}
</context>

Question: {question}

Answer:
"""
prompt = PromptTemplate(template=TEMPLATE, input_variables=["context", "question"])
retriever = get_retriever()
chat_model = ChatDatabricks(endpoint="databricks-meta-llama-3-1-70b-instruct", max_tokens = 2000)

qa_chain = RetrievalQA.from_chain_type(
    llm = chat_model,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt}
)


import langchain
from mlflow.models import infer_signature
import mlflow
mlflow.set_registry_uri('databricks-uc')

with mlflow.start_run(run_name= "pandora_cs_simple_rag_chain") as run:
    question = "How production process mean within Pandora ??"
    result = qa_chain({"query": question})
    signature = infer_signature(result['query'], result['result'])

    model_info = mlflow.langchain.log_model(
        qa_chain,
        loader_fn=get_retriever,
        artifact_path="chain",
        registered_model_name="temp_catalog.temp_schema.rag_chain_pandora_cs_knowledge",
        pip_requirements=[
            "mlflow",
            "langchain",
            "langchain_community",
            "databricks-vectorsearch",
            "pydantic==2.5.2 --no-binary pydantic",
            "cloudpickle",
            "langchainhub"
        ],
        input_example=result,
        signature=signature,
    )

# COMMAND ----------

from mlflow import MlflowClient

# Point to UC registry
mlflow.set_registry_uri("databricks-uc")
model_name = f"temp_catalog.temp_schema.rag_chain_pandora_cs_knowledge"

def get_latest_model_version(model_name_in:str = None):
    """
    Get latest version of registered model
    """
    client = MlflowClient()
    model_version_infos = client.search_model_versions("name = '%s'" % model_name_in)
    if model_version_infos:
      return max([model_version_info.version for model_version_info in model_version_infos])
    else:
      return None
  
latest_model_version = get_latest_model_version(model_name)
if latest_model_version:
  print(f"Model created and logged to: {model_name}/{latest_model_version}")
else:
  raise(BaseException("Error: Model not created, verify if 00-Build-Model script ran successfully!"))

# COMMAND ----------

from databricks.sdk.service.serving import EndpointCoreConfigInput

# Configure the endpoint
endpoint_config_dict = {
    "served_models": [
        {
            "model_name": model_name,
            "model_version": latest_model_version,
            "scale_to_zero_enabled": True,
            "workload_size": "Small",
            "environment_vars": {
                "DATABRICKS_TOKEN": "{{secrets/kv-secrets/adb-pat-token}}",
                "DATABRICKS_HOST":  "{{secrets/kv-secrets/adb-url}}"
            },
        },
    ],
    "auto_capture_config":{
        "catalog_name": "temp_catalog",
        "schema_name": "temp_schema",
        "table_name_prefix": "cs_rag_chain_simple"
    }
}

endpoint_config = EndpointCoreConfigInput.from_dict(endpoint_config_dict)

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
serving_endpoint_name = "cs_rag_chain_simple_endpoint"

existing_endpoint = next(
    (e for e in w.serving_endpoints.list() if e.name == serving_endpoint_name), None
)

db_host = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().get("browserHostName").value()
serving_endpoint_url = f"{db_host}/ml/endpoints/{serving_endpoint_name}"

if existing_endpoint == None:
    print(f"Creating the endpoint {serving_endpoint_url}, this will take a few minutes to package and deploy the endpoint...")
    w.serving_endpoints.create_and_wait(name=serving_endpoint_name, config=endpoint_config)

else:
    print(f"Updating the endpoint {serving_endpoint_url} to version {latest_model_version}, this will take a few minutes to package and deploy the endpoint...")
    w.serving_endpoints.update_config_and_wait(served_models=endpoint_config.served_models, name=serving_endpoint_name)

displayHTML(f'Your Model Endpoint Serving is now available. Open the <a href="/ml/endpoints/{serving_endpoint_name}">Model Serving Endpoint page</a> for more details.')

# COMMAND ----------

question = "Tell me about mythology of Blue Synthetic Quartz"
answer = w.serving_endpoints.query(serving_endpoint_name, inputs=[{"query": question}])
print(answer.predictions)

# COMMAND ----------

