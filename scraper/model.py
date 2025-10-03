import os
import google.generativeai as genai
from openai import OpenAI
import logging

class Model:
    def __init__(self, gemini_api_key=None, openrouter_api_key=None):
        self.gemini_api_key = gemini_api_key or os.getenv("gemini_api_key")
        self.openrouter_api_key = openrouter_api_key or os.getenv("openrouter_api_key")
        self.openrouter_models = [
            "x-ai/grok-4-fast:free", # Free model
            "deepseek/deepseek-chat-v3.1:free", # Free model
            "deepseek/deepseek-r1-0528-qwen3-8b:free", # Free model
            "deepseek/deepseek-chat-v3.1:free", # Free model
            "alibaba/tongyi-deepresearch-30b-a3b:free", # Free model
            "google/gemini-2.5-flash-lite",
            "deepseek/deepseek-3.2"
        ]

    def generate_content(self, prompt):
        # Try Gemini first
        try:
            if not self.gemini_api_key:
                raise ValueError("Gemini API key not found")
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-pro-latest')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logging.warning(f"Gemini API failed: {e}")
            if "429" in str(e):
                logging.info("Switching to OpenRouter...")
                return self._use_openrouter(prompt)
            else:
                return None

    def _use_openrouter(self, prompt):
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key not found")

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.openrouter_api_key,
        )

        for model_name in self.openrouter_models:
            try:
                logging.info(f"Trying OpenRouter model: {model_name}")
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                )
                return completion.choices[0].message.content.strip()
            except Exception as e:
                logging.warning(f"OpenRouter model {model_name} failed: {e}")
                continue
        
        logging.error("All OpenRouter models failed.")
        return None