import React, { useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Card,
  Spinner,
  Button,
  Alert,
  Badge,
} from "react-bootstrap";
import { useParams, Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import StarRatings from "react-star-ratings";
import {
  FaHeart,
  FaRegHeart,
  FaMapMarkerAlt,
  FaPhone,
  FaClock,
  FaUtensils,
  FaArrowLeft,
  FaEdit,
  FaTrash,
} from "react-icons/fa";

import {
  fetchRestaurantDetails,
  selectRestaurantDetailsLoading,
  selectRestaurantsError,
  selectSelectedRestaurant,
} from "../../redux/slices/restaurantsSlice";

import {
  deleteReview,
  fetchRestaurantReviews,
  selectRestaurantReviews,
  selectReviewsDeletingById,
  selectReviewsError,
  selectReviewsLoadingByRestaurantId,
} from "../../redux/slices/reviewsSlice";

import {
  addFavorite,
  removeFavorite,
  selectFavoriteActionLoadingByRestaurantId,
} from "../../redux/slices/favoritesSlice";

import { selectUserId } from "../../redux/slices/authSlice";
import { formatDisplayError } from "../../utils/apiError";

import "./Restaurant.css";

const fallbackRestaurantImages = [
  "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1600&q=80",
  "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1600&q=80",
  "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1600&q=80",
  "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1600&q=80",
];

function safeText(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return fallback;
}

function formatHours(hours) {
  if (!hours) return "";
  if (typeof hours === "string") return hours;
  if (Array.isArray(hours)) return hours.join(", ");

  if (typeof hours === "object") {
    return Object.entries(hours)
      .map(([day, value]) => {
        return `${day}: ${
          typeof value === "string" ? value : JSON.stringify(value)
        }`;
      })
      .join(" | ");
  }

  return "";
}

function getAmenitiesList(amenities) {
  if (!amenities) return [];

  if (Array.isArray(amenities)) {
    return amenities.map((item) => String(item).trim()).filter(Boolean);
  }

  return String(amenities)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function RestaurantDetails() {
  const { id } = useParams();
  const dispatch = useDispatch();

  const userId = useSelector(selectUserId);

  const restaurant = useSelector(selectSelectedRestaurant);
  const detailsLoading = useSelector(selectRestaurantDetailsLoading);
  const restaurantError = useSelector(selectRestaurantsError);

  const reviews = useSelector(selectRestaurantReviews(id));
  const reviewsLoadingByRestaurantId = useSelector(
    selectReviewsLoadingByRestaurantId
  );
  const reviewsError = useSelector(selectReviewsError);
  const deletingById = useSelector(selectReviewsDeletingById);

  const favoriteActionLoadingByRestaurantId = useSelector(
    selectFavoriteActionLoadingByRestaurantId
  );

  useEffect(() => {
    dispatch(fetchRestaurantDetails(id));
    dispatch(fetchRestaurantReviews(id));
  }, [dispatch, id]);

  const toggleFavorite = async () => {
    if (!userId) {
      alert("Please log in to add favorites");
      return;
    }

    if (restaurant?.isFavorite) {
      await dispatch(
        removeFavorite({
          favoriteId: restaurant.favoriteId,
          restaurantId: id,
        })
      );
    } else {
      await dispatch(
        addFavorite({
          restaurantId: id,
          userId,
        })
      );
    }

    dispatch(fetchRestaurantDetails(id));
  };

  const handleDeleteReview = async (reviewId) => {
    if (!window.confirm("Are you sure you want to delete your review?")) {
      return;
    }

    await dispatch(
      deleteReview({
        restaurantId: id,
        reviewId,
      })
    );

    dispatch(fetchRestaurantDetails(id));
    dispatch(fetchRestaurantReviews(id));
  };

  if (detailsLoading) {
    return (
      <Container className="text-center py-5">
        <Spinner animation="border" variant="danger" />
      </Container>
    );
  }

  if (!restaurant) {
    return (
      <Container className="py-5">
        {restaurantError ? (
          <Alert variant="danger">{formatDisplayError(restaurantError)}</Alert>
        ) : (
          <Alert variant="danger">Restaurant not found</Alert>
        )}

        <Link to="/" className="btn btn-danger">
          Back to Search
        </Link>
      </Container>
    );
  }

  const safeAverageRating = Number(restaurant?.average_rating) || 0;
  const safeReviewCount = Number(restaurant?.review_count) || 0;
  const amenitiesList = getAmenitiesList(restaurant?.amenities);

  const currentUserReview = reviews.find((review) => {
    return Number(review.user_id) === Number(userId);
  });

  const favoriteLoading = Boolean(favoriteActionLoadingByRestaurantId[id]);
  const reviewsLoading = Boolean(reviewsLoadingByRestaurantId[id]);

  return (
    <div className="restaurant-details-page">
      <section className="detail-hero">
        <img
          src={
            restaurant.image_url ||
            restaurant.photo_data ||
            fallbackRestaurantImages[Number(id) % fallbackRestaurantImages.length]
          }
          alt={safeText(restaurant.name, "Restaurant")}
          className="detail-hero-image"
          onError={(e) => {
            e.currentTarget.src = fallbackRestaurantImages[0];
          }}
        />

        <div className="detail-hero-overlay" />

        <Container className="detail-hero-content">
          <Link to="/" className="back-link">
            <FaArrowLeft /> Back to Search
          </Link>

          <div className="detail-title-block">
            <h1>{safeText(restaurant.name, "Restaurant")}</h1>

            <div className="detail-subtitle">
              <span className="detail-cuisine">
                <FaUtensils />{" "}
                {safeText(
                  restaurant.cuisine_type || restaurant.cuisine,
                  "Restaurant"
                )}
              </span>
            </div>

            <div className="detail-rating-row">
              <StarRatings
                rating={safeAverageRating}
                starDimension="22px"
                starSpacing="2px"
                starEmptyColor="#ddd"
                starRatedColor="#d32323"
                isSelectable={false}
              />

              <Badge bg="danger" className="detail-rating-badge">
                {safeAverageRating.toFixed(1)}
              </Badge>

              <span className="detail-review-count">
                {safeReviewCount} review{safeReviewCount !== 1 ? "s" : ""}
              </span>
            </div>
          </div>
        </Container>
      </section>

      <Container className="py-4">
        {restaurantError && (
          <Alert variant="danger">{formatDisplayError(restaurantError)}</Alert>
        )}

        {reviewsError && (
          <Alert variant="danger">{formatDisplayError(reviewsError)}</Alert>
        )}

        <Row className="g-4">
          <Col lg={8}>
            <Card className="detail-main-card mb-4">
              <Card.Body>
                <h4 className="section-title">About</h4>

                <div className="restaurant-info-detail">
                  <p>
                    <FaMapMarkerAlt />

                    <span>
                      {[
                        safeText(restaurant.address),
                        safeText(restaurant.city),
                        safeText(restaurant.zip_code),
                      ]
                        .filter(Boolean)
                        .join(", ") || "Address unavailable"}
                    </span>
                  </p>

                  {restaurant.phone && (
                    <p>
                      <FaPhone />
                      <span>{safeText(restaurant.phone)}</span>
                    </p>
                  )}

                  {restaurant.hours_of_operation && (
                    <p>
                      <FaClock />
                      <span>{formatHours(restaurant.hours_of_operation)}</span>
                    </p>
                  )}

                  {restaurant.pricing_tier && (
                    <p>
                      <strong>Price Range:</strong>
                      <span className="ms-1">
                        {safeText(restaurant.pricing_tier)}
                      </span>
                    </p>
                  )}
                </div>

                {restaurant.description && (
                  <div className="description-box">
                    <p>{safeText(restaurant.description)}</p>
                  </div>
                )}

                {amenitiesList.length > 0 && (
                  <div className="amenities-box">
                    <h5 className="amenities-title">Amenities</h5>

                    <div className="amenities-list">
                      {amenitiesList.map((amenity, idx) => (
                        <span key={idx} className="amenity-chip">
                          {amenity}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </Card.Body>
            </Card>

            <Card className="detail-main-card">
              <Card.Body>
                <div className="reviews-header">
                  <h4 className="section-title mb-0">Customer Reviews</h4>

                  <span className="reviews-header-count">
                    {reviews.length} review{reviews.length !== 1 ? "s" : ""}
                  </span>
                </div>

                {reviewsLoading ? (
                  <div className="text-center py-4">
                    <Spinner animation="border" variant="danger" />
                  </div>
                ) : reviews.length === 0 ? (
                  <div className="empty-review-state">
                    <p>No reviews yet. Be the first to review this restaurant.</p>
                  </div>
                ) : (
                  reviews.map((review) => {
                    const isOwnReview = Number(review.user_id) === Number(userId);
                    const deleteLoading = Boolean(deletingById[review.id]);

                    return (
                      <Card key={review.id} className="review-card mb-3">
                        <Card.Body>
                          <div className="review-header">
                            <div>
                              <strong>
                                {safeText(
                                  review.author?.name ||
                                    review.user_name ||
                                    review.name,
                                  "Anonymous"
                                )}
                              </strong>

                              <div className="review-rating">
                                <StarRatings
                                  rating={Number(review.rating) || 0}
                                  starDimension="16px"
                                  starSpacing="1px"
                                  starEmptyColor="#ddd"
                                  starRatedColor="#d32323"
                                  isSelectable={false}
                                />
                              </div>
                            </div>

                            <div className="d-flex align-items-center gap-2 flex-wrap justify-content-end">
                              <small className="text-muted">
                                {review.created_at
                                  ? new Date(review.created_at).toLocaleDateString()
                                  : ""}
                              </small>

                              {isOwnReview && (
                                <>
                                  <Button
                                    as={Link}
                                    to={`/restaurants/${id}/review`}
                                    variant="outline-secondary"
                                    size="sm"
                                  >
                                    <FaEdit className="me-1" />
                                    Edit
                                  </Button>

                                  <Button
                                    variant="outline-danger"
                                    size="sm"
                                    disabled={deleteLoading}
                                    onClick={() => handleDeleteReview(review.id)}
                                  >
                                    <FaTrash className="me-1" />
                                    {deleteLoading ? "Deleting..." : "Delete"}
                                  </Button>
                                </>
                              )}
                            </div>
                          </div>

                          {review.comment && (
                            <p className="review-comment">
                              {safeText(review.comment)}
                            </p>
                          )}
                        </Card.Body>
                      </Card>
                    );
                  })
                )}
              </Card.Body>
            </Card>
          </Col>

          <Col lg={4}>
            <Card className="action-card mb-3">
              <Card.Body>
                <Button
                  variant={restaurant.isFavorite ? "danger" : "outline-danger"}
                  className="w-100 mb-2"
                  onClick={toggleFavorite}
                  disabled={favoriteLoading}
                >
                  {restaurant.isFavorite ? (
                    <>
                      <FaHeart />{" "}
                      {favoriteLoading ? "Updating..." : "Remove from Favorites"}
                    </>
                  ) : (
                    <>
                      <FaRegHeart />{" "}
                      {favoriteLoading ? "Updating..." : "Add to Favorites"}
                    </>
                  )}
                </Button>

                <Button
                  as={Link}
                  to={`/restaurants/${id}/review`}
                  variant="danger"
                  className="w-100 mb-2"
                >
                  {currentUserReview ? "Edit Your Review" : "Write a Review"}
                </Button>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default RestaurantDetails;