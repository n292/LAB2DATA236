# M1 Package: FastAPI + React + Real Kafka Producer

This package includes the M1 Profile Service in FastAPI, the React frontend, photo upload, and real Kafka publishing for:
- `member.created`
- `member.updated`

## What Kafka now does

When you create a member, the backend publishes a JSON event to the `member.created` Kafka topic.

When you update a member, the backend publishes a JSON event to the `member.updated` Kafka topic.

Each message follows the shared event envelope:
- `event_type`
- `trace_id`
- `timestamp`
- `actor_id`
- `entity`
- `payload`
- `idempotency_key`

## Backend setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with your MySQL password and Kafka settings.

## MySQL setup

Run `schema.sql` in MySQL Workbench.

## Kafka setup options

### Option 1: You already have Kafka running

Keep this in `.env`:

```env
KAFKA_ENABLED=true
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_MEMBER_CREATED_TOPIC=member.created
KAFKA_MEMBER_UPDATED_TOPIC=member.updated
```

### Option 2: You want the app to run without Kafka for now

Set this in `.env`:

```env
KAFKA_ENABLED=false
```

That disables publishing but keeps the backend working.


### Option 3: Start Kafka with Docker Compose

If you have Docker Desktop, from the `backend` folder run:

```bash
docker compose -f docker-compose.kafka.yml up -d
```

That starts a local Kafka broker on `localhost:9092`.

## Run the backend

```bash
python run.py
```

Backend URLs:
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Uploaded photos: `http://localhost:8000/uploads/<filename>`

The health response now also shows whether Kafka is enabled and which topics are configured.

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:
- `http://localhost:5173`

## How photo upload works

1. On Create Profile or Edit Profile, choose an image file.
2. React sends the file to `POST /api/members/upload-photo`.
3. FastAPI saves the file locally in `backend/app/uploads`.
4. FastAPI returns a `profile_photo_url`.
5. That URL is saved with the member profile in MySQL.

## Supported image types

- `.jpg`
- `.jpeg`
- `.png`
- `.gif`
- `.webp`

## Max file size

Default is 5 MB. Change it in `backend/.env` with `MAX_FILE_SIZE_MB`.

## Verify Kafka is working

After the backend starts, create or update a member.

If Kafka is running and reachable, the backend logs will show successful publish messages.

You can also inspect the topic with a Kafka consumer from your local Kafka setup.
