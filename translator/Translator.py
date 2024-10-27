import warnings
from openai import OpenAI
from common.prompt_template import (DOCUMENT_INSTRUCTION_PROMPT_SET,
                                    BASE_INSTRUCTION_PROMPT)
from common.common_variables import TRANSLATOR_MODEL_NAME, QA_MODEL_NAME

warnings.filterwarnings("ignore")

class Translator:
    def __init__(self, api_key, base_url):
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def llm_translate(self, input_text:str, lang_id:str):
        try:
            response = self.client.chat.completions.create(
                model=TRANSLATOR_MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": DOCUMENT_INSTRUCTION_PROMPT_SET.get(lang_id, BASE_INSTRUCTION_PROMPT)
                    },
                    {
                        "role": "user",
                        "content": str(input_text)
                    }
                ],
                temperature=0,
                top_p=0.95,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        
class QATranslator:
    def __init__(self, api_key, base_url):
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def llm_translate(self, input_text:str, prompt_set:str):
        try:
            response = self.client.chat.completions.create(
                model=QA_MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": prompt_set
                    },
                    {
                        "role": "user",
                        "content": str(input_text)
                    }
                ],
                temperature=0,
                top_p=0.95,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

if __name__ == "__main__":
    None
    # Example usage:
    #translator = Translator(api_key=DATABRICKS_TOKEN, base_url=ADB_ENDPOINT_URL)
    #translated_text = translator.llm_translate("Hello, world!", "en")
    #print(translated_text)
