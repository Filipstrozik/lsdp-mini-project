# polwro_scraper.py
import os
from xml.etree.ElementInclude import include
import scrapy
from scrapy import signals
from scrapy.crawler import CrawlerProcess
import logging
from urllib.parse import urlparse, parse_qs, urljoin
from prometheus_client import Histogram, Counter
from celery import Celery


app = Celery('scraper')
app.config_from_object("config.celery_config")

# Auto-discover tasks in all registered app modules
app.autodiscover_tasks(["scraper"])

# Import histograms and counters
from scraper.metrics import (
    FORUM_SCRAPE_TIME, TOPIC_SCRAPE_TIME,
    RATING_HISTOGRAM, VOTE_RATE_HISTOGRAM,
    OPINIONS_SCRAPED, OPINIONS_ERROR, 
    COURSES_SCRAPED, PROFESSORS_SCRAPED
)


class PolwroSpider(scrapy.Spider):
    name = "polwro"
    start_urls = ["https://polwro.com/login.php"] 

    # Add excluded keywords set
    excluded_keywords = {
        'wnioski', 
        'lista-rezerwowa', 
        'wazne-jak',
        'zapisz-sie',
        'regulamin',
        'ogloszenia'
        'inni',
        'humanisci',
        'matematycy',
        'fizycy',
        'chemicy',
        'elektronicy',
        'jezykowcy'
    }

    included_keywords = {
        'sportowcy'
    }

    custom_settings = {
        "LOG_LEVEL": "WARNING",
        # Add a delay to be respectful to the server
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "FEED_EXPORT_ENCODING": "utf-8",
        "FEED_EXPORT_INDENT": 2,
        "FEED_EXPORT_ENSURE_ASCII": False,
    }

    def __init__(self, login=None, password=None, *args, **kwargs):
        super(PolwroSpider, self).__init__(*args, **kwargs)
        self.login = login
        self.password = password
        # Configure spider-specific logging
        self.logger.setLevel(logging.WARNING)
        

    def parse(self, response):
        """
        Direct login through login.php page
        """
        self.logger.info("Attempting login through login.php")

        # Find the login form - it's the one that posts to 'login.php'
        login_form = response.xpath('//form[@action="login.php"]')

        if not login_form:
            self.logger.error("Could not find login form!")
            return

        return scrapy.FormRequest.from_response(
            response,
            formxpath='//form[@action="login.php"]',  # Explicitly specify which form to use
            formdata={
                "username": self.login,
                "password": self.password,
                "login": "Zaloguj",
                "redirect": "",
                "autologin": "on"
            },
            dont_click=True,  # Don't try to click any submit buttons
            callback=self.after_login
        )

    def after_login(self, response):
        # Check if we were redirected to index.php
        self.logger.info(f"Response URL after login: {response.url}")

        if "index.php" in response.url:
            self.logger.info("Login successful - redirected to index.php")
            # Continue with scraping
            yield scrapy.Request(
                "https://polwro.com/opinie-o-prowadzacych", 
                callback=self.parse_forums
            )
        else:
            self.logger.error("Login failed - not redirected to index.php")
            return

    def parse_forums(self, response):
        # Extract forum links (ones that contain '/f,')
        for link in response.css('a[href*="/f,"]::attr(href)').getall():
            try:
                # Skip URLs containing excluded keywords
                if any(keyword in link.lower() for keyword in self.excluded_keywords):
                    self.logger.info(f"Skipping excluded forum: {link}")
                    continue

                # Skip URLs not containing included keywords
                if not any(keyword in link.lower() for keyword in self.included_keywords):
                    self.logger.info(f"Skipping forum not containing included keywords: {link}")
                    continue
                    
                # Extract forum ID (the integer after the last comma)
                forum_id = link.split(",")[-1]
                if forum_id.isdigit():
                    forum_id = int(forum_id)
                    # Construct the initial forum URL
                    forum_url = f"https://polwro.com/viewforum.php?f={forum_id}"
                    self.logger.info(f"Found forum link: {link} -> Requesting {forum_url}")
                    yield scrapy.Request(forum_url, callback=self.parse_forum)
                else:
                    self.logger.warning(f"Could not extract forum ID from link: {link}")
            except Exception as e:
                self.logger.error(f"Error processing forum link {link}: {e}")

    @FORUM_SCRAPE_TIME.time()
    def parse_forum(self, response):
        self.logger.info(f"Parsing forum page: {response.url}")

        # Extract topic links with format "t,name,id"
        topic_links_found = False
        # Use a set to store unique topic URLs
        topic_links = set()

        # Updated selector to match the specific link format
        for topic_link in response.css('a[href^="t,"]::attr(href)').getall():
            try:
                # Skip URLs containing excluded keywords
                if any(keyword in topic_link.lower() for keyword in self.excluded_keywords):
                    self.logger.info(f"Skipping excluded topic: {topic_link}")
                    continue

                # Remove 'start' parameter if present
                topic_link = topic_link.split('&start=')[0]
                topic_full_url = f"https://polwro.com/{topic_link}"
                # Only process if we haven't seen this URL before
                if topic_full_url not in topic_links:
                    topic_links.add(topic_full_url)
                    self.logger.info(f"Found new topic link: {topic_full_url}")
                    topic_links_found = True
                    yield scrapy.Request(topic_full_url, callback=self.parse_topic)
            except Exception as e:
                self.logger.error(f"Error processing topic link {topic_link}: {e}")

        # --- Pagination Logic ---
        next_page = None

        # Look for pagination div
        if response.css('div.pagination'):
            # Find "next page" link with title "Dalej"
            next_page = response.css('a.postmenu[title="Dalej"]::attr(href)').get()

        if next_page:
            # Convert relative URL to absolute if needed
            next_page_url = urljoin(response.url, next_page)
            self.logger.info(f"Found next page link: {next_page_url}")
            yield scrapy.Request(next_page_url, callback=self.parse_forum)
        else:
            self.logger.info(f"No more pages found for forum: {response.url}")

    @TOPIC_SCRAPE_TIME.time()
    def parse_topic(self, response):
        """Parse individual topic page and extract post data with metrics"""
        for post in response.css('ul.gradient_post'):
            try:
                # User info
                user_data = {
                    'username': post.css('span[itemprop="author"]::text').get('').strip(),
                    'faculty': post.css('div.ll::text').re_first(r'Wydział:\s*(.*?)(?:\s{2,}|\n|$)'),
                    'year': post.css('div.ll::text').re_first(r'Rok studiów:\s*(\d+)'),
                    'opinion_weight': post.css('span.important_inline::text').re_first(r'Waga opinii: x([\d.]+)'),
                }

                # Post metadata
                post_date = post.css('div.post_date::text').re_first(r'(\d{4}-\d{2}-\d{2})')
                professor_name = ' '.join([
                    post.css('span[itemprop="givenName"]::text').get(''),
                    post.css('span[itemprop="familyName"]::text').get('')
                ]).strip()

                # Get vote rate
                vote_rate = post.css('span.vote_rate::text').get('')

                # Rating and content
                rating = post.css('span[itemprop="ratingValue"]::text').get('')
                content = post.css('span[itemprop="reviewBody"]')
                course_name = content.css('span[style="font-weight: bold"]::text').re_first(r'Kurs: (.*?)(?:\s{2,}|\n|$)')
                review_text = content.css('::text').getall()  # Get all text content

                # Construct the post data
                post_data = {
                    **user_data,
                    'date': post_date,
                    'professor': professor_name,
                    'rating': rating,
                    'vote_rate': vote_rate,
                    'course': course_name,
                    'review': ' '.join(review_text).strip(),
                    'post_url': response.url
                }   

                app.send_task('detect_language', args=[post_data])
                # Increment counters and record metrics
                OPINIONS_SCRAPED.inc()

                if rating:
                    try:
                        RATING_HISTOGRAM.observe(float(rating))
                    except ValueError:
                        self.logger.warning(f"Invalid rating value: {rating}")

                if vote_rate:
                    try:
                        VOTE_RATE_HISTOGRAM.observe(float(vote_rate.strip()))
                    except ValueError:
                        self.logger.warning(f"Invalid vote rate value: {vote_rate}")

                if course_name:
                    COURSES_SCRAPED.inc()

                if professor_name:
                    PROFESSORS_SCRAPED.inc()

                yield post_data

            except Exception as e:
                OPINIONS_ERROR.inc()
                self.logger.error(f"Error processing post in {response.url}: {e}")

        # Handle pagination for topic pages
        next_page = None

        # Look for pagination div
        if response.css('div.pagination'):
            # Find "next page" link with title "Dalej"
            next_page = response.css('a.postmenu[title="Dalej"]::attr(href)').get()

        if next_page:
            # Convert relative URL to absolute if needed
            next_page_url = urljoin(response.url, next_page)
            self.logger.info(f"Found next page link: {next_page_url}")
            yield scrapy.Request(next_page_url, callback=self.parse_topic)
        else:
            self.logger.info(f"No more pages found for topic: {response.url}")

