import argparse
from pymongo import MongoClient
import pandas as pd

def get_mongodb_data(host, port, username, password, db_name, collection_name):
    """Connect to MongoDB and retrieve data from specified collection."""
    connection_string = f"mongodb://{username}:{password}@{host}:{port}/"
    client = MongoClient(connection_string)
    db = client[db_name]
    collection = db[collection_name]
    
    documents = list(collection.find({}))
    print(f"Loaded {len(documents)} documents from collection")
    return documents

def save_to_csv(documents, output_path):
    """Convert documents to DataFrame and save to CSV."""
    df = pd.DataFrame(documents)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"DataFrame shape: {df.shape}")
    print(f"Data saved to: {output_path}")
    return df

def main():
    parser = argparse.ArgumentParser(description='Export MongoDB data to CSV')
    parser.add_argument('--host', default='localhost', help='MongoDB host')
    parser.add_argument('--port', default='27017', help='MongoDB port')
    parser.add_argument('--username', default='root', help='MongoDB username')
    parser.add_argument('--password', default='example', help='MongoDB password')
    parser.add_argument('--db', default='reviews_db', help='Database name')
    parser.add_argument('--collection', default='vectorized_reviews', help='Collection name')
    parser.add_argument('--output', default='spark/data/vectorized_reviews.csv', 
                       help='Output CSV file path')

    args = parser.parse_args()

    # Get data from MongoDB
    documents = get_mongodb_data(
        args.host, 
        args.port,
        args.username,
        args.password,
        args.db,
        args.collection
    )

    # Save to CSV
    df = save_to_csv(documents, args.output)
    return df

if __name__ == "__main__":
    main()
