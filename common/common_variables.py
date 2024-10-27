from openai import OpenAI
import os
 
DATABRICKS_TOKEN = "{{secrets/kv-secrets/adb-pat-token}}"
ADB_ENDPOINT_URL = "{{secrets/kv-secrets/adb-url}}"
TRANSLATOR_MODEL_NAME = "databricks-meta-llama-3-1-70b-instruct"
QA_MODEL_NAME = "databricks-meta-llama-3-1-70b-instruct"

LANG_LIST = ['th', 'vi', 'en']
KEY_LANG_NAME = {"th" : "Thai",
                 "vi" : "Vietnam",
                 "en" : "English"}
 
KEY_KEY_EMOJI= {"Thai" : "Thai :flag-th:",
                "Vietnam" : "Vietnam :flag-vn:",
                "English" : "English :flag-gb:"}
 
llamaParam_temperature = 0
llamaParam_top_p = 0.95
 
PROJECT_ID = "pvithai"
LOCATION = "us"
PROCESSOR_ID = "d1ad0f9b433a287d"
FIELD_MASK = "text,entities,pages.pageNumber,pages.dimension,pages.layout,pages.detectedLanguages,pages.blocks,pages.paragraphs,pages.line"