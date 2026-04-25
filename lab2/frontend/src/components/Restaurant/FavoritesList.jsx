import React, { useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Card,
  Button,
  Alert,
  Spinner,
  Badge,
} from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  FaMapMarkerAlt,
  FaUtensils,
  FaStar,
  FaTrash,
  FaPhone,
} from "react-icons/fa";

import {
  fetchFavorites,
  removeFavorite,
  selectFavoriteActionLoadingByRestaurantId,
  selectFavorites,
  selectFavoritesError,
  selectFavoritesLoading,
} from "../../redux/slices/favoritesSlice";

import { selectUserId } from "../../redux/slices/authSlice";
import { formatDisplayError } from "../../utils/apiError";

import "./Restaurant.css";

const fallbackRestaurantImages = [
  "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?auto=format&fit=crop&w=1200&q=80",
];

function getRandomImage(resId) {
  return fallbackRestaurantImages[
    Number(resId || 0) % fallbackRestaurantImages.length
  ];
}

function getRestaurantFromFavorite(favorite) {
  return (
    favorite?.restaurant || {
      id: favorite?.restaurant_id,
      name: favorite?.restaurant_name || "Restaurant",
      cuisine_type: favorite?.cuisine_type || favorite?.cuisine || "Restaurant",
      city: favorite?.city || "",
      state: favorite?.state || "USA",
      phone: favorite?.phone || "",
      average_rating: Number(favorite?.average_rating) || 0,
      review_count: Number(favorite?.review_count) || 0,
      pricing_tier: favorite?.pricing_tier || "",
      photo_data: favorite?.photo_data || null,
    }
  );
}

function FavoritesList() {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const userId = useSelector(selectUserId);
  const favorites = useSelector(selectFavorites);
  const loading = useSelector(selectFavoritesLoading);
  const error = useSelector(selectFavoritesError);
  const actionLoadingByRestaurantId = useSelector(
    selectFavoriteActionLoadingByRestaurantId
  );

  useEffect(() => {
    if (!userId) {
      navigate("/login");
      return;
    }

    dispatch(fetchFavorites(userId));
  }, [dispatch, userId, navigate]);

  const handleRemoveFavorite = async (favoriteId, restaurantId) => {
    await dispatch(
      removeFavorite({
        favoriteId,
        restaurantId,
      })
    );

    if (userId) {
      dispatch(fetchFavorites(userId));
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

  return (
    <Container className="py-5">
      <h1 className="mb-4">My Favorite Restaurants</h1>

      {error && <Alert variant="danger">{formatDisplayError(error)}</Alert>}

      {favorites.length === 0 ? (
        <Alert variant="info">
          No favorite restaurants yet. <Link to="/">Start exploring</Link> to add
          some.
        </Alert>
      ) : (
        <Row>
          {favorites.map((favorite) => {
            const restaurant = getRestaurantFromFavorite(favorite);
            const restaurantId = restaurant?.id || favorite?.restaurant_id;
            const safeAverageRating = Number(restaurant?.average_rating) || 0;
            const safeReviewCount = Number(restaurant?.review_count) || 0;
            const removing = Boolean(actionLoadingByRestaurantId[restaurantId]);

            return (
              <Col key={favorite.id} md={6} lg={4} className="mb-4">
                <Card className="h-100 restaurant-card">
                  <div className="restaurant-image-container">
                    <Card.Img
                      variant="top"
                      src={restaurant?.photo_data || getRandomImage(restaurantId)}
                      alt={restaurant?.name || "Restaurant"}
                      className="restaurant-image"
                      onError={(e) => {
                        e.currentTarget.src = fallbackRestaurantImages[0];
                      }}
                    />

                    <Badge bg="danger" className="favorite-badge">
                      <FaStar className="me-1" />
                      Favorite
                    </Badge>
                  </div>

                  <Card.Body className="d-flex flex-column">
                    <Card.Title className="mb-2">
                      {restaurant?.name || "Restaurant"}
                    </Card.Title>

                    <div className="mb-2 text-muted">
                      <FaUtensils className="me-2" />
                      {restaurant?.cuisine_type ||
                        restaurant?.cuisine ||
                        "Restaurant"}
                    </div>

                    <div className="mb-2 text-muted">
                      <FaMapMarkerAlt className="me-2" />
                      {[restaurant?.city, restaurant?.state || "USA"]
                        .filter(Boolean)
                        .join(", ")}
                    </div>

                    {restaurant?.phone && (
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
                              className={
                                i < Math.round(safeAverageRating)
                                  ? "star-filled"
                                  : "star-empty"
                              }
                            />
                          ))}

                        <span className="ms-2 text-muted">
                          {safeAverageRating.toFixed(1)} ({safeReviewCount}{" "}
                          reviews)
                        </span>
                      </div>

                      {restaurant?.pricing_tier && (
                        <Badge bg="info">{restaurant.pricing_tier}</Badge>
                      )}
                    </div>

                    <div className="mt-auto">
                      <Link
                        to={`/restaurants/${restaurantId}`}
                        className="btn btn-primary btn-sm me-2 mb-2"
                      >
                        View Details
                      </Link>

                      <Button
                        variant="outline-danger"
                        size="sm"
                        onClick={() =>
                          handleRemoveFavorite(favorite.id, restaurantId)
                        }
                        disabled={removing}
                        className="mb-2"
                      >
                        <FaTrash className="me-1" />
                        {removing ? "Removing..." : "Remove"}
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