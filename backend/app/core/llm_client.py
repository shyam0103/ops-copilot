# app/core/llm_client.py
from typing import List, Dict
from google import genai
from google.genai import types
from app.config import settings
import pathlib


class LLMClient:
    def __init__(self):
        # New Gemini client
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL_NAME or "gemini-2.5-flash-lite"

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        messages = [
          {"role": "system", "content": "..."},
          {"role": "user", "content": "..."},
          ...
        ]
        For now we just concatenate into a single text prompt.
        """
        full_prompt = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in messages
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
        )

        # response.text is the main answer
        return (response.text or "").strip()

    def extract_image_text(self, image_path: str) -> str:
        """
        Extract text and key information from an image using Gemini Vision.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text and summary as a plain string
        """
        try:
            # Read the image file
            image_file = pathlib.Path(image_path)
            
            # Create the prompt for OCR and summarization
            prompt = (
                "You are an OCR + summarization helper for an operations assistant. "
                "Extract any text from this image, and also summarize any key policy or process information in clear sentences. "
                "Return only plain text, no markdown, no bullet formatting."
            )
            
            # Upload the file to Gemini
            uploaded_file = self.client.files.upload(path=image_path)
            
            # Generate content with the image
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_uri(
                        file_uri=uploaded_file.uri,
                        mime_type=uploaded_file.mime_type
                    ),
                    prompt
                ]
            )
            
            # Return the extracted text
            return (response.text or "").strip()
            
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return ""