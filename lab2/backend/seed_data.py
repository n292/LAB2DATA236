#!/usr/bin/env python3
"""
Seed database with sample restaurant and user data for testing
This script adds sample restaurants and users to make the app functional during development
"""

import sys
from pathlib import Path

# Add the app directory to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Restaurant, User, UserPreference
from app.utils.security import hash_password

# Database URL - using absolute path for consistency
db_path = Path(__file__).parent / "yelp_dev.db"
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def seed_data():
    """Add sample restaurants and users to database"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_restaurants = db.query(Restaurant).first()
        existing_users = db.query(User).first()
        
        if existing_restaurants and existing_users:
            print("✓ Database already contains data. Skipping seed.")
            return
        
        # Sample users for testing
        users = [
            User(
                name="Test User",
                email="testuser@example.com",
                password_hash=hash_password("TestPass123!"),
                phone="555-0001",
                city="San Francisco",
                country="United States",
                state="CA",
                languages="English",
                gender="Other",
                about_me="A regular food enthusiast",
                role="user"
            ),
            User(
                name="Restaurant Owner",
                email="owner@example.com",
                password_hash=hash_password("OwnerPass123!"),
                phone="555-0002",
                city="New York",
                country="United States",
                state="NY",
                languages="English",
                gender="Male",
                about_me="Professional restaurant owner",
                role="owner"
            ),
            User(
                name="Admin User",
                email="admin@example.com",
                password_hash=hash_password("AdminPass123!"),
                phone="555-0003",
                city="Los Angeles",
                country="United States",
                state="CA",
                languages="English",
                gender="Female",
                about_me="System administrator",
                role="user"
            )
        ]
        
        # Add users to database
        for user in users:
            db.add(user)
        
        db.commit()
        print(f"✓ Successfully added {len(users)} sample users!")
        
        # Print user summary
        for u in users:
            print(f"  • {u.name} ({u.email}) - Role: {u.role}")
        
        # Sample restaurants
        restaurants = [
            Restaurant(
                name="The Italian Kitchen",
                cuisine_type="Italian",
                address="123 Main St",
                city="New York",
                phone="(555) 123-4567",
                pricing_tier="$$",
                average_rating=4.5,
                review_count=0
            ),
            Restaurant(
                name="Dragon Palace",
                cuisine_type="Chinese",
                address="456 Oak Ave",
                city="New York",
                phone="(555) 234-5678",
                pricing_tier="$$",
                average_rating=4.2,
                review_count=0
            ),
            Restaurant(
                name="Tokyo Ramen House",
                cuisine_type="Japanese",
                address="789 Pine Rd",
                city="Brooklyn",
                phone="(555) 345-6789",
                pricing_tier="$$",
                average_rating=4.7,
                review_count=0
            ),
            Restaurant(
                name="El Mariachi",
                cuisine_type="Mexican",
                address="321 Elm St",
                city="Queens",
                phone="(555) 456-7890",
                pricing_tier="$",
                average_rating=4.3,
                review_count=0
            ),
            Restaurant(
                name="Spice Route",
                cuisine_type="Indian",
                address="654 Maple Blvd",
                city="Manhattan",
                phone="(555) 567-8901",
                pricing_tier="$$",
                average_rating=4.6,
                review_count=0
            ),
            Restaurant(
                name="Le Petit Café",
                cuisine_type="French",
                address="987 Cedar Ln",
                city="Downtown",
                phone="(555) 678-9012",
                pricing_tier="$$$",
                average_rating=4.8,
                review_count=0
            ),
            Restaurant(
                name="Burger Paradise",
                cuisine_type="American",
                address="147 Birch Way",
                city="Midtown",
                phone="(555) 789-0123",
                pricing_tier="$",
                average_rating=4.1,
                review_count=0
            ),
            Restaurant(
                name="Thai Orchid",
                cuisine_type="Thai",
                address="258 Spruce Dr",
                city="East Side",
                phone="(555) 890-1234",
                pricing_tier="$$",
                average_rating=4.4,
                review_count=0
            ),
            Restaurant(
                name="Athens Taverna",
                cuisine_type="Greek",
                address="369 Poplar Ct",
                city="West Side",
                phone="(555) 901-2345",
                pricing_tier="$$",
                average_rating=4.5,
                review_count=0
            ),
            Restaurant(
                name="La Bodega Española",
                cuisine_type="Spanish",
                address="741 Walnut St",
                city="Arts District",
                phone="(555) 012-3456",
                pricing_tier="$$",
                average_rating=4.3,
                review_count=0
            )
        ]
        
        # Add restaurants to database
        for restaurant in restaurants:
            db.add(restaurant)
        
        db.commit()
        print(f"✓ Successfully added {len(restaurants)} sample restaurants!")
        
        # Print restaurant summary
        for r in restaurants:
            print(f"  • {r.name} ({r.cuisine_type}) - {r.city}")
            
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Seeding database with sample data...\n")
    seed_data()
    print("\n✓ Complete!")
