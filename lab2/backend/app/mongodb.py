import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "yelp_mongo_db")

client = MongoClient(MONGO_URI)
mongo_db = client[MONGO_DB_NAME]


def create_mongo_indexes():
    mongo_db.users.create_index([("email", ASCENDING)], unique=True)
    mongo_db.sessions.create_index([("token", ASCENDING)], unique=True)
    mongo_db.sessions.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

    mongo_db.restaurants.create_index([("name", ASCENDING)])
    mongo_db.restaurants.create_index([("city", ASCENDING)])
    mongo_db.restaurants.create_index([("owner_id", ASCENDING)])

    mongo_db.reviews.create_index([("restaurant_id", ASCENDING)])
    mongo_db.reviews.create_index([("user_id", ASCENDING)])

    mongo_db.favourites.create_index(
        [("user_id", ASCENDING), ("restaurant_id", ASCENDING)],
        unique=True
    )

    mongo_db.activity_logs.create_index([("event_type", ASCENDING)])
    mongo_db.activity_logs.create_index([("created_at", ASCENDING)])