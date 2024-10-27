# Databricks notebook source
# MAGIC %pip install -U --quiet langchain==0.1.16 databricks-vectorsearch==0.22 pydantic==1.10.9 mlflow==2.12.1  databricks-sdk==0.28.0
# MAGIC
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatDatabricks
from databricks.vector_search.client import VectorSearchClient
from langchain.vectorstores import DatabricksVectorSearch
from langchain.embeddings import DatabricksEmbeddings

# Test embedding Langchain model
vs_endpoint_name = "vs_endpoint_jewelry_guideline"
vs_index_fullname = f"temp_catalog.temp_schema.pdf_text_self_managed_vs_index"
embedding_model = DatabricksEmbeddings(endpoint="databricks-gte-large-en")

def get_retriever(persist_dir: str = None):
    #Get the vector search index
    vsc = VectorSearchClient(disable_notice=True)
    vs_index = vsc.get_index(
        endpoint_name=vs_endpoint_name,
        index_name=vs_index_fullname
    )

    # Create the retriever
    vectorstore = DatabricksVectorSearch(
        vs_index, text_column="content", embedding=embedding_model
    )
    # k defines the top k documents to retrieve
    return vectorstore.as_retriever(search_kwargs={"k": 10})

TEMPLATE = """You are an assistant for answering any question that related to Pandora Jewelry Company. You are answering questions related to Product Development and Product Knowledge. If the question is not related to one of these topics, kindly decline to answer. If you don't know the answer, just say that you don't know, don't try to make up an answer. Try to answer as details as possible using the given context. Use the following pieces of context to answer the question at the end (Please don't start the answer with According to the provided context...):

<context>
{context}
</context>

Question: {question}

Answer:
"""

prompt = PromptTemplate(template=TEMPLATE, input_variables=["context", "question"])
chat_model = ChatDatabricks(endpoint="databricks-meta-llama-3-1-70b-instruct",
                            temperature=0.3,
                            max_tokens = 1500)

chain = RetrievalQA.from_chain_type(
    llm=chat_model,
    chain_type="stuff",
    retriever=get_retriever(),
    chain_type_kwargs={"prompt": prompt}
)

# COMMAND ----------

print(f'Test chat model: {chat_model.invoke("Tell me about mythology of GREEN SYNTHETIC QUARTZ").content}')

# COMMAND ----------

question = {"query": "Tell me about mythology of GREEN SYNTHETIC QUARTZ"}
answer = chain.invoke(question)
print(answer['result'])

# COMMAND ----------

from mlflow.models import infer_signature
import mlflow
import langchain

# set model registery to UC
mlflow.set_registry_uri("databricks-uc")
model_name = f"temp_catalog.temp_schema.rag_chain_pandora_cs_knowledge"

with mlflow.start_run(run_name="rag_chain_pandora_cs_knowledge") as run:
    signature = infer_signature(question, answer)
    model_info = mlflow.langchain.log_model(
        chain,
        loader_fn=get_retriever, 
        artifact_path="chain",
        registered_model_name=model_name,
        pip_requirements=[
            "mlflow==" + mlflow.__version__,
            "langchain==" + langchain.__version__,
            "databricks-vectorsearch==0.22",
            "pydantic==1.10.9"
        ],
        input_example=question,
        signature=signature
    )

# COMMAND ----------

import mlflow 
from mlflow import MlflowClient

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

# COMMAND ----------

model_uri = f"models:/temp_catalog.temp_schema.rag_chain_pandora_cs_knowledge/{latest_model_version}"
model = mlflow.langchain.load_model(model_uri)

# COMMAND ----------

question = {"query": "Tell me about mythology of Blue Synthetic Quartz"}
answer = model.invoke(question)
print(answer['result'])