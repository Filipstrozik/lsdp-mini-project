from prometheus_client import Summary, Counter, Histogram

# Scraping time metrics
FORUM_SCRAPE_TIME = Summary(
    'polwro_forum_scrape_seconds',
    'Time spent scraping a forum page'
)

TOPIC_SCRAPE_TIME = Summary(
    'polwro_topic_scrape_seconds',
    'Time spent scraping a topic page'
)

# Success/Error counters
SCRAPE_SUCCESS_COUNTER = Counter(
    'polwro_scrape_success_total',
    'Total number of successful scraping operations'
)

SCRAPE_ERROR_COUNTER = Counter(
    'polwro_scrape_error_total',
    'Total number of failed scraping operations'
)

# Opinion metrics
OPINIONS_SCRAPED = Counter(
    'polwro_opinions_total',
    'Total number of opinions scraped'
)

OPINIONS_ERROR = Counter(
    'polwro_opinions_errors_total',
    'Total number of errors during opinion scraping'
)

# Rating metrics
RATING_HISTOGRAM = Histogram(
    'polwro_opinion_rating',
    'Distribution of professor ratings',
    buckets=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
)

VOTE_RATE_HISTOGRAM = Histogram(
    'polwro_opinion_vote_rate',
    'Distribution of opinion vote rates',
    buckets=[0, 1, 2, 3, 4, 5, 10, 20, 50, 100]
)

# Course metrics
COURSES_SCRAPED = Counter(
    'polwro_courses_total',
    'Total number of unique courses scraped'
)

# Professor metrics
PROFESSORS_SCRAPED = Counter(
    'polwro_professors_total',
    'Total number of unique professors scraped'
)

# Language detection metrics
LANGUAGE_COUNTER = Counter(
    'detected_language_total',
    'Number of reviews by detected language',
    ['language']
)

LANGUAGE_DETECTION_TIME = Histogram(
    'language_detection_seconds',
    'Time spent on language detection',
    buckets=[.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0]
)
