import torch
import logging
import numpy as np
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.ml.linalg import Vectors
from transformers import AutoTokenizer, AutoModel
from inference_service.config.config import ModelConfig


class ModelHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = ModelConfig()

        # Initialize Spark
        self.spark = SparkSession.builder.appName("ModelInference").getOrCreate()

        # Load tokenizer and BERT model
        self.logger.info("Loading tokenizer and BERT model...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.BERT_MODEL_PATH)
        self.bert_model = AutoModel.from_pretrained(self.config.BERT_MODEL_PATH)

        # Load Spark pipeline model
        self.logger.info("Loading Spark pipeline model...")
        self.model = PipelineModel.load(self.config.SPARK_MODEL_PATH)

        self.logger.info("Model handler initialized successfully")

    def predict(self, text):
        """Perform prediction on input text"""
        self.logger.info("Generating embeddings...")

        # Tokenize input
        tokens = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        )

        # Generate vector embeddings
        with torch.no_grad():
            outputs = self.bert_model(**tokens)
            # Use the [CLS] token representation as the vector
            vector = outputs.last_hidden_state[:, 0, :].squeeze().tolist()

        # Create DataFrame with vector
        data_list = [(Vectors.dense(vector),)]
        df = self.spark.createDataFrame(data_list, ["vectors"])

        # Get predictions
        self.logger.info("Running prediction...")
        predictions = self.model.transform(df)

        # Extract prediction
        prediction = predictions.select("prediction").collect()[0][0]

        # Get confidence (probabilities)
        if "probability" in predictions.columns:
            probability = predictions.select("probability").collect()[0][0]
            confidence = float(max(probability.toArray()))
        else:
            confidence = 1.0  # Default if no probability column

        # Get the predicted label
        label_mapping = self.model.stages[0].labels
        rating = label_mapping[int(prediction)]

        return prediction, confidence, rating

    def check_health(self):
        """Check if the model is healthy"""
        try:
            # Simple health check - try to predict a sample text
            self.predict("Sample text for health check")
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
