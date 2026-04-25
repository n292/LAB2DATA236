import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./slices/authSlice";
import restaurantsReducer from "./slices/restaurantsSlice";
import reviewsReducer from "./slices/reviewsSlice";
import favoritesReducer from "./slices/favoritesSlice";

const store = configureStore({
  reducer: {
    auth: authReducer,
    restaurants: restaurantsReducer,
    reviews: reviewsReducer,
    favorites: favoritesReducer,
  },
  devTools: process.env.NODE_ENV !== "production",
});

export default store;