import React, { useState } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { Container, Form, Button, Alert } from "react-bootstrap";
import { useDispatch, useSelector } from 'react-redux';
import { loginStart, loginSuccess, loginFailure } from '../../redux/slices/authSlice';
import authService from "../../services/auth";
import "./Auth.css";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { loading, error } = useSelector((state) => state.auth);
  const dispatch = useDispatch();

  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || "/";

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (loading) return;

    dispatch(loginStart());

    try {
      const response = await authService.login(email, password);
      // Assuming authService.login returns the user and token
      // If it doesn't return user, we might need another fetch
      const userData = JSON.parse(localStorage.getItem('user'));
      const token = localStorage.getItem('token');
      
      dispatch(loginSuccess({ user: userData, token: token }));
      navigate(from, { replace: true });
    } catch (err) {
      console.error("Login error:", err);

      const errorMessage =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.detail ||
        err?.message ||
        "Invalid email or password";

      dispatch(loginFailure(typeof errorMessage === "string" ? errorMessage : "Invalid email or password"));
    }
  };

  return (
    <Container className="auth-container">
      <div className="auth-card">
        <h1>Welcome Back</h1>
        <p className="text-muted">Sign in to your LabPair-45 Eats account</p>

        {error && (
          <Alert variant="danger" className="mb-3">
            {error}
          </Alert>
        )}

        <Form onSubmit={handleSubmit} noValidate>
          <Form.Group className="mb-3">
            <Form.Label>Email</Form.Label>
            <Form.Control
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
              }}
              required
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Password</Form.Label>
            <Form.Control
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
              }}
              required
            />
          </Form.Group>

          <Button
            variant="danger"
            type="submit"
            className="w-100 mb-3"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign In"}
          </Button>
        </Form>

        <p className="text-center mb-0">
          Don't have an account? <Link to="/signup">Sign up here</Link>
        </p>
      </div>
    </Container>
  );
}

export default Login;