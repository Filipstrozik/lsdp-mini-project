from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml import Pipeline
from pyspark.ml.tuning import ParamGridBuilder, TrainValidationSplit
from pyspark.sql.functions import col
import torch

def create_spark_session():
    return (
        SparkSession.builder.appName("ReviewClassification")
        .config(
            "spark.mongodb.read.connection.uri",
            "mongodb://root:example@mongodb:27017/reviews_db?authSource=admin"
        )
        .config("spark.mongodb.read.database", "reviews_db")
        .config("spark.mongodb.read.collection", "vectorized_reviews")
        .config(
            "spark.jars.packages",
            "org.mongodb.spark:mongo-spark-connector_2.12:10.2.1"
        )
        .getOrCreate()
    )


def load_data_from_mongo(spark):
    df = (
        spark.read.format("mongodb")
        .option("uri", "mongodb://root:example@mongodb:27017")
        .option("database", "reviews_db")
        .option("collection", "vectorized_reviews")
        .load()
    )
    return df

def save_data_to_csv(df, path):
    df.write.csv(path, header=True, mode="overwrite")


def prepare_features(df):
    # Convert rating strings to numeric labels
    string_indexer = StringIndexer(inputCol="rating", outputCol="label")

    # Convert vectors array to feature column
    assembler = VectorAssembler(inputCols=["vectors"], outputCol="features")

    return df.select("vectors", "rating").withColumn(
        "rating",
        col("rating").cast("string"),  # Ensure rating is string type for StringIndexer
    )


def split_data(df):
    train_data, temp_data = df.randomSplit([0.7, 0.3], seed=42)
    val_data, test_data = temp_data.randomSplit([0.5, 0.5], seed=42)
    return train_data, val_data, test_data


def create_pipeline():
    string_indexer = StringIndexer(inputCol="rating", outputCol="label")
    assembler = VectorAssembler(inputCols=["vectors"], outputCol="features")

    lr = LogisticRegression(
        featuresCol="features",
        labelCol="label",
        maxIter=10,
        regParam=0.3,
        elasticNetParam=0.8,
        family="multinomial",  # For multiclass classification
    )

    return Pipeline(stages=[string_indexer, assembler, lr])


def train_model(pipeline, train_data, val_data):
    paramGrid = (
        ParamGridBuilder()
        .addGrid(pipeline.getStages()[-1].regParam, [0.1, 0.3, 0.5])
        .addGrid(pipeline.getStages()[-1].elasticNetParam, [0.0, 0.5, 1.0])
        .addGrid(pipeline.getStages()[-1].maxIter, [10, 20, 30])
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
    )

    model = tvs.fit(train_data)
    return model


def evaluate_model(model, test_data):
    predictions = model.transform(test_data)
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
    label_mapping = model.stages[0].labels
    print("\nRating to Label Mapping:")
    for idx, rating in enumerate(label_mapping):
        print(f"Rating {rating} -> Label {idx}")

    return predictions


def predict_custom_text(spark, model, text, tokenizer, bert_model):
    # Vectorize input text (similar to before)
    tokens = tokenizer(
        text, return_tensors="pt", truncation=True, padding=True, max_length=512
    )

    with torch.no_grad():
        outputs = bert_model(**tokens)
        vectors = outputs.last_hidden_state[:, 0, :].squeeze().tolist()

    # Create DataFrame with vector and dummy rating (will be transformed by pipeline)
    test_df = spark.createDataFrame([(vectors, "5,0")], ["vectors", "rating"])

    # Make prediction
    prediction = model.transform(test_df)
    pred_label = prediction.select("prediction").collect()[0][0]

    # Convert numeric prediction back to rating using label mapping
    original_rating = model.stages[0].labels[int(pred_label)]
    return original_rating


def main():
    spark = create_spark_session()

    df = load_data_from_mongo(spark)
    # Save data to CSV for debugging
    save_data_to_csv(df, "results/reviews.csv")

    # prepared_df = prepare_features(df)

    # train_data, val_data, test_data = split_data(prepared_df)

    # pipeline = create_pipeline()
    # model = train_model(pipeline, train_data, val_data)

    # predictions = evaluate_model(model, test_data)

    # # Example prediction
    # custom_text = "Świetny wykładowca, bardzo dobrze tłumaczy materiał"
    # predicted_rating = predict_custom_text(spark, model, custom_text)
    # print(f"Predicted rating for custom text: {predicted_rating}")

    # # Save predictions
    # predictions.toPandas().to_csv("predictions.csv", index=False)

    spark.stop()


if __name__ == "__main__":
    main()
