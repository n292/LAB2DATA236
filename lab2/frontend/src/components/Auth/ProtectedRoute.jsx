import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import authService from "../../services/auth";

function ProtectedRoute({ children }) {
  const location = useLocation();
  const isLoggedIn = !!authService.getToken?.();

  if (!isLoggedIn) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}

export default ProtectedRoute;