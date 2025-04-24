# prometheus_exporter.py
import os
from prometheus_client import CollectorRegistry, multiprocess, generate_latest
import time
import logging
from scraper.metrics import * 
from prometheus_client import make_wsgi_app
from wsgiref.simple_server import make_server

logger = logging.getLogger(__name__)


def start_metrics_server(port=8000):
    """
    Start the Prometheus metrics HTTP server
    """

    # Always create a registry
    registry = CollectorRegistry()
    
    # If multiprocess collection is enabled, add it to the registry

    tmp_dir = os.getenv('PROMETHEUS_MULTIPROC_DIR')
    if tmp_dir:
        logger.info(f"Using multiprocess mode with directory: {tmp_dir}")
        multiprocess.MultiProcessCollector(registry)

    try:
        app = make_wsgi_app(registry=registry)
        httpd = make_server("", port, app)
        logger.info(f"Prometheus metrics server started on port {port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start metrics server: {str(e)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_metrics_server(port=8000)

    # Keep the script running
    while True:
        time.sleep(1)
