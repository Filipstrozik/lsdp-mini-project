import shutil
from pyspark.sql import SparkSession, DataFrame
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml import Pipeline
from pyspark.ml.tuning import ParamGridBuilder, TrainValidationSplit
from pyspark.sql.functions import col, udf
from pyspark.ml.linalg import Vectors, VectorUDT
import os
from pathlib import Path

def create_spark_session():
    spark_master_url = os.getenv("SPARK_MASTER_URL", "spark://localhost:7077")
    return (
        SparkSession.builder.appName("ReviewClassification")
        .config("spark.master", spark_master_url)
        .config("spark.broadcast.compress", "true")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.kryoserializer.buffer.max", "512m")
        .config("spark.driver.maxResultSize", "2g")
        .getOrCreate()
    )

def load_data_from_csv(spark, file_path):
    return spark.read.option("multiline", "true").option("escape", "\"").csv(
        file_path, header=True, inferSchema=True, sep=","
    )

def prepare_features(df: DataFrame) -> DataFrame:
    # Convert string of space-separated numbers to vector
    def string_to_vector(vec_str):
        try:
            # Split string by whitespace and convert to float array
            vec_list = [float(x) for x in vec_str.split()]
            return Vectors.dense(vec_list)
        except:
            return None
    
    string_to_vector_udf = udf(string_to_vector, VectorUDT())
    
    return df.select(
        string_to_vector_udf(col("vectors")).alias("vectors"),
        col("rating").cast("string")
    ).repartition(4)

def split_data(df, train_ratio=0.9):
    train_data, test_data = df.randomSplit([train_ratio, 1 - train_ratio], seed=42)
    return train_data, test_data

def create_pipeline():
    string_indexer = StringIndexer(inputCol="rating", outputCol="label")
    assembler = VectorAssembler(inputCols=["vectors"], outputCol="features")

    rf = RandomForestClassifier(
        featuresCol="features",
        labelCol="label",
        numTrees=10,
        maxDepth=5,
        seed=42,
        cacheNodeIds=False,
        maxBins=32
    )

    return Pipeline(stages=[string_indexer, assembler, rf])

def train_model(pipeline, train_data):
    paramGrid = (
        ParamGridBuilder()
        .addGrid(pipeline.getStages()[-1].numTrees, [10, 20])
        .addGrid(pipeline.getStages()[-1].maxDepth, [5, 10])
        .build()
    )

    evaluator = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="accuracy"
    )

    tvs = TrainValidationSplit(
        estimator=pipeline,
        estimatorParamMaps=paramGrid,
        evaluator=evaluator,
        trainRatio=0.8,
        parallelism=2,
    )

    model = tvs.fit(train_data)
    return model

def evaluate_model(model, test_data):
    predictions = model.bestModel.transform(test_data)
    evaluator = MulticlassClassificationEvaluator(labelCol="label")

    accuracy = evaluator.evaluate(predictions, {evaluator.metricName: "accuracy"})
    f1 = evaluator.evaluate(predictions, {evaluator.metricName: "f1"})
    precision = evaluator.evaluate(
        predictions, {evaluator.metricName: "weightedPrecision"}
    )
    recall = evaluator.evaluate(predictions, {evaluator.metricName: "weightedRecall"})

    print(f"Accuracy: {accuracy}")
    print(f"F1 Score: {f1}")
    print(f"Precision: {precision}")
    print(f"Recall: {recall}")

    # Print classification mapping
    label_mapping = model.bestModel.stages[0].labels
    print("\nRating to Label Mapping:")
    for idx, rating in enumerate(label_mapping):
        print(f"Rating {rating} -> Label {idx}")

    # # Print feature importances
    # rf_model = model.bestModel.stages[-1]
    # feature_importances = rf_model.featureImportances
    # print("\nFeature Importances:")
    # print(feature_importances)

    return predictions

def main():

    spark = create_spark_session()
    # print current working directory
    # Load data from CSV
    df = load_data_from_csv(spark, "/opt/bitnami/spark/data/vectorized_reviews.csv")

    # Prepare features
    prepared_df = prepare_features(df)

    # Split data
    train_data, test_data = split_data(prepared_df, train_ratio=0.9)
    print('Training Data Count:', train_data.count())
    print('Test Data Count:', test_data.count())

    # Create and train model
    pipeline = create_pipeline()
    model = train_model(pipeline, train_data)

    # Evaluate model
    predictions = evaluate_model(model, test_data)

    # Save the model
    spark_path = "/opt/bitnami/spark/data/review_classification_model"
    model.bestModel.write().overwrite().save(spark_path)

    # Move the model to the desired location
    desired_path = "/app/models/review_classification_model"
    os.makedirs(os.path.dirname(desired_path), exist_ok=True)
    shutil.move(
        spark_path,
        desired_path
    )
    # Print the model path
    print(f"Model saved to {desired_path}")

    spark.stop()

if __name__ == "__main__":
    main()
