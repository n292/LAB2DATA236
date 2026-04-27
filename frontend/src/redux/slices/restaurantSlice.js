import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  list: [],
  selectedRestaurant: null,
  loading: false,
  error: null,
  filters: {
    cuisine: '',
    search: '',
  }
};

const restaurantSlice = createSlice({
  name: 'restaurants',
  initialState,
  reducers: {
    setRestaurants: (state, action) => {
      state.list = action.payload;
      state.loading = false;
    },
    selectRestaurant: (state, action) => {
      state.selectedRestaurant = action.payload;
      state.loading = false;
    },
    setLoading: (state) => {
      state.loading = true;
    },
    setError: (state, action) => {
      state.error = action.payload;
      state.loading = false;
    },
    updateFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    }
  },
});

export const { setRestaurants, selectRestaurant, setLoading, setError, updateFilters } = restaurantSlice.actions;
export default restaurantSlice.reducer;
