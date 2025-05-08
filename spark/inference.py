from pyspark.ml import PipelineModel
from pyspark.sql import SparkSession
import torch
from transformers import AutoTokenizer, AutoModel
import logging
from pyspark.ml.linalg import Vectors
from pyspark.sql.types import StructType, StructField, ArrayType, FloatType

# Start Spark session
spark = SparkSession.builder.appName("ModelInference").getOrCreate()

tokenizer = AutoTokenizer.from_pretrained("allegro/herbert-base-cased")
bert_model = AutoModel.from_pretrained("allegro/herbert-base-cased")

logger = logging.getLogger(__name__)

loaded_model = PipelineModel.load(
    "spark/models/review_classification_model/review_classification_model"
)
print("Model loaded successfully.")

# Example review text
data_text = "Beznadzieja, Odradzam. Zajęcia nudne. Nie warto. Omijać szerokim łukiem. Nie polecam. Kolokwium trudne."
# data_text = "Bardzo dobry prowadzący, bardzo polecam. Potrafi wytłumaczyć wszystko w prosty sposób. Zajęcia są ciekawe i nie ma mowy o nudzie. Bardzo polecam! :)"

tokens = tokenizer(
    data_text,
    return_tensors="pt",
    truncation=True,
    padding=True,
    max_length=512,
)

# Generate vector embeddings using HerBERT
with torch.no_grad():
    outputs = bert_model(**tokens)
    # Use the [CLS] token representation as the vector
    data_vector = outputs.last_hidden_state[:, 0, :].squeeze().tolist()

# Create a DataFrame with the vector
data_list = [(Vectors.dense(data_vector),)]
schema = StructType([StructField("vectors", ArrayType(FloatType()), True)])
df = spark.createDataFrame(data_list, ["vectors"])

# Get predictions
predictions = loaded_model.transform(df)

# Show results
print("\nPrediction Results:")
predictions.select("prediction").show()

# Get label mapping
label_mapping = loaded_model.stages[0].labels
print("\nRating to Label Mapping:")
for idx, rating in enumerate(label_mapping):
    print(f"Rating {rating} -> Label {idx}")

# Get the predicted label and corresponding rating
predicted_label = predictions.select("prediction").collect()[0][0]
predicted_rating = label_mapping[int(predicted_label)]
print(f"\nPredicted Rating: {predicted_rating}")

spark.stop()
