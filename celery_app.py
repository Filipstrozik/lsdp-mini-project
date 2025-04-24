from celery import Celery

# Initialize the Celery app
app = Celery("scraper")

# Load configuration from a module
app.config_from_object("config.celery_config")

# Auto-discover tasks in all registered app modules
app.autodiscover_tasks(["scraper"])

if __name__ == "__main__":
    app.start()
    
