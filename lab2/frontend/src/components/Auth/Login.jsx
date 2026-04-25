import React, { useState } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { Container, Form, Button, Alert, Spinner } from "react-bootstrap";

import {
  clearAuthError,
  loginUser,
  selectAuthError,
  selectAuthLoading,
} from "../../redux/slices/authSlice";

import "./Auth.css";

function Login() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();

  const loading = useSelector(selectAuthLoading);
  const error = useSelector(selectAuthError);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const from = location.state?.from?.pathname || "/";

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (loading) return;

    dispatch(clearAuthError());

    try {
      await dispatch(loginUser({ email, password })).unwrap();
      navigate(from, { replace: true });
    } catch {
      // Redux stores the rejected error in auth.error.
    }
  };

  return (
    <Container className="auth-container">
      <div className="auth-card">
        <h1>Welcome Back</h1>
        <p className="text-muted">Sign in to your LabPair-45 Eats account</p>

        {error && (
          <Alert variant="danger" className="mb-3">
            {typeof error === "string" ? error : "Invalid email or password"}
          </Alert>
        )}

        <Form onSubmit={handleSubmit} noValidate>
          <Form.Group className="mb-3">
            <Form.Label>Email</Form.Label>

            <Form.Control
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Password</Form.Label>

            <Form.Control
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </Form.Group>

          <Button
            variant="danger"
            type="submit"
            className="w-100 mb-3"
            disabled={loading}
          >
            {loading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Signing in...
              </>
            ) : (
              "Sign In"
            )}
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