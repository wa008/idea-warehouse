import json
import time
from datetime import datetime
import subprocess
import os
from dotenv import load_dotenv
import logging
import argparse
from model import Model

# Configure logging
# logging.basicConfig(filename='scraper.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

def get_top_paid_apps():
    """
    Get the top paid apps from the App Store.
    """
    logging.info("Getting top paid apps from the App Store...")
    try:
        result = subprocess.run(["node", "scraper/get_top_paid_apps.js"], capture_output=True, text=True, check=True)
        apps = json.loads(result.stdout)
        logging.info(f"Found {len(apps)} top paid apps.")
        return apps
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error(f"Could not get top paid apps: {e}")
        return []

def generate_tags_for_review(review, model):
    """
    Generate tags for a given review using the Model class.
    """
    logging.info(f"Generating tags for review: {review['review']}")

    prompt = f"""Analyze the following app review and assign one or more of the following tags:

*   **no update:** The app hasn't been updated in a long time, and the review mentions issues that could be fixed with an update.
*   **niche demand:** The review requests a feature that is likely not in high demand from the general user base.
*   **valuable opinion:** The review provides constructive feedback or a new idea that could improve the app.

Review: {review['review']}

Tags:"""

    generated_text = model.generate_content(prompt)

    if generated_text:
        allowed_tags = ["no update", "niche demand", "valuable opinion"]
        tags = [tag for tag in allowed_tags if tag in generated_text]
        if not tags:
            tags = ["untagged"]
        logging.info(f"Generated tags: {tags}")
        return tags
    else:
        logging.error("Failed to generate tags.")
        return ["untagged"]

def get_reviews_for_app(app, model):
    """
    Get low-rated reviews for a given app using the app-store-scraper Node.js script.
    """
    logging.info("Getting reviews for {}...".format(app['title']))
    reviews = []
    try:
        result = subprocess.run(["node", "scraper/get_reviews.js", str(app['id'])], capture_output=True, text=True, check=True)
        scraped_reviews = json.loads(result.stdout)
        logging.info(f"Found {len(scraped_reviews)} reviews for {app['title']}")
        for i, r in enumerate(scraped_reviews):
            logging.info(f"Processing review {i+1}/{len(scraped_reviews)} for {app['title']}")
            if r['score'] <= 2:
                review = {
                    "app_name": app["title"],
                    "rating": r['score'],
                    "review": r['text'],
                    "date": datetime.fromisoformat(r.get('updated')).strftime('%Y-%m-%d') if r.get('updated') else 'N/A'
                }
                review["tags"] = generate_tags_for_review(review, model)
                reviews.append(review)
                time.sleep(20) # Add a delay to avoid hitting the rate limit
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error("Could not get reviews for {}: {}".format(app['title'], e))
    return reviews

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--GEMINIAPIKEY", help="Gemini API key")
    parser.add_argument("--OPENROUTERAPIKEY", help="OpenRouter API key")
    args = parser.parse_args()

    logging.info("Starting scraper...")
    model = Model(gemini_api_key=args.GEMINIAPIKEY, openrouter_api_key=args.OPENROUTERAPIKEY)
    apps = get_top_paid_apps()
    
    try:
        with open("data/apps_data.json", "r") as f:
            apps_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        apps_data = []

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

    for i, app in enumerate(apps_to_process):
        logging.info(f"Processing app {i+1}/{len(apps_to_process)}: {app['title']}")
        reviews = get_reviews_for_app(app, model)

        app_data = {
            "id": app['id'],
            "name": app['title'],
            "reviews": reviews
        }

        apps_data.append(app_data)
        
        processed_apps[str(app['id'])] = datetime.now().isoformat()

        logging.info(f"Writing {len(apps_data)} apps to data/apps_data.json")
        with open("data/apps_data.json", "w") as f:
            json.dump(apps_data, f, indent=4)
        
        with open("data/processed_apps.json", "w") as f:
            json.dump(processed_apps, f, indent=4)

        logging.info(f"Processed {app['title']} and updated checkpoint.")

    logging.info("Finished processing apps.")

if __name__ == "__main__":
    main()
