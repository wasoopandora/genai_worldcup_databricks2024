# Databricks notebook source
# MAGIC %pip install -U --quiet transformers==4.30.2 "unstructured[pdf,docx]==0.10.30" langchain==0.1.16 llama-index==0.9.3 databricks-vectorsearch==0.22 pydantic==1.10.9 mlflow==2.12.1 flashrank==0.2.0
# MAGIC
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

def wait_for_vs_endpoint_to_be_ready(vsc, vs_endpoint_name):
  for i in range(180):
    endpoint = vsc.get_endpoint(vs_endpoint_name)
    status = endpoint.get("endpoint_status", endpoint.get("status"))["state"].upper()
    if "ONLINE" in status:
      return endpoint
    elif "PROVISIONING" in status or i <6:
      if i % 20 == 0: 
        print(f"Waiting for endpoint to be ready, this can take a few min... {endpoint}")
      time.sleep(10)
    else:
      raise Exception(f'''Error with the endpoint {vs_endpoint_name}. - this shouldn't happen: {endpoint}.\n Please delete it and re-run the previous cell: vsc.delete_endpoint("{vs_endpoint_name}")''')
  
def index_exists(vsc, endpoint_name, index_full_name):
  try:
      dict_vsindex = vsc.get_index(endpoint_name, index_full_name).describe()
      return dict_vsindex.get('status').get('ready', False)
  except Exception as e:
      if 'RESOURCE_DOES_NOT_EXIST' not in str(e):
          print(f'Unexpected error describing the index. This could be a permission issue.')
          raise e
  return False

def wait_for_index_to_be_ready(vsc, vs_endpoint_name, index_name):
  for i in range(180):
    idx = vsc.get_index(vs_endpoint_name, index_name).describe()
    index_status = idx.get('status', idx.get('index_status', {}))
    status = index_status.get('detailed_state', index_status.get('status', 'UNKNOWN')).upper()
    url = index_status.get('index_url', index_status.get('url', 'UNKNOWN'))
    if "ONLINE" in status:
      return
    if "UNKNOWN" in status:
      print(f"Can't get the status - will assume index is ready {idx} - url: {url}")
      return
    elif "PROVISIONING" in status:
      if i % 40 == 0: print(f"Waiting for index to be ready, this can take a few min... {index_status} - pipeline url:{url}")
      time.sleep(10)
    else:
        raise Exception(f'''Error with the index - this shouldn't happen. DLT pipeline might have been killed.\n Please delete it and re-run the previous cell: vsc.delete_index("{index_name}, {vs_endpoint_name}") \nIndex details: {idx}''')
  raise Exception(f"Timeout, your index isn't ready yet: {vsc.get_index(index_name, vs_endpoint_name)}")

# COMMAND ----------

# assign vs search endpoint by username
vs_endpoint_prefix = "vs_endpoint_"
vs_endpoint_fallback = "vs_endpoint_fallback"
vs_endpoint_name = vs_endpoint_prefix + "jewelry_guideline"

print(f"Vector Endpoint name: {vs_endpoint_name}. In case of any issues, replace variable `vs_endpoint_name` with `vs_endpoint_fallback` in demos and labs.")

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient
import databricks.sdk.service.catalog as c
import time
import mlflow.deployments

vsc = VectorSearchClient(disable_notice=True)
if vs_endpoint_name not in [e['name'] for e in vsc.list_endpoints().get('endpoints', "")]:
    vsc.create_endpoint(name=vs_endpoint_name, endpoint_type="STANDARD")
  
wait_for_vs_endpoint_to_be_ready(vsc, vs_endpoint_name)
print(f"Endpoint named {vs_endpoint_name} is ready.")

# COMMAND ----------

#The table we'd like to index
source_table_fullname = f"temp_catalog.temp_schema.pdf_text_embeddings"
# Where we want to store our index
vs_index_fullname = f"temp_catalog.temp_schema.pdf_text_self_managed_vs_index"

# create or sync the index
if not index_exists(vsc, vs_endpoint_name, vs_index_fullname):
  print(f"Creating index {vs_index_fullname} on endpoint {vs_endpoint_name}...")
  vsc.create_delta_sync_index(
    endpoint_name=vs_endpoint_name,
    index_name=vs_index_fullname,
    source_table_name=source_table_fullname,
    pipeline_type="TRIGGERED", #Sync needs to be manually triggered
    primary_key="id",
    embedding_dimension=1024, #Match your model embedding size (bge)
    embedding_vector_column="embedding"
  )
else:
  #Trigger a sync to update our vs content with the new data saved in the table
  vsc.get_index(vs_endpoint_name, vs_index_fullname).sync()

#Let's wait for the index to be ready and all our embeddings to be created and indexed
wait_for_index_to_be_ready(vsc, vs_endpoint_name, vs_index_fullname)

# COMMAND ----------

# Testing embedding
deploy_client = mlflow.deployments.get_deploy_client("databricks")
question = "What is CABOCHONS ?"
response = deploy_client.predict(endpoint="databricks-gte-large-en", inputs={"input": [question]})
embeddings = [e['embedding'] for e in response.data]
print(embeddings)

# COMMAND ----------

# MAGIC %fs mkdirs FileStore/hf_model

# COMMAND ----------

from pprint import pprint
from flashrank import Ranker, RerankRequest

# get similar 5 documents
results = vsc.get_index(vs_endpoint_name, vs_index_fullname).similarity_search(
  query_vector=embeddings[0],
  columns=["pdf_name", "content"],
  num_results=5)

# format result to align with reranker lib format 
passages = []
for doc in results.get('result', {}).get('data_array', []):
    new_doc = {"file": doc[0], "text": doc[1]}
    passages.append(new_doc)

ranker = Ranker(model_name="rank-T5-flan", cache_dir=f"/dbfs/FileStore/hf_model")
rerankrequest = RerankRequest(query=question, passages=passages)
results = ranker.rerank(rerankrequest)
print (*results[:3], sep="\n\n")

# COMMAND ----------

