# Yelp Prototype - Backend (FastAPI)

A FastAPI-based backend for a Yelp-like restaurant discovery platform with AI-powered recommendations.

## Features

- User authentication (JWT-based)
- Restaurant CRUD operations
- Review management system
- User preferences and favorites
- AI assistant for personalized restaurant recommendations
- RESTful APIs with Swagger documentation

## Stack

- **Framework**: FastAPI
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT
- **Password Hashing**: bcrypt
- **AI**: Langchain +Local LLM(OLLAMA)
- **API Documentation**: Swagger/OpenAPI

## Prerequisites

- Python 3.8+
- MySQL 5.7+
- pip or conda

## Installation

1. **Clone and Navigate**:
   ```bash
   cd yelp_backend
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Database**:
   ```bash
   # Create MySQL database
   mysql -u root -p
   CREATE DATABASE yelp_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   EXIT;
   ```

5. **Configure Environment**:
   - Copy `.env.example` to `.env`
   - Update database credentials and API keys:
     ```
     DB_HOST=localhost
     DB_USER=root
     DB_PASSWORD=your_password
     DB_NAME=yelp_db
     SECRET_KEY=your-secret-key
     TAVILY_API_KEY=your-tavily-key
     ```

## Running the Backend

```bash
cd app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/redoc`
- Test using postman 

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User signup
- `POST /api/auth/login` - User login

### Users
- `GET /api/users/{user_id}` - Get user profile
- `PUT /api/users/{user_id}` - Update user profile
- `GET /api/users/{user_id}/preferences` - Get user preferences
- `POST /api/users/{user_id}/preferences` - Set user preferences

### Restaurants
- `GET /api/restaurants/` - Search restaurants
- `GET /api/restaurants/{restaurant_id}` - Get restaurant details
- `POST /api/restaurants/` - Create restaurant
- `PUT /api/restaurants/{restaurant_id}` - Update restaurant
- `DELETE /api/restaurants/{restaurant_id}` - Delete restaurant

### Reviews
- `GET /api/reviews/restaurant/{restaurant_id}` - Get reviews
- `POST /api/reviews/restaurant/{restaurant_id}` - Create review
- `PUT /api/reviews/{review_id}` - Update review
- `DELETE /api/reviews/{review_id}` - Delete review

### Favorites
- `GET /api/favorites/user/{user_id}` - Get user favorites
- `POST /api/favorites/` - Add favorite
- `DELETE /api/favorites/{favorite_id}` - Remove favorite

### AI Assistant
- `POST /api/ai-assistant/chat` - Chat with AI assistant

## Database Schema

See `DATABASE_SCHEMA.md` for detailed schema information.

## Project Structure

```
yelp_backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── routes/
│   │   ├── auth.py          # Authentication routes
│   │   ├── users.py         # User routes
│   │   ├── restaurants.py   # Restaurant routes
│   │   ├── reviews.py       # Review routes
│   │   ├── favorites.py     # Favorite routes
│   │   └── ai_assistant.py  # AI assistant routes
│   ├── services/
│   │   └── ai_service.py    # AI service logic
│   └── utils/
│       └── security.py      # Security utilities
├── requirements.txt
├── .env
└── .gitignore
```

## Testing the APIs

Use Postman and test each endpoint. 

```bash
# Use with Postman
# Import the schema in Postman: File > Import > Link
```

## Deployment

For production deployment:

1. Update `.env` with production values
2. Set `DEBUG=False`
3. Use a production ASGI server (Gunicorn):
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```

## Troubleshooting

**Database Connection Error**:
- Ensure MySQL is running
- Check database credentials in `.env`
- Verify database exists: `SHOW DATABASES;`

**Import Errors**:
- Verify all packages installed: `pip install -r requirements.txt`
- Check Python version (3.8+)

**API Port Already in Use**:
```bash
# Change port in uvicorn command or find process:
lsof -i :8000  # Find process on port 8000
kill -9 <PID>  # Kill the process
```

## License

MIT License - See LICENSE file for details
