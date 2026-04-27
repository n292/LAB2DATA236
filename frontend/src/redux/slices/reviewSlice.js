import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  restaurantReviews: [],
  userReviews: [],
  loading: false,
  error: null,
};

const reviewSlice = createSlice({
  name: 'reviews',
  initialState,
  reducers: {
    setRestaurantReviews: (state, action) => {
      state.restaurantReviews = action.payload;
      state.loading = false;
    },
    setUserReviews: (state, action) => {
      state.userReviews = action.payload;
      state.loading = false;
    },
    addReview: (state, action) => {
      state.restaurantReviews.unshift(action.payload);
    },
    removeReview: (state, action) => {
      state.restaurantReviews = state.restaurantReviews.filter(r => r.id !== action.payload);
      state.userReviews = state.userReviews.filter(r => r.id !== action.payload);
    },
    setReviewLoading: (state) => {
      state.loading = true;
    }
  },
});

export const { setRestaurantReviews, setUserReviews, addReview, removeReview, setReviewLoading } = reviewSlice.actions;
export default reviewSlice.reducer;
