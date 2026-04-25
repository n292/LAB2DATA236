import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from passlib.context import CryptContext
from pymongo import MongoClient, ASCENDING
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_mysql_engine():
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "yelp_db")

    url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(url)


def get_mongo_db():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name = os.getenv("MONGO_DB_NAME", "yelp_mongo_db")
    client = MongoClient(mongo_uri)
    return client[mongo_db_name]


def fetch_all(engine, query):
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return [dict(row._mapping) for row in result]


def safe_datetime(value):
    if value is None:
        return datetime.now(timezone.utc)
    return value


def migrate_users(engine, mongo_db):
    rows = fetch_all(engine, "SELECT * FROM users")
    docs = []

    for row in rows:
        password_hash = row.get("password_hash")
        if not password_hash or not str(password_hash).startswith("$2"):
            password_hash = pwd_context.hash("Password123!")

        docs.append({
            "_id": row["id"],
            "mysql_id": row["id"],
            "name": row.get("name"),
            "email": row.get("email"),
            "password_hash": password_hash,
            "phone": row.get("phone"),
            "profile": {
                "about_me": row.get("about_me"),
                "city": row.get("city"),
                "state": row.get("state"),
                "country": row.get("country"),
                "languages": row.get("languages"),
                "gender": row.get("gender"),
                "profile_picture_exists": row.get("profile_picture") is not None,
            },
            "role": row.get("role") or "USER",
            "created_at": safe_datetime(row.get("created_at")),
            "updated_at": safe_datetime(row.get("updated_at")),
        })

    mongo_db.users.delete_many({})
    if docs:
        mongo_db.users.insert_many(docs)

    print(f"Migrated users: {len(docs)}")


def migrate_user_preferences(engine, mongo_db):
   
    try:
        rows = fetch_all(engine, "SELECT * FROM user_preferences")
    except Exception as exc:
        print(f"Skipped user_preferences: {exc}")
        return

    docs = []
    for row in rows:
        docs.append({
            "mysql_id": row.get("id"),
            "user_id": row.get("user_id"),
            "preferences": row,
            "created_at": datetime.now(timezone.utc),
        })

    mongo_db.user_preferences.delete_many({})
    if docs:
        mongo_db.user_preferences.insert_many(docs)

    print(f"Migrated user_preferences: {len(docs)}")


def migrate_restaurants(engine, mongo_db):
    rows = fetch_all(engine, "SELECT * FROM restaurants")
    docs = []

    for row in rows:
        docs.append({
            "_id": row["id"],
            "mysql_id": row["id"],
            "name": row.get("name"),
            "cuisine_type": row.get("cuisine_type"),
            "description": row.get("description"),
            "location": {
                "address": row.get("address"),
                "city": row.get("city"),
                "zip_code": row.get("zip_code"),
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
            },
            "contact": {
                "phone": row.get("phone"),
                "email": row.get("email"),
            },
            "hours_of_operation": row.get("hours_of_operation"),
            "amenities": row.get("amenities"),
            "pricing_tier": row.get("pricing_tier"),
            "owner_id": row.get("owner_id"),
            "average_rating": row.get("average_rating") or 0,
            "review_count": row.get("review_count") or 0,
            "photos": {
                "stored_in_mysql_blob": row.get("photos") is not None,
                "photo_refs": [],
            },
            "created_at": safe_datetime(row.get("created_at")),
            "updated_at": safe_datetime(row.get("updated_at")),
        })

    mongo_db.restaurants.delete_many({})
    if docs:
        mongo_db.restaurants.insert_many(docs)

    print(f"Migrated restaurants: {len(docs)}")


