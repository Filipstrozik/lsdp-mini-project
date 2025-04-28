from prometheus_client import Summary, Counter, Histogram

FORUM_SCRAPE_TIME = Summary(
    'polwro_forum_scrape_seconds',
    'Time spent scraping a forum page'
)

TOPIC_SCRAPE_TIME = Summary(
    'polwro_topic_scrape_seconds',
    'Time spent scraping a topic page'
)

SCRAPE_SUCCESS_COUNTER = Counter(
    'polwro_scrape_success_total',
    'Total number of successful scraping operations'
)

SCRAPE_ERROR_COUNTER = Counter(
    'polwro_scrape_error_total',
    'Total number of failed scraping operations'
)

OPINIONS_SCRAPED = Counter(
    'polwro_opinions_total',
    'Total number of opinions scraped'
)

OPINIONS_ERROR = Counter(
    'polwro_opinions_errors_total',
    'Total number of errors during opinion scraping'
)

RATING_COUNTER = Counter(
    'polwro_opinion_rating_total',
    'Count of professor ratings by rating value',
    ['rating']  # Label for different rating values
)


VOTE_RATE_HISTOGRAM = Histogram(
    "polwro_opinion_vote_rate",
    "Distribution of opinion vote rates",
    buckets=[-100, -50, -20, -10, -5, -1, 0, 1, 5, 10, 20, 50, 100],
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
