import os


class ModelConfig:
    def __init__(self):
        # Model paths
        self.BERT_MODEL_PATH = os.environ.get(
            "BERT_MODEL_PATH", "allegro/herbert-base-cased"
        )
        self.SPARK_MODEL_PATH = os.environ.get(
            "SPARK_MODEL_PATH",
            "spark/models/review_classification_model/review_classification_model",
        )

        # Server settings
        self.SERVER_PORT = int(os.environ.get("SERVER_PORT", 50051))
        self.MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 10))

        # Logging settings
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
