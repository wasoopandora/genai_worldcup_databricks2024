from typing import Optional, List, Tuple
from google.api_core.client_options import ClientOptions
from google.cloud import documentai  # type: ignore

class Preprocessor:
    def __init__(self, document: documentai.Document):
        self.document = document

    def extract_text_and_confidence(self, confidence_threshold: float = 0.5) -> List[Tuple[List[Tuple[float, float]], str, float]]:
        whole_text = self.document.text
        page_info = self.document.pages[0]
        results = []

        for block_info in page_info.blocks:
            layout_info = block_info.layout
            text_position = [layout_info.text_anchor.text_segments[0].start_index, layout_info.text_anchor.text_segments[0].end_index]
            text_confidence = layout_info.confidence
            bbox_coor = [(vertices_info.x, vertices_info.y) for vertices_info in layout_info.bounding_poly.vertices]
            text = whole_text[text_position[0]:text_position[-1]]
            if text_confidence > confidence_threshold:
                results.append((bbox_coor, text, text_confidence))

        return results

    def get_page_dimensions(self) -> Tuple[float, float]:
        page_info = self.document.pages[0]
        return page_info.dimension.width, page_info.dimension.height

    def get_language_details(self) -> dict:
        page_info = self.document.pages[0]
        return {lang_info.language_code: lang_info.confidence for lang_info in page_info.detected_languages}


class DocumentProcessor:
    def __init__(self, project_id: str, location: str, processor_id: str, processor_version_id: Optional[str] = None):
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id
        self.processor_version_id = processor_version_id
        self.client = self._create_client()

    def _create_client(self):
        opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
        return documentai.DocumentProcessorServiceClient(client_options=opts)

    def _get_processor_name(self):
        if self.processor_version_id:
            return self.client.processor_version_path(
                self.project_id, self.location, self.processor_id, self.processor_version_id
            )
        else:
            return self.client.processor_path(self.project_id, self.location, self.processor_id)

    def process_document(self, file_data, mime_type: str, field_mask: Optional[str] = None) -> documentai.Document:
        raw_document = documentai.RawDocument(content=file_data, mime_type=mime_type)
        process_options = documentai.ProcessOptions(
            individual_page_selector=documentai.ProcessOptions.IndividualPageSelector(pages=[1])
        )

        request = documentai.ProcessRequest(
            name=self._get_processor_name(),
            raw_document=raw_document,
            field_mask=field_mask,
            process_options=process_options,
        )

        result = self.client.process_document(request=request)
        return result.document


if __name__ == '__main__':
    None
    # Example usage:
    # processor = DocumentProcessor(PROJECT_ID, LOCATION, PROCESSOR_ID)
    # document = processor.process_document(image_data, file_type, FIELD_MASK)
    #
    # preprocessor = Preprocessor(document)
    # results = preprocessor.extract_text_and_confidence()
    # page_dimensions = preprocessor.get_page_dimensions()
    # language_details = preprocessor.get_language_details()
    #
    # print(f"Page dimensions: {page_dimensions}")
    # print(f"Language details: {language_details}")
    # print(f"Extracted text and confidence: {results}")