import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  items: [],
  loading: false,
  error: null,
};

const favoritesSlice = createSlice({
  name: 'favorites',
  initialState,
  reducers: {
    setFavorites: (state, action) => {
      state.items = action.payload;
      state.loading = false;
    },
    addFavorite: (state, action) => {
      if (!state.items.find(item => item.id === action.payload.id)) {
        state.items.push(action.payload);
      }
    },
    removeFavorite: (state, action) => {
      state.items = state.items.filter(item => item.id !== action.payload);
    },
    setFavLoading: (state) => {
      state.loading = true;
    }
  },
});

export const { setFavorites, addFavorite, removeFavorite, setFavLoading } = favoritesSlice.actions;
export default favoritesSlice.reducer;
