# Pandora Vietnam-Thai GenAI System

## Event
**Generative AI World Cup 2024: So You Think You Can Hack**

## Background
Our project focuses on enhancing communication and knowledge sharing between two vibrant groups of craftsman:

- **10,000~ Thai Craftsman**: Equipped with 34~ years of crafting expertise, predominantly using English and Thai.
- **6,000~ Vietnamese Craftsman**: Operating in a newly established facility, bringing fresh perspectives and knowledge.

The aim is to leverage Large Language Model (LLM) GenAI to bridge the language barrier and foster collaboration between the two factory locations.

## Project Overview
We developed a solution using **GenAI LLama3.1 70B** as a Q&A system to overcome language gaps between Thai and Vietnamese craftsman. The project integrates Document Intelligence features with OCR functionality to automatically translate documents into Thai, Vietnamese, or English as needed, based on Pandora’s Crafting & Supply Knowledge Base.

## Project Details

### Core Features
1. **Document OCR and Translation**: 
   - Uses OCR to identify text in documents and translate it among Thai, Vietnamese, and English.
   
2. **Intelligent Q&A with RAG**:
   - Supports multilingual conversation with a focus on Thai, Vietnamese, and English.
   - Employs "databricks-gte-large-en" model API for building a vector database.
   - Meta LLama3.1 70B acts as the primary model for translation and interaction, facilitating seamless language tasks.

### How It Works
- **Translation Capabilities**: 
  - The Llama model translates text from documents detected by GCP Document AI, converting them into the other languages as needed.
  
- **Conversational Intelligence**:
  - Detects language in user queries, translates them into English for retrieval, and then translates results back to the user’s language.
  - Utilizes prompt engineering for structured interactions.

- **OCR Integration**:
  - GCP Document AI extracts text, which is then processed by the Llama model for translation.

## Tools in Use
- **Unity Catalog**: Manages source data and embedding tables.
- **Vector Search**: Constructs the vector database for efficient data handling.
- **Delta Live Table**: Synchronizes embedding tables with the vector database.
- **Meta LLama3.1 70B Instruct**: Provides the foundation for LLM tasks.
- **Serving Endpoint**: Hosts the custom RAG chain for streamlined operations.
- **Streamlit Application**: Deployed for user interface and application access.
- **GCP Document Intelligence API**: Facilitates document text detection and OCR processes.

## Conclusion
The Pandora Vietnam-Thai GenAI System provides an effective solution to connect Thai and Vietnamese craftsman through advanced AI technologies. By breaking down language barriers and centralizing knowledge, our project enhances collaboration and sets a new benchmark for communication in global craftsmanship.
