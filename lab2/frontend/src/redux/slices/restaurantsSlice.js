import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { restaurantsAPI, favoritesAPI } from "../../services/api";

export const fetchRestaurants = createAsyncThunk(
  "restaurants/fetchRestaurants",
  async ({ filters = {}, userId = null } = {}, { rejectWithValue }) => {
    try {
      const params = {};

      if (filters.name) params.name = filters.name;
      if (filters.cuisine) params.cuisine = filters.cuisine;
      if (filters.city) params.city = filters.city;
      if (filters.keyword) params.keywords = filters.keyword;

      const response = await restaurantsAPI.search(params);
      let restaurants = Array.isArray(response.data) ? response.data : [];

      if (userId) {
        const favoriteChecks = await Promise.all(
          restaurants.map(async (restaurant) => {
            try {
              const favResponse = await favoritesAPI.check(userId, restaurant.id);

              return {
                restaurantId: restaurant.id,
                isFavorite: Boolean(favResponse?.data?.is_favorite),
                favoriteId: favResponse?.data?.favorite_id || null,
              };
            } catch {
              return {
                restaurantId: restaurant.id,
                isFavorite: false,
                favoriteId: null,
              };
            }
          })
        );

        restaurants = restaurants.map((restaurant) => {
          const match = favoriteChecks.find(
            (item) => Number(item.restaurantId) === Number(restaurant.id)
          );

          return {
            ...restaurant,
            isFavorite: match ? match.isFavorite : false,
            favoriteId: match ? match.favoriteId : null,
          };
        });
      }

      return restaurants;
    } catch (error) {
      return rejectWithValue(
        error?.response?.data?.detail || "Failed to fetch restaurants"
      );
    }
  }
);

export const fetchRestaurantDetails = createAsyncThunk(
  "restaurants/fetchRestaurantDetails",
  async (restaurantId, { rejectWithValue }) => {
    try {
      const response = await restaurantsAPI.getDetails(restaurantId);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error?.response?.data?.detail || "Failed to fetch restaurant details"
      );
    }
  }
);

const restaurantsSlice = createSlice({
  name: "restaurants",

  initialState: {
    list: [],
    selected: null,
    filters: {
      name: "",
      cuisine: "",
      city: "",
      keyword: "",
    },
    loading: false,
    detailsLoading: false,
    error: null,
    message: null,
  },

  reducers: {
    setRestaurantFilters: (state, action) => {
      state.filters = {
        ...state.filters,
        ...action.payload,
      };
    },

    clearRestaurantFilters: (state) => {
      state.filters = {
        name: "",
        cuisine: "",
        city: "",
        keyword: "",
      };
    },

    updateRestaurantFavoriteState: (state, action) => {
      const { restaurantId, isFavorite, favoriteId } = action.payload;

      state.list = state.list.map((restaurant) =>
        Number(restaurant.id) === Number(restaurantId)
          ? {
              ...restaurant,
              isFavorite,
              favoriteId,
            }
          : restaurant
      );

      if (state.selected && Number(state.selected.id) === Number(restaurantId)) {
        state.selected = {
          ...state.selected,
          isFavorite,
          favoriteId,
        };
      }
    },

    clearRestaurantMessage: (state) => {
      state.message = null;
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(fetchRestaurants.pending, (state) => {
        state.loading = true;
        state.error = null;
      })

      .addCase(fetchRestaurants.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload;
      })

      .addCase(fetchRestaurants.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Failed to fetch restaurants";
      })

      .addCase(fetchRestaurantDetails.pending, (state) => {
        state.detailsLoading = true;
        state.error = null;
      })

      .addCase(fetchRestaurantDetails.fulfilled, (state, action) => {
        state.detailsLoading = false;
        state.selected = action.payload;
      })

      .addCase(fetchRestaurantDetails.rejected, (state, action) => {
        state.detailsLoading = false;
        state.error = action.payload || "Failed to fetch restaurant details";
      });
  },
});

export const {
  setRestaurantFilters,
  clearRestaurantFilters,
  updateRestaurantFavoriteState,
  clearRestaurantMessage,
} = restaurantsSlice.actions;

export const selectRestaurants = (state) => state.restaurants.list;
export const selectSelectedRestaurant = (state) => state.restaurants.selected;
export const selectRestaurantFilters = (state) => state.restaurants.filters;
export const selectRestaurantsLoading = (state) => state.restaurants.loading;
export const selectRestaurantDetailsLoading = (state) =>
  state.restaurants.detailsLoading;
export const selectRestaurantsError = (state) => state.restaurants.error;
export const selectRestaurantsMessage = (state) => state.restaurants.message;

export default restaurantsSlice.reducer;