def migrate_reviews(engine, mongo_db):
    rows = fetch_all(engine, "SELECT * FROM reviews")
    docs = []

    for row in rows:
        docs.append({
            "_id": row["id"],
            "mysql_id": row["id"],
            "user_id": row.get("user_id"),
            "restaurant_id": row.get("restaurant_id"),
            "rating": row.get("rating"),
            "comment": row.get("comment"),
            "photos": {
                "stored_in_mysql_blob": row.get("photos") is not None,
                "photo_refs": [],
            },
            "created_at": safe_datetime(row.get("created_at")),
            "updated_at": safe_datetime(row.get("updated_at")),
        })

    mongo_db.reviews.delete_many({})
    if docs:
        mongo_db.reviews.insert_many(docs)

    print(f"Migrated reviews: {len(docs)}")


def migrate_favourites(engine, mongo_db):
    rows = fetch_all(engine, "SELECT * FROM favorites")
    docs = []

    for row in rows:
        docs.append({
            "_id": row["id"],
            "mysql_id": row["id"],
            "user_id": row.get("user_id"),
            "restaurant_id": row.get("restaurant_id"),
            "created_at": safe_datetime(row.get("created_at")),
        })

    mongo_db.favourites.delete_many({})
    if docs:
        mongo_db.favourites.insert_many(docs)

    print(f"Migrated favourites: {len(docs)}")


def create_sessions(mongo_db):
    mongo_db.sessions.delete_many({})

    session_doc = {
        "user_id": 1,
        "token": "sample-secure-session-token-for-demo",
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=2),
        "ip_address": "127.0.0.1",
        "user_agent": "Lab2 MongoDB demo",
        "is_active": True,
    }

    mongo_db.sessions.insert_one(session_doc)

    print("Created demo MongoDB session with expiry")


def create_activity_logs(mongo_db):
    mongo_db.activity_logs.delete_many({})

    logs = [
        {
            "event_type": "migration.completed",
            "actor_id": "system",
            "payload": {
                "source": "mysql",
                "target": "mongodb",
                "description": "Migrated Lab 1 Yelp data into MongoDB",
            },
            "created_at": datetime.now(timezone.utc),
        },
        {
            "event_type": "restaurant.created",
            "actor_id": "system",
            "payload": {
                "description": "Restaurant event migrated/recorded for activity log demo",
            },
            "created_at": datetime.now(timezone.utc),
        },
        {
            "event_type": "review.processed",
            "actor_id": "system",
            "payload": {
                "description": "Review activity log demo",
            },
            "created_at": datetime.now(timezone.utc),
        },
    ]

    mongo_db.activity_logs.insert_many(logs)

    print(f"Created activity logs: {len(logs)}")


def create_indexes(mongo_db):
    mongo_db.users.create_index([("email", ASCENDING)], unique=True)
    mongo_db.sessions.create_index([("token", ASCENDING)], unique=True)
    mongo_db.sessions.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
    mongo_db.restaurants.create_index([("name", ASCENDING)])
    mongo_db.restaurants.create_index([("location.city", ASCENDING)])
    mongo_db.reviews.create_index([("restaurant_id", ASCENDING)])
    mongo_db.reviews.create_index([("user_id", ASCENDING)])
    mongo_db.favourites.create_index([("user_id", ASCENDING), ("restaurant_id", ASCENDING)], unique=True)
    mongo_db.activity_logs.create_index([("event_type", ASCENDING)])
    mongo_db.activity_logs.create_index([("created_at", ASCENDING)])

    print("Created MongoDB indexes")


def main():
    engine = get_mysql_engine()
    mongo_db = get_mongo_db()

    print("Starting MySQL to MongoDB migration...")

    migrate_users(engine, mongo_db)
    migrate_user_preferences(engine, mongo_db)
    migrate_restaurants(engine, mongo_db)
    migrate_reviews(engine, mongo_db)
    migrate_favourites(engine, mongo_db)
    create_sessions(mongo_db)
    create_activity_logs(mongo_db)
    create_indexes(mongo_db)

    print("Migration complete.")

    print("\nMongoDB collection counts:")
    for collection_name in mongo_db.list_collection_names():
        print(f"{collection_name}: {mongo_db[collection_name].count_documents({})}")


if __name__ == "__main__":
    main()