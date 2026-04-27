import os
import sys
from datetime import datetime, timezone
import random

try:
    from app.mongodb import mongo_db
except ImportError:
    from mongodb import mongo_db

def seed_100_restaurants():
    cuisines = ["Italian", "Mexican", "Chinese", "Indian", "Japanese", "American", "French", "Thai", "Greek", "Spanish"]
    cities = ["San Jose", "San Francisco", "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego"]
    amenities = ["Outdoor Seating", "Wifi", "Parking", "Delivery", "Takeout", "Reservations", "Alcohol"]
    pricing = ["$", "$$", "$$$", "$$$$"]

    restaurants = []
    
    # Start with ID 2 since 1 was seeded already
    last_rest = mongo_db.restaurants.find_one({}, sort=[("_id", -1)])
    start_id = (last_rest["_id"] + 1) if last_rest else 1

    for i in range(100):
        name = f"Restaurant {i + start_id}"
        cuisine = random.choice(cuisines)
        city = random.choice(cities)
        
        restaurants.append({
            "_id": i + start_id,
            "mysql_id": i + start_id,
            "name": f"{cuisine} Delight {i + start_id}",
            "cuisine_type": cuisine,
            "description": f"A wonderful {cuisine} restaurant in {city}.",
            "location": {
                "address": f"{random.randint(100, 999)} Main St",
                "city": city,
                "zip_code": f"{random.randint(90000, 99999)}"
            },
            "contact": {
                "phone": f"555-{random.randint(1000, 9999)}",
                "email": f"info@rest{i + start_id}.com"
            },
            "hours_of_operation": '{"mon": "9am-10pm", "tue": "9am-10pm", "wed": "9am-10pm", "thu": "9am-10pm", "fri": "9am-11pm", "sat": "10am-11pm", "sun": "10am-9pm"}',
            "amenities": random.sample(amenities, k=random.randint(1, 4)),
            "pricing_tier": random.choice(pricing),
            "average_rating": round(random.uniform(3.0, 5.0), 1),
            "review_count": random.randint(0, 100),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

    if restaurants:
        mongo_db.restaurants.insert_many(restaurants)
    
    print(f"Successfully seeded {len(restaurants)} restaurants into MongoDB!")

if __name__ == "__main__":
    seed_100_restaurants()
