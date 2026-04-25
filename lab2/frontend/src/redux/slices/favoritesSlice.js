import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { favoritesAPI } from "../../services/api";
import { updateRestaurantFavoriteState } from "./restaurantsSlice";

export const fetchFavorites = createAsyncThunk(
  "favorites/fetchFavorites",
  async (userId, { rejectWithValue }) => {
    try {
      const response = await favoritesAPI.getByUser(userId);
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      return rejectWithValue(
        error?.response?.data?.detail || "Failed to fetch favourites"
      );
    }
  }
);

export const checkFavorite = createAsyncThunk(
  "favorites/checkFavorite",
  async ({ userId, restaurantId }, { dispatch, rejectWithValue }) => {
    try {
      const response = await favoritesAPI.check(userId, restaurantId);

      const payload = {
        restaurantId,
        isFavorite: Boolean(response?.data?.is_favorite),
        favoriteId: response?.data?.favorite_id || null,
      };

      dispatch(updateRestaurantFavoriteState(payload));

      return payload;
    } catch (error) {
      return rejectWithValue(
        error?.response?.data?.detail || "Failed to check favourite"
      );
    }
  }
);

export const addFavorite = createAsyncThunk(
  "favorites/addFavorite",
  async ({ restaurantId, userId }, { dispatch, rejectWithValue }) => {
    try {
      const response = await favoritesAPI.add(restaurantId, userId);

      const payload = {
        restaurantId,
        favorite: response.data,
        favoriteId: response?.data?.id || null,
      };

      dispatch(
        updateRestaurantFavoriteState({
          restaurantId,
          isFavorite: true,
          favoriteId: payload.favoriteId,
        })
      );

      return payload;
    } catch (error) {
      return rejectWithValue(
        error?.response?.data?.detail || "Failed to add favourite"
      );
    }
  }
);

export const removeFavorite = createAsyncThunk(
  "favorites/removeFavorite",
  async ({ favoriteId, restaurantId }, { dispatch, rejectWithValue }) => {
    try {
      if (favoriteId) {
        await favoritesAPI.remove(favoriteId);
      }

      dispatch(
        updateRestaurantFavoriteState({
          restaurantId,
          isFavorite: false,
          favoriteId: null,
        })
      );

      return {
        favoriteId,
        restaurantId,
      };
    } catch (error) {
      return rejectWithValue(
        error?.response?.data?.detail || "Failed to remove favourite"
      );
    }
  }
);

const favoritesSlice = createSlice({
  name: "favorites",

  initialState: {
    items: [],
    byRestaurantId: {},
    loading: false,
    actionLoadingByRestaurantId: {},
    error: null,
  },

  reducers: {
    clearFavoritesError: (state) => {
      state.error = null;
    },

    resetFavorites: (state) => {
      state.items = [];
      state.byRestaurantId = {};
      state.loading = false;
      state.actionLoadingByRestaurantId = {};
      state.error = null;
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(fetchFavorites.pending, (state) => {
        state.loading = true;
        state.error = null;
      })

      .addCase(fetchFavorites.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;

        state.byRestaurantId = action.payload.reduce((acc, favorite) => {
          const restaurantId =
            favorite?.restaurant?.id || favorite?.restaurant_id;

          if (restaurantId) {
            acc[restaurantId] = {
              isFavorite: true,
              favoriteId: favorite.id,
            };
          }

          return acc;
        }, {});
      })

      .addCase(fetchFavorites.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Failed to fetch favourites";
      })

      .addCase(checkFavorite.fulfilled, (state, action) => {
        const { restaurantId, isFavorite, favoriteId } = action.payload;

        state.byRestaurantId[restaurantId] = {
          isFavorite,
          favoriteId,
        };
      })

      .addCase(addFavorite.pending, (state, action) => {
        const restaurantId = action.meta.arg.restaurantId;

        state.actionLoadingByRestaurantId[restaurantId] = true;
        state.error = null;
      })

      .addCase(addFavorite.fulfilled, (state, action) => {
        const { restaurantId, favorite, favoriteId } = action.payload;

        state.actionLoadingByRestaurantId[restaurantId] = false;

        state.byRestaurantId[restaurantId] = {
          isFavorite: true,
          favoriteId,
        };

        if (favorite) {
          const exists = state.items.some(
            (item) => Number(item.id) === Number(favorite.id)
          );

          if (!exists) {
            state.items.push(favorite);
          }
        }
      })

      .addCase(addFavorite.rejected, (state, action) => {
        const restaurantId = action.meta.arg.restaurantId;

        state.actionLoadingByRestaurantId[restaurantId] = false;
        state.error = action.payload || "Failed to add favourite";
      })

      .addCase(removeFavorite.pending, (state, action) => {
        const restaurantId = action.meta.arg.restaurantId;

        state.actionLoadingByRestaurantId[restaurantId] = true;
        state.error = null;
      })

      .addCase(removeFavorite.fulfilled, (state, action) => {
        const { favoriteId, restaurantId } = action.payload;

        state.actionLoadingByRestaurantId[restaurantId] = false;

        state.items = state.items.filter(
          (favorite) => Number(favorite.id) !== Number(favoriteId)
        );

        state.byRestaurantId[restaurantId] = {
          isFavorite: false,
          favoriteId: null,
        };
      })

      .addCase(removeFavorite.rejected, (state, action) => {
        const restaurantId = action.meta.arg.restaurantId;

        state.actionLoadingByRestaurantId[restaurantId] = false;
        state.error = action.payload || "Failed to remove favourite";
      });
  },
});

export const {
  clearFavoritesError,
  resetFavorites,
} = favoritesSlice.actions;

export const selectFavorites = (state) => state.favorites.items;

export const selectFavoritesByRestaurantId = (state) =>
  state.favorites.byRestaurantId;

export const selectFavoritesLoading = (state) => state.favorites.loading;

export const selectFavoriteActionLoadingByRestaurantId = (state) =>
  state.favorites.actionLoadingByRestaurantId;

export const selectFavoritesError = (state) => state.favorites.error;

export default favoritesSlice.reducer;