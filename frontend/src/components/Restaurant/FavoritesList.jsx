import React, { useEffect, useState } from "react";
import { Container, Row, Col, Card, Button, Alert, Spinner, Badge } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import { FaMapMarkerAlt, FaUtensils, FaStar, FaTrash, FaPhone } from "react-icons/fa";
import "./Restaurant.css";

import { favoritesAPI } from "../../services/api";
import authService from "../../services/auth";

const fallbackRestaurantImages = [
  "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?auto=format&fit=crop&w=1200&q=80",
];

function FavoritesList() {
  const userId = authService.getUserId();
  const navigate = useNavigate();
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [removingId, setRemovingId] = useState(null);

  useEffect(() => {
    if (!userId) {
      navigate("/login");
      return;
    }
    
    fetchFavorites();
  }, [userId, navigate]);

  const fetchFavorites = async () => {
    try {
      setLoading(true);
      const response = await favoritesAPI.getByUser(userId);
      setFavorites(Array.isArray(response.data) ? response.data : []);
      setError(null);
    } catch (err) {
      console.error("Error fetching favorites:", err);
      setError("Failed to load your favorite restaurants");
      setFavorites([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFavorite = async (favoriteId, restaurantId) => {
    try {
      setRemovingId(favoriteId);
      await favoritesAPI.remove(favoriteId);
      setFavorites(favorites.filter(fav => fav.id !== favoriteId));
    } catch (err) {
      console.error("Error removing favorite:", err);
      alert("Failed to remove favorite. Please try again.");
    } finally {
      setRemovingId(null);
    }
  };

  const getRandomImage = (resId) => {
    return fallbackRestaurantImages[resId % fallbackRestaurantImages.length];
  };

  if (loading) {
    return (
      <Container className="py-5 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </Container>
    );
  }

  return (
    <Container className="py-5">
      <h1 className="mb-4">My Favorite Restaurants</h1>
      
      {error && <Alert variant="danger">{error}</Alert>}

      {favorites.length === 0 ? (
        <Alert variant="info">
          No favorite restaurants yet. <Link to="/">Start exploring</Link> to add some!
        </Alert>
      ) : (
        <Row>
          {favorites.map((favorite) => {
            const restaurant = favorite.restaurant;
            return (
              <Col key={favorite.id} md={6} lg={4} className="mb-4">
                <Card className="h-100 restaurant-card">
                  <div className="restaurant-image-container">
                    <Card.Img
                      variant="top"
                      src={restaurant?.photo_data || getRandomImage(restaurant.id)}
                      alt={restaurant.name}
                      className="restaurant-image"
                    />
                    <Badge bg="danger" className="favorite-badge">
                      <FaStar className="me-1" />
                      Favorite
                    </Badge>
                  </div>

                  <Card.Body className="d-flex flex-column">
                    <Card.Title className="mb-2">{restaurant.name}</Card.Title>

                    <div className="mb-2 text-muted">
                      <FaUtensils className="me-2" />
                      {restaurant.cuisine_type}
                    </div>

                    <div className="mb-2 text-muted">
                      <FaMapMarkerAlt className="me-2" />
                      {restaurant.city}, {restaurant.state || "USA"}
                    </div>

                    {restaurant.phone && (
                      <div className="mb-3 text-muted">
                        <FaPhone className="me-2" />
                        {restaurant.phone}
                      </div>
                    )}

                    <div className="mb-3">
                      <div className="rating mb-1">
                        {Array(5)
                          .fill(0)
                          .map((_, i) => (
                            <FaStar
                              key={i}
                              className={i < Math.round(restaurant.average_rating) ? "star-filled" : "star-empty"}
                            />
                          ))}
                        <span className="ms-2 text-muted">
                          {restaurant.average_rating.toFixed(1)} ({restaurant.review_count} reviews)
                        </span>
                      </div>
                      {restaurant.pricing_tier && (
                        <Badge bg="info">{restaurant.pricing_tier}</Badge>
                      )}
                    </div>

                    <div className="mt-auto">
                      <Link to={`/restaurants/${restaurant.id}`} className="btn btn-primary btn-sm me-2 mb-2">
                        View Details
                      </Link>
                      <Button
                        variant="outline-danger"
                        size="sm"
                        onClick={() => handleRemoveFavorite(favorite.id, restaurant.id)}
                        disabled={removingId === favorite.id}
                        className="mb-2"
                      >
                        <FaTrash className="me-1" />
                        {removingId === favorite.id ? "Removing..." : "Remove"}
                      </Button>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            );
          })}
        </Row>
      )}
    </Container>
  );
}

export default FavoritesList;
