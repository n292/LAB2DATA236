import React, { useEffect, useState } from "react";
import { Container, Row, Col, Card, Button, Alert, Spinner, Table, Badge } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import { FaChartBar, FaStar, FaComments, FaHeart, FaEdit, FaTrash } from "react-icons/fa";
import "./Restaurant.css";

import { restaurantsAPI } from "../../services/api";
import authService from "../../services/auth";

function OwnerDashboard() {
  const userId = authService.getUserId();
  const userRole = authService.getUserRole();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  console.log('OwnerDashboard loaded, userId:', userId, 'userRole:', userRole);

  useEffect(() => {
    if (!userId) {
      console.error('No userId found, redirecting to login');
      navigate("/login");
      return;
    }

    if (userRole !== "owner") {
      console.error('User role is not owner:', userRole);
      setError(`You must be an owner to access this page. Your role: ${userRole}`);
      setLoading(false);
      return;
    }

    fetchDashboard();
  }, [userId, userRole, navigate]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      console.log('Fetching dashboard...');
      const response = await restaurantsAPI.getOwnerDashboard();
      console.log('Dashboard response:', response);
      setDashboard(response.data || response);
      setError(null);
    } catch (err) {
      console.error("Error fetching dashboard:", err);
      const errorMsg = err.response?.data?.detail || err.message || "Failed to load your dashboard";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRestaurant = async (restaurantId) => {
    if (window.confirm("Are you sure you want to delete this restaurant?")) {
      try {
        setDeletingId(restaurantId);
        await restaurantsAPI.delete(restaurantId);
        fetchDashboard();
      } catch (err) {
        console.error("Error deleting restaurant:", err);
        alert("Failed to delete restaurant");
      } finally {
        setDeletingId(null);
      }
    }
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

  if (error) {
    return (
      <Container className="py-5">
        <Alert variant="danger">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container fluid className="py-5 bg-light">
      <Container>
        <h1 className="mb-4">
          <FaChartBar className="me-2" />
          Restaurant Owner Dashboard
        </h1>

        {/* Analytics Summary */}
        <Row className="mb-4">
          <Col md={3} className="mb-3">
            <Card className="text-center border-primary">
              <Card.Body>
                <h5 className="text-muted">Restaurants</h5>
                <h2 className="text-primary">{dashboard?.total_restaurants || 0}</h2>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3} className="mb-3">
            <Card className="text-center border-danger">
              <Card.Body>
                <h5 className="text-muted">Favorites</h5>
                <h2 className="text-danger">{dashboard?.total_favorites || 0}</h2>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3} className="mb-3">
            <Card className="text-center border-warning">
              <Card.Body>
                <h5 className="text-muted">Avg Rating</h5>
                <h2 className="text-warning">{dashboard?.average_rating || 0}</h2>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3} className="mb-3">
            <Card className="text-center border-info">
              <Card.Body>
                <h5 className="text-muted">Reviews</h5>
                <h2 className="text-info">{dashboard?.total_reviews || 0}</h2>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Recent Reviews */}
        {dashboard?.recent_reviews && dashboard.recent_reviews.length > 0 && (
          <Card className="mb-4">
            <Card.Header>
              <Card.Title className="mb-0">
                <FaComments className="me-2" />
                Recent Reviews
              </Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="table-responsive">
                <Table hover>
                  <thead>
                    <tr>
                      <th>Rating</th>
                      <th>Review</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.recent_reviews.map((review) => (
                      <tr key={review.id}>
                        <td>
                          <div className="rating">
                            {Array(5)
                              .fill(0)
                              .map((_, i) => (
                                <FaStar
                                  key={i}
                                  className={i < review.rating ? "star-filled" : "star-empty"}
                                  size={14}
                                />
                              ))}
                          </div>
                        </td>
                        <td>{review.comment?.substring(0, 100)}...</td>
                        <td>{new Date(review.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            </Card.Body>
          </Card>
        )}

        {/* My Restaurants */}
        <Card>
          <Card.Header>
            <div className="d-flex justify-content-between align-items-center">
              <Card.Title className="mb-0">My Restaurants</Card.Title>
              <Link to="/restaurants/new" className="btn btn-success btn-sm">
                + Add Restaurant
              </Link>
            </div>
          </Card.Header>
          <Card.Body>
            {dashboard?.restaurants && dashboard.restaurants.length > 0 ? (
              <div className="table-responsive">
                <Table hover>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Cuisine</th>
                      <th>City</th>
                      <th>Rating</th>
                      <th>Reviews</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.restaurants.map((restaurant) => (
                      <tr key={restaurant.id}>
                        <td>
                          <strong>{restaurant.name}</strong>
                        </td>
                        <td>{restaurant.cuisine_type}</td>
                        <td>{restaurant.city}</td>
                        <td>
                          <div className="rating">
                            {Array(5)
                              .fill(0)
                              .map((_, i) => (
                                <FaStar
                                  key={i}
                                  className={i < Math.round(restaurant.average_rating) ? "star-filled" : "star-empty"}
                                  size={14}
                                />
                              ))}
                          </div>
                          <span className="ms-2 text-muted">{restaurant.average_rating.toFixed(1)}</span>
                        </td>
                        <td>
                          <Badge bg="info">{restaurant.review_count}</Badge>
                        </td>
                        <td>
                          <Link
                            to={`/restaurants/${restaurant.id}/edit`}
                            className="btn btn-sm btn-outline-primary me-2"
                            title="Edit"
                          >
                            <FaEdit />
                          </Link>
                          <Button
                            variant="outline-danger"
                            size="sm"
                            onClick={() => handleDeleteRestaurant(restaurant.id)}
                            disabled={deletingId === restaurant.id}
                            title="Delete"
                          >
                            <FaTrash />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            ) : (
              <Alert variant="info">
                No restaurants yet.{" "}
                <Link to="/restaurants/new">Create your first restaurant listing</Link>
              </Alert>
            )}
          </Card.Body>
        </Card>
      </Container>
    </Container>
  );
}

export default OwnerDashboard;
