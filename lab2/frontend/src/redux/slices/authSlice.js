import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import authService from "../../services/auth";
import { getApiErrorMessage } from "../../utils/apiError";

function normalizeRole(role) {
  if (!role) return "user";

  let value = String(role).trim();

  if (value.includes(".")) {
    value = value.split(".").pop();
  }

  return value.toLowerCase();
}

function readAuthFromStorage() {
  const token = localStorage.getItem("access_token");
  const rawUserId = localStorage.getItem("user_id");
  const role = normalizeRole(localStorage.getItem("user_role"));

  const userId = rawUserId ? Number(rawUserId) : null;

  return {
    token,
    userId,
    role,
    session: token
      ? {
          token,
          userId,
          role,
        }
      : null,
    isAuthenticated: Boolean(token),
  };
}

const initialStoredAuth = readAuthFromStorage();

const initialState = {
  token: initialStoredAuth.token,
  userId: initialStoredAuth.userId,
  role: initialStoredAuth.role,
  session: initialStoredAuth.session,
  isAuthenticated: initialStoredAuth.isAuthenticated,
  loading: false,
  error: null,
};

export const loginUser = createAsyncThunk(
  "auth/loginUser",
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const data = await authService.login(email, password);

      const token = data.access_token || localStorage.getItem("access_token");
      const userId = data.user_id ?? authService.getUserId();
      const role = normalizeRole(data.role ?? authService.getUserRole());

      return {
        token,
        userId: userId ? Number(userId) : null,
        role,
        session: {
          token,
          userId: userId ? Number(userId) : null,
          role,
        },
      };
    } catch (error) {
      return rejectWithValue(getApiErrorMessage(error, "Login failed"));
    }
  }
);

export const signupUser = createAsyncThunk(
  "auth/signupUser",
  async ({ name, email, password, role = "user" }, { dispatch, rejectWithValue }) => {
    try {
      await authService.signup(name, email, password, role);

      const loginResult = await dispatch(
        loginUser({ email, password })
      ).unwrap();

      return loginResult;
    } catch (error) {
      return rejectWithValue(getApiErrorMessage(error, "Signup failed"));
    }
  }
);

export const logoutUser = createAsyncThunk("auth/logoutUser", async () => {
  authService.logout();

  return {
    token: null,
    userId: null,
    role: "user",
    session: null,
    isAuthenticated: false,
  };
});

export const syncAuthFromStorage = createAsyncThunk(
  "auth/syncAuthFromStorage",
  async () => {
    return readAuthFromStorage();
  }
);

const authSlice = createSlice({
  name: "auth",
  initialState,

  reducers: {
    clearAuthError: (state) => {
      state.error = null;
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })

      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
        state.token = action.payload.token;
        state.userId = action.payload.userId;
        state.role = action.payload.role;
        state.session = action.payload.session;
        state.isAuthenticated = true;
      })

      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Login failed";
        state.token = null;
        state.userId = null;
        state.role = "user";
        state.session = null;
        state.isAuthenticated = false;
      })

      .addCase(signupUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })

      .addCase(signupUser.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
        state.token = action.payload.token;
        state.userId = action.payload.userId;
        state.role = action.payload.role;
        state.session = action.payload.session;
        state.isAuthenticated = true;
      })

      .addCase(signupUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Signup failed";
      })

      .addCase(logoutUser.pending, (state) => {
        state.loading = false;
        state.error = null;
      })

      .addCase(logoutUser.fulfilled, (state, action) => {
        state.token = action.payload.token;
        state.userId = action.payload.userId;
        state.role = action.payload.role;
        state.session = action.payload.session;
        state.isAuthenticated = action.payload.isAuthenticated;
        state.loading = false;
        state.error = null;
      })

      .addCase(syncAuthFromStorage.fulfilled, (state, action) => {
        state.token = action.payload.token;
        state.userId = action.payload.userId;
        state.role = action.payload.role;
        state.session = action.payload.session;
        state.isAuthenticated = action.payload.isAuthenticated;
      });
  },
});

export const { clearAuthError } = authSlice.actions;

export const selectAuth = (state) => state.auth;
export const selectToken = (state) => state.auth.token;
export const selectUserId = (state) => state.auth.userId;
export const selectUserRole = (state) => state.auth.role;
export const selectSession = (state) => state.auth.session;
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated;
export const selectAuthLoading = (state) => state.auth.loading;
export const selectAuthError = (state) => state.auth.error;

export default authSlice.reducer;