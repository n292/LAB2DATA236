import React, { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from "react-router-dom";
import { Container, Navbar, Nav } from "react-bootstrap";
import { useSelector, useDispatch } from 'react-redux';
import { logout } from './redux/slices/authSlice';
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

import RestaurantSearch from "./components/Restaurant/RestaurantSearch";
import RestaurantDetails from "./components/Restaurant/RestaurantDetails";
import AddRestaurantForm from "./components/Restaurant/AddRestaurantForm";
import WriteReviewPage from "./components/Restaurant/WriteReviewPage";
import FavoritesList from "./components/Restaurant/FavoritesList";
import UserHistory from "./components/Restaurant/UserHistory";
import OwnerDashboard from "./components/Restaurant/OwnerDashboard";
import Login from "./components/Auth/Login";
import Signup from "./components/Auth/Signup";
import ProfilePage from "./components/Profile/ProfilePage";
import PreferencesEditor from "./components/Profile/PreferencesEditor";
import AIChatbot from "./components/ChatBot/AIChatbot";
import ProtectedRoute from "./components/Auth/ProtectedRoute";

function AppLayout() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { isLoggedIn, user } = useSelector((state) => state.auth);

  const handleLogout = () => {
    dispatch(logout());
    navigate("/login");
  };

  return (
    <div className="app">
      <Navbar expand="lg" className="navbar-custom" sticky="top">
        <Container>
          <Navbar.Brand as={Link} to="/" className="brand-logo">
            LabPair-45 Eats
          </Navbar.Brand>

          <Navbar.Toggle aria-controls="main-navbar-nav" />

          <Navbar.Collapse id="main-navbar-nav">
            <Nav className="ms-auto">
              <Nav.Link as={Link} to="/">
                Restaurants
              </Nav.Link>

              {isLoggedIn && (
                <>
                  <Nav.Link as={Link} to="/restaurants/new">
                    Add Restaurant
                  </Nav.Link>
                  <Nav.Link as={Link} to="/favorites">
                    Favorites
                  </Nav.Link>
                  <Nav.Link as={Link} to="/history">
                    History
                  </Nav.Link>
                  <Nav.Link as={Link} to="/owner/dashboard">
                    Dashboard
                  </Nav.Link>
                  <Nav.Link as={Link} to="/chatbot">
                    Assistant
                  </Nav.Link>
                  <Nav.Link as={Link} to="/profile">
                    Profile
                  </Nav.Link>
                  <Nav.Link as={Link} to="/preferences">
                    Preferences
                  </Nav.Link>
                </>
              )}

              {isLoggedIn ? (
                <Nav.Link as="button" onClick={handleLogout} className="nav-link btn btn-link">
                  Log Out
                </Nav.Link>
              ) : (
                <>
                  <Nav.Link as={Link} to="/login">
                    Log In
                  </Nav.Link>
                  <Nav.Link as={Link} to="/signup">
                    Sign Up
                  </Nav.Link>
                </>
              )}
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <main>
        <Routes>
          <Route path="/" element={<RestaurantSearch />} />
          <Route path="/restaurants/:id" element={<RestaurantDetails />} />

          <Route
            path="/restaurants/new"
            element={
              <ProtectedRoute>
                <AddRestaurantForm />
              </ProtectedRoute>
            }
          />

          <Route
            path="/restaurants/:id/edit"
            element={
              <ProtectedRoute>
                <AddRestaurantForm />
              </ProtectedRoute>
            }
          />

          <Route
            path="/restaurants/:id/review"
            element={
              <ProtectedRoute>
                <WriteReviewPage />
              </ProtectedRoute>
            }
          />

          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/preferences"
            element={
              <ProtectedRoute>
                <PreferencesEditor />
              </ProtectedRoute>
            }
          />

          <Route
            path="/chatbot"
            element={
              <ProtectedRoute>
                <AIChatbot />
              </ProtectedRoute>
            }
          />

          <Route
            path="/favorites"
            element={
              <ProtectedRoute>
                <FavoritesList />
              </ProtectedRoute>
            }
          />

          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <UserHistory />
              </ProtectedRoute>
            }
          />

          <Route
            path="/owner/dashboard"
            element={
              <ProtectedRoute>
                <OwnerDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>

      <footer className="footer">
        <Container>
          <div className="footer-content">
            <p>© 2026 LabPair-45 Eats</p>
            <div className="footer-nav">
              <Link to="/">Restaurants</Link>
              {isLoggedIn ? (
                <>
                  <Link to="/restaurants/new">Add Restaurant</Link>
                  <Link to="/chatbot">Assistant</Link>
                  <Link to="/profile">Profile</Link>
                  <Link to="/preferences">Preferences</Link>
                </>
              ) : (
                <>
                  <Link to="/login">Log In</Link>
                  <Link to="/signup">Sign Up</Link>
                </>
              )}
            </div>
          </div>
        </Container>
      </footer>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppLayout />
    </Router>
  );
}

export default App;