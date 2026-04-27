#!/usr/bin/env python3
"""
Seed database with sample restaurant and user data for testing.
Adds 500 test users + 50 restaurants so JMeter can run at
100/200/300/400/500 concurrent users without hitting the
one-review-per-user-per-restaurant constraint.
Also writes lab2/users.csv for JMeter CSV Data Set Config.
"""

import sys
from pathlib import Path

# Add the app directory to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Restaurant, User
from app.utils.security import hash_password

# Database URL - using absolute path for consistency
db_path = Path(__file__).parent / "yelp_dev.db"
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# ── constants ────────────────────────────────────────────────────────────────
TEST_PASSWORD = "TestPass123!"
NUM_USERS = 500
NUM_RESTAURANTS = 50

CITIES  = ["San Francisco", "New York", "Los Angeles", "Chicago", "Austin"]
STATES  = ["CA",            "NY",       "CA",          "IL",      "TX"]
GENDERS = ["Male", "Female", "Other"]

CUISINE_NAMES = [
    ("Italian",  ["Trattoria Roma",    "Pasta Palace",    "Bella Napoli",     "La Cucina",        "Ristorante Marco"]),
    ("Chinese",  ["Dragon Palace",     "Golden Phoenix",  "Jade Garden",      "Lucky Star",       "Dim Sum House"]),
    ("Japanese", ["Tokyo Ramen House", "Sakura Sushi",    "Kyoto Kitchen",    "Osaka Grill",      "Noodle Ninja"]),
    ("Mexican",  ["El Mariachi",       "Casa Fiesta",     "Taco Loco",        "La Hacienda",      "Salsa Verde"]),
    ("Indian",   ["Spice Route",       "Taj Mahal",       "Curry House",      "Bombay Bites",     "Delhi Darbar"]),
    ("French",   ["Le Petit Cafe",     "Bistro Paris",    "Cafe Lumiere",     "Maison Blanche",   "Boulangerie du Coin"]),
    ("American", ["Burger Paradise",   "The Smokehouse",  "Classic Diner",    "All-Day Grill",    "The Steakhouse"]),
    ("Thai",     ["Thai Orchid",       "Bangkok Street",  "Lotus Garden",     "Pad Thai Place",   "Chilli Basil"]),
    ("Greek",    ["Athens Taverna",    "Mykonos Grill",   "Zorba's Kitchen",  "Olive and Feta",   "Parthenon Cafe"]),
    ("Spanish",  ["La Bodega",         "Barcelona Tapas", "El Toro",          "Iberian Kitchen",  "Paella House"]),
]

RESTAURANT_CITIES = [
    "New York", "Brooklyn", "Queens", "Manhattan", "Midtown",
    "Downtown", "East Side", "West Side", "Arts District", "Uptown",
]
TIERS   = ["$", "$$", "$$$"]
RATINGS = [4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 5.0]
COMMENTS = [
    "Great place! Highly recommend.",
    "Amazing food and great service.",
    "Really enjoyed the atmosphere here.",
    "Will definitely come back again!",
    "One of the best restaurants I have visited.",
]
# ─────────────────────────────────────────────────────────────────────────────


def seed_data():
    """Add 500 users and 50 restaurants; generate users.csv for JMeter."""
    db = SessionLocal()

    try:
        # ── guard: skip if already seeded ───────────────────────────────────
        user_count = db.query(User).count()
        restaurant_count = db.query(Restaurant).count()

        if user_count >= NUM_USERS and restaurant_count >= NUM_RESTAURANTS:
            print(f"✓ Already have {user_count} users and {restaurant_count} restaurants. Skipping.")
            return

        # ── users ────────────────────────────────────────────────────────────
        existing_emails = {row[0] for row in db.query(User.email).all()}
        hashed_pw = hash_password(TEST_PASSWORD)

        # Named accounts kept for manual testing / backward compat
        named = [
            ("Test User",        "test@example.com",     "Password123!",  "555-0000", "San Francisco", "CA", "Other",  "user"),
            ("testuser",         "testuser@example.com", TEST_PASSWORD,   "555-0001", "San Francisco", "CA", "Other",  "user"),
            ("Restaurant Owner", "owner@example.com",    "OwnerPass123!", "555-0002", "New York",      "NY", "Male",   "owner"),
            ("Admin User",       "admin@example.com",    "AdminPass123!", "555-0003", "Los Angeles",   "CA", "Female", "user"),
        ]
        added_users = 0
        for name, email, pw, phone, city, state, gender, role in named:
            if email not in existing_emails:
                db.add(User(
                    name=name, email=email,
                    password_hash=hash_password(pw),
                    phone=phone, city=city, country="United States",
                    state=state, languages="English", gender=gender,
                    about_me="Sample account", role=role,
                ))
                existing_emails.add(email)
                added_users += 1

        # Bulk performance-test users
        for i in range(1, NUM_USERS + 1):
            email = f"user{i}@test.com"
            if email not in existing_emails:
                idx = (i - 1) % len(CITIES)
                db.add(User(
                    name=f"Perf User {i}",
                    email=email,
                    password_hash=hashed_pw,
                    phone=f"555-{i:04d}",
                    city=CITIES[idx],
                    country="United States",
                    state=STATES[idx],
                    languages="English",
                    gender=GENDERS[i % len(GENDERS)],
                    about_me=f"JMeter test account #{i}",
                    role="user",
                ))
                existing_emails.add(email)
                added_users += 1

        db.commit()
        total_users = db.query(User).count()
        print(f"✓ Added {added_users} new users  (DB total: {total_users})")

        # ── write users.csv for JMeter ───────────────────────────────────────
        csv_path = Path(__file__).parent.parent / "lab2" / "users.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w") as f:
            f.write("email,password\n")
            for i in range(1, NUM_USERS + 1):
                f.write(f"user{i}@test.com,{TEST_PASSWORD}\n")
        print(f"✓ JMeter CSV written → {csv_path}")

        # ── restaurants ──────────────────────────────────────────────────────
        existing_names = {row[0] for row in db.query(Restaurant.name).all()}
        added_restaurants = 0
        seq = 1
        for cuisine, names in CUISINE_NAMES:
            for rname in names:
                if rname not in existing_names:
                    city = RESTAURANT_CITIES[(seq - 1) % len(RESTAURANT_CITIES)]
                    db.add(Restaurant(
                        name=rname,
                        cuisine_type=cuisine,
                        address=f"{seq * 10} Sample St",
                        city=city,
                        phone=f"(555) {seq:03d}-{(seq * 7) % 9999:04d}",
                        pricing_tier=TIERS[seq % len(TIERS)],
                        average_rating=RATINGS[seq % len(RATINGS)],
                        review_count=0,
                    ))
                    existing_names.add(rname)
                    added_restaurants += 1
                seq += 1

        db.commit()
        total_restaurants = db.query(Restaurant).count()
        print(f"✓ Added {added_restaurants} new restaurants  (DB total: {total_restaurants})")

    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding database...\n")
    seed_data()
    print("\n✓ Complete!")
