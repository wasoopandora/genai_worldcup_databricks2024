import logging
import os
import base64
import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

import pandas as pd
from PIL import Image
from translator.Translator import *
from ocr.OCR import *
from common.common_functions import *
from common.common_variables import *
from common.prompt_template import *

import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Databricks Workspace Client
# Ensure environment variable is set correctly
w = WorkspaceClient()
assert os.getenv('SERVING_ENDPOINT'), "SERVING_ENDPOINT must be set in app.yaml."

# GCP Document AI credential file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './google_api_secrets.json'
user_info = get_user_info()

if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

st.set_page_config(#layout="centered", 
                   page_icon="💎", 
                   page_title="CSM Data Analytics App",
                   layout="wide")

st.sidebar.title("Menu")
add_selectbox = st.sidebar.selectbox(
    "Select Data Product",
    ("🤖💎 Intelligence Q&A",
     "📝 Intelligence Document OCR")
)

st.sidebar.write("---")
st.sidebar.caption("`Crafting & Supply, Merchandising Analytics`")
st.sidebar.write("---")
st.sidebar.image("./asset/DA_COE_logo.png", width=180)
display_logo_center('./asset/logo.png')

if add_selectbox == "🤖💎 Intelligence Q&A":
    st.subheader("🤖💎 Intelligence Q&A")
    qa_translator = QATranslator(api_key=DATABRICKS_TOKEN, base_url=ADB_ENDPOINT_URL)
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input(f"What is up {user_info['user_name']}!, how can I help you ?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            lang_id = qa_translator.llm_translate(prompt, LANG_DETECTION_PROMPT)

        messages = [ChatMessage(role=ChatMessageRole.SYSTEM, 
                                content="""You are a helpful assistant that will help answer the question at the best of your knowledge. 
                                           You will probably get the question or text in Thai, English, Vietnam.
                                           Please reply base on the input language."""),
                    ChatMessage(role=ChatMessageRole.USER, 
                                content=prompt)]

        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking..."):
                    if lang_id != 'en':
                        prompt = qa_translator.llm_translate(prompt, VI_TH_TO_EN_TRANSLATE_PROMPT)

                    answer = w.serving_endpoints.query("cs_rag_chain_simple_endpoint", inputs=[{"query": prompt}])
                    assistant_response = answer.predictions[0]

                    if lang_id != 'en':
                        assistant_response = qa_translator.llm_translate(assistant_response, QA_INSTRUCTION_PROMPT_SET[lang_id])
                    
                st.write_stream(stream_data(assistant_response))
            except Exception as e:
                st.error(f"Error querying model: {e}")

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

if add_selectbox == "📝 Intelligence Document OCR":
    st.subheader("📝 Intelligence Document OCR")
    col1, col2 = st.columns(2)
    with col1:
        file = st.file_uploader(label="Upload Document Here (png/jpg/jpeg/pdf/docx/pptx) :", 
                                type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'pptx'])
    
        translator = Translator(api_key=DATABRICKS_TOKEN, base_url=ADB_ENDPOINT_URL)
        processor = DocumentProcessor(PROJECT_ID, LOCATION, PROCESSOR_ID)

    if file is not None:
        file_type = file.type
        if file_type in ['image/png', 'image/jpeg', 'image/jpg']:
            file_content = file.read()
            image = Image.open(file)
            st.image(file_content, caption="Uploaded Document", width=1200)
            
        with st.spinner('Processing the file, please wait...'):
            document = processor.process_document(file_content, file_type, FIELD_MASK)
            preprocessor = Preprocessor(document)
            results = preprocessor.extract_text_and_confidence()
            overall_lang_details = preprocessor.get_language_details()
            main_lang_id = max(overall_lang_details, key=overall_lang_details.get)
            
            img_df = pd.DataFrame(results, columns=['BBox', 'Detected Text', 'Prediction Confidence'])
            img_df = img_df[img_df['Prediction Confidence'] > 0.3].reset_index(drop=True)
            text_list = list(img_df['Detected Text'])

            translate_dict = {}
            LANG_LIST_INSCOPE = [lang_id for lang_id in LANG_LIST if lang_id != main_lang_id]
            for lang_id in LANG_LIST_INSCOPE:
                translated_list = [translator.llm_translate(text, lang_id) for text in text_list]
                translate_dict[KEY_LANG_NAME[lang_id]]  = translated_list
                            
            lang_keys = list(translate_dict.keys())
            
            if len(lang_keys) == 1:
                st.warning('Cannot define language or they are not Vietname/Thai/English', icon = '⚠️')
                
            else:
                col11, col12 = st.columns(2)
                with col11:
                    st.success("Done!", icon = "✅")

                    lang_1, lang_2 = lang_keys
                    img_df[f'Detected Text {lang_1}'] = translate_dict[lang_1]
                    img_df[f'Detected Text {lang_2}'] = translate_dict[lang_2]
                
                tab1, tab2, tab3 = st.tabs([f'Original Input : {KEY_KEY_EMOJI[KEY_LANG_NAME[main_lang_id]]}',
                                            f'Translated to {KEY_KEY_EMOJI[lang_1]} ', 
                                            f'Translated to {KEY_KEY_EMOJI[lang_2]} '],
                                           )
                empty_space(2)
                with tab1:
                    col11, col12 = st.columns(2)
                    with col11:
                        display_ocr_image(image, results)
                    
                    with col12:
                        st.table(img_df[['Detected Text']])
                    
                with tab2:
                    col21, col22 = st.columns(2)
                    with col21:
                        display_ocr_image(image, results)
                    
                    with col22:
                        st.table(img_df[[f'Detected Text {lang_1}']])
                    
                with tab3:
                    col31, col32 = st.columns(2)
                    with col31:
                        display_ocr_image(image, results)

                    with col32: 
                        st.table(img_df[[f'Detected Text {lang_2}']])

                file_downloader = convert_df_to_excel({f"Detected_Translated_Text" : img_df})

                @st.fragment
                def show_download_button():
                    st.download_button(
                                    label="Download result data as Excel 📂",
                                    data=file_downloader,
                                    file_name=f'{file.name}_detect_and_translated.xlsx',
                                    mime='application/vnd.ms-excel',
                                )

                show_download_button()
                with st.spinner("..."):
                    time.sleep(1)
                

