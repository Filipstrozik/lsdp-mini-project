# MLOps pipeline for Polwro forum

## Overview
This project implements a complete MLOps pipeline for scraping, processing, and analyzing reviews from the Polwro forum. The system includes web scraping, data processing, monitoring, and visualization components.

## Architecture
The system consists of several interconnected services:

### Core Services
- **Web Scraper**: A Scrapy-based spider that crawls the Polwro forum for reviews
- **Celery Workers**: Distributed task processing for scraping and text analysis
- **MongoDB**: Primary database for storing scraped reviews
- **Redis**: Message broker and result backend for Celery
- **RabbitMQ**: Message queue for task distribution

### Processing Pipeline
1. **Data Collection**
   - Automated forum scraping with authentication
   - Incremental and full scan modes
   - Language detection for reviews
   - Text vectorization using HerBERT model

2. **Data Processing**
   - Apache Spark for large-scale data processing
   - CSV export capabilities
   - Text vectorization and analysis

### Monitoring Stack
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and monitoring dashboards
- **Custom Metrics**: 
  - Opinion counts
  - Processing times
  - Language statistics
  - Rating distributions

### Visualization
- **Redash**: Data visualization and SQL querying interface
- **Spark History Server**: Spark job monitoring and history

## Setup and Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.x
- Environment variables for Polwro credentials

### Getting Started
1. Clone the repository
2. Create a `.env` file with required credentials:
   ```
   POLWRO_USERNAME=your_username
   POLWRO_PASSWORD=your_password
   ```
3. Start the core services:
   ```bash
   docker-compose up -d
   ```
4. Start Spark cluster (optional):
   ```bash
   docker-compose -f docker-compose-spark.yml up -d
   ```
5. Start Redash (optional):
   ```bash
   docker-compose -f docker-compose-redash.yml up -d
   ```

### Accessing Services
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- RabbitMQ Management: http://localhost:15672
- Spark Master UI: http://localhost:8080
- Spark History Server: http://localhost:18080
- Redash: http://localhost:5001

## Project Structure
```
├── scraper/              # Web scraping components
├── spark/               # Spark processing scripts
├── monitoring/          # Monitoring configuration
├── config/             # Service configurations
└── docker-compose files # Infrastructure definitions
```

## Tech Stack

### Core Technologies
- **Python 3.x**: Primary programming language
- **Docker & Docker Compose**: Containerization and orchestration
- **MongoDB**: Primary database for storing reviews
- **Redis**: Message broker and caching
- **RabbitMQ**: Message queue system

### Data Processing & ML
- **Apache Spark**: Distributed data processing
  - PySpark SQL
  - PySpark ML (RandomForest, Pipeline, VectorAssembler)
  - Spark History Server
- **HerBERT**: Polish language model for text vectorization
- **NumPy & Pandas**: Data manipulation and analysis

### Web Scraping & Task Processing
- **Scrapy**: Web crawling framework
- **Celery**: Distributed task queue
  - Task scheduling and monitoring
  - Asynchronous processing

### Monitoring & Visualization
- **Prometheus**: Metrics collection and storage
  - Custom metrics exporters
  - Alert management
- **Grafana**: Data visualization and dashboards
- **Redash**: SQL querying and visualization

### DevOps & Infrastructure
- **Docker Compose**: Multi-container deployment
  - Spark cluster management
  - Service orchestration
- **Prometheus Alertmanager**: Alert routing and notification
- **Environment-based configuration**: .env files for credentials

## Features
- Automated review collection from Polwro
- Natural language processing pipeline
- Real-time metrics and monitoring
- Scalable data processing with Spark
- Containerized deployment
- Comprehensive monitoring and alerting
