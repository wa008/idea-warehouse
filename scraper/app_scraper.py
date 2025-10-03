import json
import time
from datetime import datetime
import subprocess
import os
from dotenv import load_dotenv
import logging
import argparse
from model import Model, get_model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

def get_top_paid_apps(num=200):
    """
    Get the top paid apps from the App Store.
    """
    logging.info("Getting top paid apps from the App Store...")
    try:
        result = subprocess.run(["node", "scraper/get_top_paid_apps.js", str(num)], capture_output=True, text=True, check=True)
        apps = json.loads(result.stdout)
        logging.info(f"Found {len(apps)} top paid apps.")
        return apps
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error(f"Could not get top paid apps: {e}")
        return []

def get_reviews_for_app(app, model, remaining_quota):
    """
    Get low-rated reviews for a given app.
    """
    logging.info(f"Getting reviews for {app['title']}...")
    reviews = []
    processing_review_amount = 0 
    try:
        result = subprocess.run(["node", "scraper/get_reviews.js", str(app['id'])], capture_output=True, text=True, check=True)
        scraped_reviews = json.loads(result.stdout)
        logging.info(f"Found {len(scraped_reviews)} reviews for {app['title']}")
        for r in scraped_reviews:
            if r['score'] <= 2:
                processing_review_amount += 1
                logging.info(f"Processing review: {processing_review_amount} / {remaining_quota} for curect app {app['title']}")
                if processing_review_amount > remaining_quota:
                    logging.info(f"Review quota for current app of {remaining_quota} reached. Stopping.")
                    break
                analysis = model.get_review_analysis(r['text'])
                review = {
                    "app_name": app["title"],
                    "rating": r['score'],
                    "review": r['text'],
                    "date": datetime.fromisoformat(r.get('updated')).strftime('%Y-%m-%d') if r.get('updated') else 'N/A',
                    "value": analysis.get('value', 0),
                    "potential_idea": analysis.get('potential_idea', ''),
                    "tags": model.get_tags_for_review(r['text'])
                }
                reviews.append(review)
                time.sleep(1)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error(f"Could not get reviews for {app['title']}: {e}")
    return reviews

class AppScraper:
    def __init__(self, gemini_api_key, openrouter_api_key):
        self.llm_model = get_model(gemini_api_key, openrouter_api_key)
        self.apps_data = []
        self.processed_apps = {}
        self.load_data()

    def load_data(self):
        try:
            with open("data/apps_data.json", "r") as f:
                self.apps_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.apps_data = []

        try:
            with open("data/processed_apps.json", "r") as f:
                self.processed_apps = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.processed_apps = {}

    def save_data(self):
        with open("data/apps_data.json", "w") as f:
            json.dump(self.apps_data, f, indent=4)
        with open("data/processed_apps.json", "w") as f:
            json.dump(self.processed_apps, f, indent=4)

    def run(self, num_apps=200, max_reviews=30, from_scratch=False):
        logging.info("Starting scraper...")
        logging.info(f"max_reviews: {max_reviews}")
        if from_scratch:
            self.apps_data = []
            self.processed_apps = {}

        apps = get_top_paid_apps(num=num_apps)
        
        unprocessed_apps = [app for app in apps if str(app['id']) not in self.processed_apps]
        apps_to_process = unprocessed_apps if unprocessed_apps else sorted(apps, key=lambda app: self.processed_apps.get(str(app['id']), '1970-01-01T00:00:00.000000'))

        total_reviews_processed = 0

        for app in apps_to_process:
            logging.info(f"Totally processing reviews {total_reviews_processed} / {max_reviews}")
            if total_reviews_processed >= max_reviews:
                logging.info(f"Review quota of {max_reviews} reached. Stopping.")
                break

            remaining_quota = max_reviews - total_reviews_processed
            logging.info(f"Processing app: {app['title']}")
            reviews = get_reviews_for_app(app, self.llm_model, remaining_quota)
            
            if not reviews:
                self.processed_apps[str(app['id'])] = datetime.now().isoformat()
                continue

            if len(reviews) > remaining_quota:
                reviews = reviews[:remaining_quota]

            total_reviews_processed += len(reviews)

            description = app.get('summary', '')
            if len(description.split()) > 15:
                description = ' '.join(description.split()[:15]) + '...'

            app_data = {
                "id": app['id'],
                "name": app['title'],
                "url": app.get('url'),
                "description": description,
                "reviews": reviews
            }

            self.apps_data = [a for a in self.apps_data if a['id'] != app['id']]
            self.apps_data.append(app_data)
            
            self.processed_apps[str(app['id'])] = datetime.now().isoformat()
            self.save_data()

            logging.info(f"Processed {app['title']} and updated checkpoint.")

            if total_reviews_processed >= max_reviews:
                logging.info(f"Review quota of {max_reviews} reached. Stopping.")
                break

        logging.info(f"Finished processing apps. Processed {total_reviews_processed} reviews.")

def main():
    parser = argparse.ArgumentParser(description='Scrape app reviews.')
    parser.add_argument('--num_apps', type=int, default=200, help='Number of apps to fetch from the top list.')
    parser.add_argument('--max_reviews', type=int, default=30, help='Maximum number of reviews to process in a single run.')
    parser.add_argument('--from_scratch', action='store_true', help='Start scraping from scratch.')
    parser.add_argument("--GEMINIAPIKEY", help="Gemini API key")
    parser.add_argument("--OPENROUTERAPIKEY", help="OpenRouter API key")
    args = parser.parse_args()

    scraper = AppScraper(gemini_api_key=args.GEMINIAPIKEY, openrouter_api_key=args.OPENROUTERAPIKEY)
    scraper.run(num_apps=args.num_apps, max_reviews=args.max_reviews, from_scratch=args.from_scratch)

if __name__ == "__main__":
    main()
