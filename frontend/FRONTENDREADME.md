# Yelp Prototype - Frontend (React)

A modern React-based frontend for a Yelp-like restaurant discovery platform with AI-powered recommendations.

## Features

- User authentication (signup/login)
- Restaurant search and filtering
- Detailed restaurant views with reviews
- Favorite restaurants management
- AI chatbot for personalized recommendations
- User profile and preferences management
- Responsive design for mobile, tablet, and desktop
- Bootstrap and custom CSS styling

## Stack

- **Framework**: React 18
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **UI Library**: React Bootstrap
- **Icons**: React Icons
- **Ratings**: React Star Ratings
- **Styling**: Bootstrap 5 + Custom CSS

## Prerequisites

- Node.js 14+ 
- npm or yarn

## Installation

1. **Navigate to Frontend Directory**:
   ```bash
   cd yelp_frontend
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Configure API URL**:
   - Update `.env` file:
     ```
     REACT_APP_API_URL=http://localhost:8000/api
     ```

## Running the Frontend

```bash
npm start
```

The application will be available at `http://localhost:3000`

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Project Structure

```
yelp_frontend/
├── public/
│   └── index.html           # HTML entry point
├── src/
│   ├── components/
│   │   ├── Auth/            # Login, Signup components
│   │   ├── Profile/         # Profile, Preferences components
│   │   ├── Restaurant/      # Search, Details components
│   │   ├── Review/          # Review components
│   │   └── ChatBot/         # AI Chatbot component
│   ├── pages/               # Page components
│   ├── services/
│   │   ├── api.js           # Axios API client
│   │   └── auth.js          # Auth utilities
│   ├── App.jsx              # Main App component
│   ├── App.css              # Global styles
│   ├── index.jsx            # React entry point
│   └── index.css            # Global styles
├── package.json
├── .env
└── .gitignore
```

## Key Pages

### Public Pages
- **Home/Explore** (`/`) - Restaurant search and discovery
- **Restaurant Details** (`/restaurants/:id`) - Individual restaurant view
- **Login** (`/login`) - User authentication
- **Signup** (`/signup`) - User registration

### Protected Pages (Require Login)
- **AI Chatbot** (`/chatbot`) - AI assistant for recommendations
- **Profile** (`/profile`) - User profile management
- **Preferences** (`/preferences`) - AI preferences configuration

## Component Documentation

### Authentication Components
- `Login.jsx` - User login form
- `Signup.jsx` - User registration form

### Profile Components
- `ProfilePage.jsx` - User profile view and edit
- `PreferencesEditor.jsx` - AI preferences configuration

### Restaurant Components
- `RestaurantSearch.jsx` - Search and browse restaurants
- `RestaurantDetails.jsx` - Detailed view with reviews

### Chatbot Component
- `AIChatbot.jsx` - AI assistant interface with recommendations

## Environment Variables

Create a `.env` file in the project root:

```env
REACT_APP_API_URL=http://localhost:8000/api
```

```

## Features Implementation

### Authentication Flow
1. User signs up/logs in
2. JWT token stored in localStorage
3. Token automatically added to API requests
4. Protected routes validate authentication
5. Logout clears token and redirects to login

### Restaurant Search
- Real-time search and filtering
- Multiple filter options
- Responsive restaurant cards
- Quick view and detailed page

### AI Chatbot
- Natural language queries
- Personalized recommendations
- Real-time responses
- Quick action buttons

### User Preferences
- Cuisine preferences
- Price range selection
- Dietary restrictions
- Ambiance preferences
- Location preferences
- Sort preferences


## Testing

To test the application:

1. **Start Backend Server** (see backend README)
2. **Start Frontend Application**: `npm start`
3. **Test User Flow**:
   - Navigate to `/signup` and create account
   - Search for restaurants
   - Add restaurants to favorites
   - Write reviews
   - Use AI chatbot for recommendations
   - Update profile and preferences

## License

MIT License - See LICENSE file for details
