import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { reviewsAPI } from "../../services/api";

export const fetchRestaurantReviews = createAsyncThunk(
  "reviews/fetchRestaurantReviews",
  async (restaurantId, { rejectWithValue }) => {
    try {
      const response = await reviewsAPI.getByRestaurant(restaurantId);

      return {
        restaurantId,
        reviews: Array.isArray(response.data) ? response.data : [],
      };
    } catch (error) {
      return rejectWithValue(
        error?.response?.data?.detail || "Failed to fetch reviews"
      );
    }
  }
);

export const fetchUserReviews = createAsyncThunk(
  "reviews/fetchUserReviews",
  async ({ userId, params = {} }, { rejectWithValue }) => {
    try {
      const response = await reviewsAPI.getByUser(userId, params);
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      return rejectWithValue(
        error?.response?.data?.detail || "Failed to fetch user reviews"
      );
    }
  }
);

export const createReview = createAsyncThunk(
  "reviews/createReview",
  async ({ restaurantId, userId, data }, { rejectWithValue }) => {
    try {
      const response = await reviewsAPI.create(restaurantId, userId, data);

      return {
        restaurantId,
        review: response.data,
      };
    } catch (error) {
      return rejectWithValue(
        error?.response?.data?.detail ||
          error?.response?.data?.message ||
          "Failed to create review"
      );
    }
  }
);

export const updateReview = createAsyncThunk(
  "reviews/updateReview",
  async ({ restaurantId, reviewId, data }, { rejectWithValue }) => {
    try {
      const response = await reviewsAPI.update(reviewId, data);

      return {
        restaurantId,
        reviewId,
        review: response.data,
      };
    } catch (error) {
      return rejectWithValue(
        error?.response?.data?.detail ||
          error?.response?.data?.message ||
          "Failed to update review"
      );
    }
  }
);

export const deleteReview = createAsyncThunk(
  "reviews/deleteReview",
  async ({ restaurantId, reviewId }, { rejectWithValue }) => {
    try {
      await reviewsAPI.delete(reviewId);

      return {
        restaurantId,
        reviewId,
      };
    } catch (error) {
      return rejectWithValue(
        error?.response?.data?.detail ||
          error?.response?.data?.message ||
          "Failed to delete review"
      );
    }
  }
);

const reviewsSlice = createSlice({
  name: "reviews",

  initialState: {
    byRestaurantId: {},
    userReviews: [],
    loadingByRestaurantId: {},
    userReviewsLoading: false,
    submitting: false,
    deletingById: {},
    error: null,
    lastUpdatedReviewId: null,
  },

  reducers: {
    clearReviewsError: (state) => {
      state.error = null;
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(fetchRestaurantReviews.pending, (state, action) => {
        const restaurantId = action.meta.arg;

        state.loadingByRestaurantId[restaurantId] = true;
        state.error = null;
      })

      .addCase(fetchRestaurantReviews.fulfilled, (state, action) => {
        const { restaurantId, reviews } = action.payload;

        state.loadingByRestaurantId[restaurantId] = false;
        state.byRestaurantId[restaurantId] = reviews;
      })

      .addCase(fetchRestaurantReviews.rejected, (state, action) => {
        const restaurantId = action.meta.arg;

        state.loadingByRestaurantId[restaurantId] = false;
        state.error = action.payload || "Failed to fetch reviews";
        state.byRestaurantId[restaurantId] = [];
      })

      .addCase(fetchUserReviews.pending, (state) => {
        state.userReviewsLoading = true;
        state.error = null;
      })

      .addCase(fetchUserReviews.fulfilled, (state, action) => {
        state.userReviewsLoading = false;
        state.userReviews = action.payload;
      })

      .addCase(fetchUserReviews.rejected, (state, action) => {
        state.userReviewsLoading = false;
        state.error = action.payload || "Failed to fetch user reviews";
      })

      .addCase(createReview.pending, (state) => {
        state.submitting = true;
        state.error = null;
      })

      .addCase(createReview.fulfilled, (state, action) => {
        const { restaurantId, review } = action.payload;

        state.submitting = false;
        state.lastUpdatedReviewId = review?.id || null;

        if (!state.byRestaurantId[restaurantId]) {
          state.byRestaurantId[restaurantId] = [];
        }

        state.byRestaurantId[restaurantId].push(review);
      })

      .addCase(createReview.rejected, (state, action) => {
        state.submitting = false;
        state.error = action.payload || "Failed to create review";
      })

      .addCase(updateReview.pending, (state) => {
        state.submitting = true;
        state.error = null;
      })

      .addCase(updateReview.fulfilled, (state, action) => {
        const { restaurantId, reviewId, review } = action.payload;

        state.submitting = false;
        state.lastUpdatedReviewId = reviewId;

        const existingReviews = state.byRestaurantId[restaurantId] || [];

        state.byRestaurantId[restaurantId] = existingReviews.map((item) =>
          Number(item.id) === Number(reviewId)
            ? {
                ...item,
                ...review,
              }
            : item
        );
      })

      .addCase(updateReview.rejected, (state, action) => {
        state.submitting = false;
        state.error = action.payload || "Failed to update review";
      })

      .addCase(deleteReview.pending, (state, action) => {
        const reviewId = action.meta.arg.reviewId;

        state.deletingById[reviewId] = true;
        state.error = null;
      })

      .addCase(deleteReview.fulfilled, (state, action) => {
        const { restaurantId, reviewId } = action.payload;

        state.deletingById[reviewId] = false;

        state.byRestaurantId[restaurantId] = (
          state.byRestaurantId[restaurantId] || []
        ).filter((review) => Number(review.id) !== Number(reviewId));
      })

      .addCase(deleteReview.rejected, (state, action) => {
        const reviewId = action.meta.arg.reviewId;

        state.deletingById[reviewId] = false;
        state.error = action.payload || "Failed to delete review";
      });
  },
});

export const { clearReviewsError } = reviewsSlice.actions;

export const selectReviewsByRestaurantId = (state) =>
  state.reviews.byRestaurantId;

export const selectRestaurantReviews = (restaurantId) => (state) =>
  state.reviews.byRestaurantId[restaurantId] || [];

export const selectReviewsLoadingByRestaurantId = (state) =>
  state.reviews.loadingByRestaurantId;

export const selectUserReviews = (state) => state.reviews.userReviews;

export const selectUserReviewsLoading = (state) =>
  state.reviews.userReviewsLoading;

export const selectReviewsSubmitting = (state) => state.reviews.submitting;

export const selectReviewsDeletingById = (state) =>
  state.reviews.deletingById;

export const selectReviewsError = (state) => state.reviews.error;

export default reviewsSlice.reducer;