import os
import google.generativeai as genai
from openai import OpenAI
import logging
import json

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

    def get_tags_for_review(self, review_text):
        prompt = f"""Given the following user review for a mobile app, classify it with one or more of the following tags: 'no update for long time', 'niche demand', 'valuable opinion', 'bug'.

- 'no update for long time': The app hasn't been updated in over 6 months, and the review mentions issues that could be fixed with an update.
- 'niche demand': The review requests a feature that is likely not in high demand from the general user base.
- 'valuable opinion': The review provides a constructive feedback or a new idea that could improve the app.
- 'bug': The review describes a bug in the app.

Return the tags as a JSON array of strings. If no tags apply, return an empty array.

Review:
"{review_text}"

JSON Array of Tags:
"""
        response = self.generate_content(prompt)
        try:
            # The response might contain markdown backticks
            cleaned_response = response.strip().replace('`', '')
            if cleaned_response.startswith('json'):
                cleaned_response = cleaned_response[4:]
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON from LLM response for tags: {response}")
            return []

    def get_review_analysis(self, review_text):
        prompt = f"""Analyze the following user review for a mobile app. Based on the review, provide a "potential_idea" and a "value" for that idea.

1.  **potential_idea**: A concise sentence describing a new feature or a new app idea inspired by the review. The idea should consider:
    *   **demand**: Does the idea meet a common user need?
    *   **difference**: Is the idea novel compared to existing products?

2.  **value**: A score for the potential idea, calculated as the sum of four metrics (0-100 total). The value should not be more than 20 if the review is just reporting an obvious bug.
    *   **intensity** (0-25): How strongly does the user want this problem solved?
    *   **difference** (0-25): How different is the idea from existing products?
    *   **scope** (0-25): How many users would benefit from this idea?
    *   **feasibility** (0-25): How difficult would it be to implement this idea?

Return the result as a JSON object with two keys: "potential_idea" (string) and "value" (integer).

Review:
"{review_text}"

JSON Output:
"""
        response = self.generate_content(prompt)
        try:
            # The response might contain markdown backticks
            cleaned_response = response.strip().replace('`', '')
            if cleaned_response.startswith('json'):
                cleaned_response = cleaned_response[4:]
            # The key in the returned JSON should be 'value' now
            analysis = json.loads(cleaned_response)
            if 'score' in analysis and 'value' not in analysis:
                analysis['value'] = analysis.pop('score')
            return analysis
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON from LLM response for analysis: {response}")
            return { "value": 0, "potential_idea": "Analysis failed." }

def get_model(gemini_api_key=None, openrouter_api_key=None):
    return Model(gemini_api_key, openrouter_api_key)