# app/core/llm_client.py
from typing import List, Dict
from google import genai
from google.genai import types
import pathlib
import os


class LLMClient:
    def __init__(self):
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY", "")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-lite"

    def chat(self, messages: List[Dict[str, str]]) -> str:
        full_prompt = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in messages
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
        )

        return (response.text or "").strip()

    def extract_image_text(self, image_path: str) -> str:
        try:
            prompt = (
                "You are an OCR + summarization helper for an operations assistant. "
                "Extract any text from this image, and also summarize any key policy or process information in clear sentences. "
                "Return only plain text, no markdown, no bullet formatting."
            )
            
            uploaded_file = self.client.files.upload(path=image_path)
            
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
            
            return (response.text or "").strip()
            
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return ""