import React, { useEffect, useState } from "react";
import { Container, Row, Col, Card, Button, Alert, Spinner, Badge, Tabs, Tab } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import { FaMapMarkerAlt, FaUtensils, FaStar, FaRegStar, FaTrash } from "react-icons/fa";
import "./Restaurant.css";

import { restaurantsAPI, reviewsAPI } from "../../services/api";
import authService from "../../services/auth";

const fallbackRestaurantImages = [
  "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?auto=format&fit=crop&w=1200&q=80",
];

function UserHistory() {
  const userId = authService.getUserId();
  const navigate = useNavigate();
  const [addedRestaurants, setAddedRestaurants] = useState([]);
  const [userReviews, setUserReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("restaurants");

  useEffect(() => {
    if (!userId) {
      navigate("/login");
      return;
    }

    fetchHistory();
  }, [userId, navigate]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      // Fetch restaurants added/owned by user
      const restaurantsResponse = await restaurantsAPI.getByUser(userId);
      setAddedRestaurants(Array.isArray(restaurantsResponse.data) ? restaurantsResponse.data : []);
      
      // Fetch reviews by user
      const reviewsResponse = await reviewsAPI.getByUser(userId);
      setUserReviews(Array.isArray(reviewsResponse.data) ? reviewsResponse.data : []);
      
      setError(null);
    } catch (err) {
      console.error("Error fetching history:", err);
      setError("Failed to load your history");
    } finally {
      setLoading(false);
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
      <h1 className="mb-4">My History</h1>

      {error && <Alert variant="danger">{error}</Alert>}

      <Tabs
        id="history-tabs"
        activeKey={activeTab}
        onSelect={(k) => setActiveTab(k)}
        className="mb-4"
      >
        <Tab eventKey="restaurants" title="Restaurants I Added">
          {addedRestaurants.length === 0 ? (
            <Alert variant="info">
              You haven't added any restaurants yet.{" "}
              <Link to="/restaurants/new">Add one now!</Link>
            </Alert>
          ) : (
            <Row>
              {addedRestaurants.map((restaurant) => (
                <Col key={restaurant.id} md={6} lg={4} className="mb-4">
                  <Card className="h-100 restaurant-card">
                    <div className="restaurant-image-container">
                      <Card.Img
                        variant="top"
                        src={restaurant?.photo_data || getRandomImage(restaurant.id)}
                        alt={restaurant.name}
                        className="restaurant-image"
                      />
                    </div>

                    <Card.Body className="d-flex flex-column">
                      <Card.Title className="mb-2">{restaurant.name}</Card.Title>

                      <div className="mb-2 text-muted">
                        <FaUtensils className="me-2" />
                        {restaurant.cuisine_type}
                      </div>

                      <div className="mb-2 text-muted">
                        <FaMapMarkerAlt className="me-2" />
                        {restaurant.city}
                      </div>

                      <div className="mb-3">
                        <div className="rating mb-1">
                          {Array(5)
                            .fill(0)
                            .map((_, i) => (
                              <FaStar
                                key={i}
                                className={
                                  i < Math.round(restaurant.average_rating)
                                    ? "star-filled"
                                    : "star-empty"
                                }
                              />
                            ))}
                          <span className="ms-2 text-muted">
                            {restaurant.average_rating.toFixed(1)} (
                            {restaurant.review_count} reviews)
                          </span>
                        </div>
                        {restaurant.pricing_tier && (
                          <Badge bg="info">{restaurant.pricing_tier}</Badge>
                        )}
                      </div>

                      <div className="mt-auto">
                        <Link
                          to={`/restaurants/${restaurant.id}`}
                          className="btn btn-primary btn-sm w-100"
                        >
                          View Details
                        </Link>
                      </div>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          )}
        </Tab>

        <Tab eventKey="reviews" title="My Reviews">
          {userReviews.length === 0 ? (
            <Alert variant="info">
              You haven't written any reviews yet. <Link to="/">Find a restaurant</Link> to review!
            </Alert>
          ) : (
            <Row>
              {userReviews.map((review) => (
                <Col key={review.id} md={6} lg={4} className="mb-4">
                  <Card className="h-100">
                    <Card.Body>
                      <Card.Title>{review.restaurant?.name || "Restaurant"}</Card.Title>
                      <div className="mb-2">
                        {[...Array(5)].map((_, i) => (
                          <FaStar
                            key={i}
                            className={i < review.rating ? "star-filled" : "star-empty"}
                            size={14}
                          />
                        ))}
                        <span className="ms-2 text-muted">{review.rating}/5</span>
                      </div>
                      <p className="text-muted small mb-3">{review.comment}</p>
                      <small className="text-muted">
                        {new Date(review.created_at).toLocaleDateString()}
                      </small>
                      <div className="mt-3">
                        <Link to={`/restaurants/${review.restaurant?.id}`} className="btn btn-sm btn-primary">
                          View Restaurant
                        </Link>
                      </div>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          )}
        </Tab>

        <Tab eventKey="activity" title="Activity">
          <Alert variant="info">
            <p><strong>Your Activity Summary:</strong></p>
            <ul>
              <li>Restaurants Added: {addedRestaurants.length}</li>
              <li>Reviews Written: {userReviews.length}</li>
            </ul>
          </Alert>
        </Tab>
      </Tabs>
    </Container>
  );
}

export default UserHistory;
