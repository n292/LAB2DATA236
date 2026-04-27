import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useSelector } from 'react-redux';

function ProtectedRoute({ children }) {
  const location = useLocation();
  const { isLoggedIn } = useSelector((state) => state.auth);

  if (!isLoggedIn) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}

export default ProtectedRoute;