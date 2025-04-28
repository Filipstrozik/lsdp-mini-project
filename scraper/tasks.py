# scraper/tasks.py
from datetime import datetime
import logging
from celery import Celery, shared_task, chain
from scrapy.crawler import CrawlerProcess
from scraper.polwro_scraper import PolwroSpider
import os
from langdetect import detect
import time
from scraper.metrics import LANGUAGE_COUNTER, LANGUAGE_DETECTION_TIME
from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModel
import torch

# Load HerBERT model and tokenizer globally to avoid reloading for every task
tokenizer = AutoTokenizer.from_pretrained("allegro/herbert-base-cased")
model = AutoModel.from_pretrained("allegro/herbert-base-cased")

logger = logging.getLogger(__name__)


@shared_task()
def run_polwro_scraper(full_scan=True):
    """
    Task to run the PolWro scraper
    Args:
        full_scan (bool): If True, performs a complete scan of all forums
    """
    try:
        settings = {
            "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "LOG_LEVEL": "WARNING",  # Set to WARNING to reduce log verbosity
            "DOWNLOAD_DELAY": 2 if full_scan else 1,  # Be more conservative during full scan
        }

        process = CrawlerProcess(settings)

        # Load credentials from environment variables
        login = os.getenv('POLWRO_USERNAME')
        password = os.getenv('POLWRO_PASSWORD')

        if not login or not password:
            raise ValueError("Missing POLWRO_USERNAME or POLWRO_PASSWORD environment variables")

        process.crawl(PolwroSpider, 
                     login=login, 
                     password=password, 
                     full_scan=full_scan)
        process.start()

        logger.info(f"Completed {'full' if full_scan else 'incremental'} scan of PolWro")
        return "Scraping completed successfully"

    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        # Retry the task with exponential backoff
        run_polwro_scraper.retry(exc=e, countdown=2 ** run_polwro_scraper.request.retries * 60)


@shared_task(name="detect_language")
def detect_language(post_data):
    """
    Detect language of the review text and add it to post data
    """
    start_time = time.time()
    try:
        language = detect(post_data["review"])
        post_data["language"] = language

        # Record language detection metrics
        LANGUAGE_COUNTER.labels(language=language).inc()

        # If the language is Polish, chain to text vectorization
        if language == 'pl':
            chain(text_vectorizer.s(post_data))()

    except Exception as e:
        post_data["language"] = "unknown"
        LANGUAGE_COUNTER.labels(language="unknown").inc()
        logger.error(f"Language detection error: {str(e)}")
    finally:
        # Record detection time
        detection_time = time.time() - start_time
        LANGUAGE_DETECTION_TIME.observe(detection_time)

    return post_data


@shared_task(name="text_vectorizer")
def text_vectorizer(post_data):
    """
    Process Polish reviews for text vectorization using HerBERT and save to MongoDB.
    """
    try:
        # Tokenize the review text
        tokens = tokenizer(
            post_data["review"],
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        )

        # Generate vector embeddings using HerBERT
        with torch.no_grad():
            outputs = model(**tokens)
            # Use the [CLS] token representation as the vector
            post_data["vectors"] = outputs.last_hidden_state[:, 0, :].squeeze().tolist()

        # Chain to save the vectorized data to MongoDB
        chain(save_to_mongo.s(post_data))()
    except Exception as e:
        logger.error(f"Text vectorization error: {str(e)}")
        return None


@shared_task(name="save_to_mongo")
def save_to_mongo(vectorized_data):
    """
    Save vectorized data to MongoDB collection and update last opinion date
    """
    try:
        client = MongoClient("mongodb://root:example@mongodb:27017/")
        db = client["reviews_db"]
        collection = db["vectorized_reviews"]
        metadata_collection = db["scraping_metadata"]
        
        if vectorized_data and '_id' not in vectorized_data:
            # Ensure date is datetime object
            if isinstance(vectorized_data.get('date'), str):
                try:
                    if ',' in vectorized_data['date']:
                        vectorized_data['date'] = datetime.strptime(vectorized_data['date'], '%Y-%m-%d, %H:%M')
                    else:
                        vectorized_data['date'] = datetime.strptime(vectorized_data['date'], '%Y-%m-%d')
                except ValueError as e:
                    logger.error(f"Date parsing error: {e}")
                    return None
            
            # Save the review
            result = collection.insert_one(vectorized_data)
            
            # Update last opinion date if present in the data
            if 'date' in vectorized_data:
                metadata_collection.update_one(
                    {"_id": "last_opinion_date"},
                    {"$max": {"date": vectorized_data["date"]}},
                    upsert=True
                )
                logger.info(f"Updated last opinion date to: {vectorized_data['date']}")
            
            return str(result.inserted_id)
        else:
            logger.warning("No data to save or document already exists")
            return None
            
    except Exception as e:
        logger.error(f"MongoDB save error: {str(e)}")
        return None
