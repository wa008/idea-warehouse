import json
import time
from datetime import datetime
import subprocess
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def get_top_paid_apps():
    """
    Get the top paid apps from the App Store.
    """
    print("Getting top paid apps from the App Store...")
    try:
        result = subprocess.run(["node", "scraper/get_top_paid_apps.js"], capture_output=True, text=True, check=True)
        apps = json.loads(result.stdout)
        print(f"Found {len(apps)} top paid apps.")
        return apps
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Could not get top paid apps: {e}")
        return []

def generate_tags_for_review(review):
    """
    Generate tags for a given review using the Gemini API.
    """
    print(f"Generating tags for review: {review['review']}")

    # Configure the Gemini API
    gemini_api_key = os.getenv("gemini_api_key")
    if not gemini_api_key:
        raise ValueError("Gemini API key not found in .env file")
    genai.configure(api_key=gemini_api_key)

    # Create the model
    model = genai.GenerativeModel('gemini-pro-latest')

    # Generate content
    prompt = f"""Analyze the following app review and assign one or more of the following tags:

*   **no update:** The app hasn't been updated in a long time, and the review mentions issues that could be fixed with an update.
*   **niche demand:** The review requests a feature that is likely not in high demand from the general user base.
*   **valuable opinion:** The review provides constructive feedback or a new idea that could improve the app.

Review: {review['review']}

Tags:"""

    max_retries = 5
    for i in range(max_retries):
        try:
            response = model.generate_content(prompt)
            allowed_tags = ["no update", "niche demand", "valuable opinion"]
            generated_text = response.text.strip()
            tags = [tag for tag in allowed_tags if tag in generated_text]
            if not tags:
                tags = ["untagged"]
            print(f"Generated tags: {tags}")
            return tags
        except Exception as e:
            if "429" in str(e):
                print(f"Rate limit hit, retrying in {2**i} seconds...")
                time.sleep(2**i)
            else:
                print(f"Could not generate tags for review: {e}")
                return ["untagged"]
    print("Failed to generate tags after multiple retries.")
    return ["untagged"]

def get_reviews_for_app(app):
    """
    Get low-rated reviews for a given app using the app-store-scraper Node.js script.
    """
    print("Getting reviews for {}...".format(app['name']))
    reviews = []
    try:
        result = subprocess.run(["node", "scraper/get_reviews.js", str(app['id'])], capture_output=True, text=True, check=True)
        scraped_reviews = json.loads(result.stdout)
        print(f"Found {len(scraped_reviews)} reviews for {app['name']}")
        for r in scraped_reviews:
            if r['score'] <= 2:
                review = {
                    "app_name": app["name"],
                    "rating": r['score'],
                    "review": r['text'],
                    "date": r['date'].split(' ')[0]
                }
                review["tags"] = generate_tags_for_review(review)
                reviews.append(review)
                time.sleep(30) # Add a delay to avoid hitting the rate limit
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print("Could not get reviews for {}: {}".format(app['name'], e))
    return reviews

def main():
    apps = get_top_paid_apps()
    
    try:
        with open("data/tagged_reviews.json", "r") as f:
            all_reviews = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_reviews = []

    try:
        with open("data/processed_apps.json", "r") as f:
            processed_apps = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        processed_apps = {}

    unprocessed_apps = [app for app in apps if str(app['id']) not in processed_apps]

    apps_to_process = []
    if unprocessed_apps:
        apps_to_process = unprocessed_apps
    else:
        # If all apps have been processed, find the one with the oldest timestamp
        sorted_processed_apps = sorted(processed_apps.items(), key=lambda item: item[1])
        if sorted_processed_apps:
            oldest_app_id, _ = sorted_processed_apps[0]
            apps_to_process = [app for app in apps if str(app['id']) == oldest_app_id]

    # Limit the number of apps to process in a single run
    app_quota = 10
    apps_to_process = apps_to_process[:app_quota]

    for app in apps_to_process:
        reviews = get_reviews_for_app(app)
        all_reviews.extend(reviews)
        
        processed_apps[str(app['id'])] = datetime.now().isoformat()

        print(f"Writing {len(all_reviews)} reviews to data/tagged_reviews.json")
        with open("data/tagged_reviews.json", "w") as f:
            json.dump(all_reviews, f, indent=4)
        
        with open("data/processed_apps.json", "w") as f:
            json.dump(processed_apps, f, indent=4)

        print(f"Processed {app['name']} and updated checkpoint.")

    print("Finished processing apps.")

if __name__ == "__main__":
    main()