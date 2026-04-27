#!/usr/bin/env python3
"""
Seeds 500 test users into the running MongoDB container for JMeter performance testing.
Run from the LAB2DATA236-main directory:
  python3 mongo_seed_users.py
"""
import subprocess, json, sys, pathlib

MONGO_CONTAINER = "lab2-mongodb-1"
DB_NAME = "yelp_mongo_db"
TEST_PASSWORD = "TestPass123!"
NUM_USERS = 500

# --- Step 1: generate bcrypt hash inside the API container ---
print("Generating bcrypt hash inside API container...")
result = subprocess.run(
    ["docker", "exec", "lab2-api-1", "python3", "-c",
     f"import bcrypt; h=bcrypt.hashpw(b'{TEST_PASSWORD}',bcrypt.gensalt(12)).decode(); print(h)"],
    capture_output=True, text=True, check=True
)
hashed_pw = result.stdout.strip()
print(f"Hash: {hashed_pw[:30]}...")

# --- Step 2: Delete existing test users ---
print("Cleaning up old test users...")
subprocess.run(
    ["docker", "exec", MONGO_CONTAINER, "mongosh", DB_NAME, "--quiet", "--eval",
     "db.users.deleteMany({email: /.*@test\.com/})"],
    check=True
)

# --- Step 3: build docs for users ---
docs = []
csv_rows = []

CITIES = ["San Francisco","New York","Los Angeles","Chicago","Austin"]
STATES  = ["CA","NY","CA","IL","TX"]
GENDERS = ["Male","Female","Other"]

# Start IDs from 1000 to avoid conflict
start_id = 1000

for i in range(1, NUM_USERS + 1):
    email = f"user{i}@test.com"
    csv_rows.append(f"{email},{TEST_PASSWORD}")
    docs.append({
        "_id": start_id,
        "name": f"Perf User {i}",
        "email": email,
        "password_hash": hashed_pw,
        "phone": f"555-{i:04d}",
        "city": CITIES[i % 5],
        "country": "United States",
        "state": STATES[i % 5],
        "languages": "English",
        "gender": GENDERS[i % 3],
        "about_me": f"JMeter perf test user #{i}",
        "role": "user",
        "profile_picture": None,
        "reviews": [],
        "favorites": [],
        "created_at": "ISODATE_PLACEHOLDER",
        "updated_at": "ISODATE_PLACEHOLDER",
        "profile": {}
    })
    start_id += 1

print(f"Inserting {len(docs)} users...")

# --- Step 4: write JS in batches ---
BATCH = 50
inserted = 0
for batch_start in range(0, len(docs), BATCH):
    batch = docs[batch_start:batch_start + BATCH]
    # Convert placeholders to actual ISODate constructor calls in JS
    js_batch = json.dumps(batch).replace('"ISODATE_PLACEHOLDER"', 'new Date()')
    js = f"db.users.insertMany({js_batch});"
    
    proc = subprocess.run(
        ["docker", "exec", "-i", MONGO_CONTAINER,
         "mongosh", DB_NAME, "--quiet"],
        input=js,
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        print(f"ERROR on batch {batch_start}: {proc.stderr[:300]}")
        sys.exit(1)
    inserted += len(batch)
    print(f"  Inserted {inserted}/{len(docs)}...", end="\r")

print(f"\n✓ Inserted {len(docs)} new users")

# --- Step 5: write users.csv ---
csv_path = pathlib.Path(__file__).parent / "lab2" / "users.csv"
csv_path.parent.mkdir(parents=True, exist_ok=True)
with open(csv_path, "w") as f:
    f.write("email,password\n")
    for row in csv_rows:
        f.write(row + "\n")
print(f"✓ users.csv written → {csv_path}  ({len(csv_rows)} rows)")
print("\n✓ Done! Test review submission again.")
