import React, { useEffect, useState } from "react";
import {
  Container,
  Card,
  Form,
  Button,
  Alert,
  Spinner,
  Row,
  Col,
  Badge,
} from "react-bootstrap";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import StarRatings from "react-star-ratings";

import {
  fetchRestaurantDetails,
  selectRestaurantDetailsLoading,
  selectRestaurantsError,
  selectSelectedRestaurant,
} from "../../redux/slices/restaurantsSlice";

import {
  createReview,
  deleteReview,
  fetchRestaurantReviews,
  selectRestaurantReviews,
  selectReviewsDeletingById,
  selectReviewsError,
  selectReviewsSubmitting,
  updateReview,
} from "../../redux/slices/reviewsSlice";

import { selectUserId } from "../../redux/slices/authSlice";
import { formatDisplayError } from "../../utils/apiError";

import "./RestaurantForms.css";

function WriteReviewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const userId = useSelector(selectUserId);
  const restaurant = useSelector(selectSelectedRestaurant);
  const loadingRestaurant = useSelector(selectRestaurantDetailsLoading);
  const restaurantError = useSelector(selectRestaurantsError);

  const reviews = useSelector(selectRestaurantReviews(id));
  const reviewsError = useSelector(selectReviewsError);
  const submitting = useSelector(selectReviewsSubmitting);
  const deletingById = useSelector(selectReviewsDeletingById);

  const existingReview = reviews.find((review) => {
    return Number(review.user_id) === Number(userId);
  });

  const existingReviewId = existingReview?.id || null;
  const isEditMode = Boolean(existingReviewId);
  const deleting = Boolean(existingReviewId && deletingById[existingReviewId]);

  const [reviewData, setReviewData] = useState({
    rating: 5,
    comment: "",
  });

  const [localError, setLocalError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    dispatch(fetchRestaurantDetails(id));
    dispatch(fetchRestaurantReviews(id));
  }, [dispatch, id]);

  useEffect(() => {
    if (existingReview) {
      setReviewData({
        rating: Number(existingReview.rating) || 5,
        comment: existingReview.comment || "",
      });
    } else {
      setReviewData({
        rating: 5,
        comment: "",
      });
    }
  }, [existingReview]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setLocalError("");
    setSuccess("");

    if (!userId) {
      setLocalError("You must be logged in to write a review.");
      return;
    }

    if (!reviewData.comment.trim()) {
      setLocalError("Please enter a review comment.");
      return;
    }

    const payload = {
      rating: Number(reviewData.rating),
      comment: reviewData.comment.trim(),
    };

    try {
      if (isEditMode) {
        await dispatch(
          updateReview({
            restaurantId: id,
            reviewId: existingReviewId,
            data: payload,
          })
        ).unwrap();

        setSuccess("Review updated successfully.");
      } else {
        await dispatch(
          createReview({
            restaurantId: id,
            userId,
            data: payload,
          })
        ).unwrap();

        setSuccess("Review submitted successfully.");
      }

      navigate(`/restaurants/${id}`);
    } catch {
      // Error is stored in Redux reviews.error.
    }
  };

  const handleDelete = async () => {
    if (!existingReviewId) return;

    if (!window.confirm("Are you sure you want to delete your review?")) {
      return;
    }

    try {
      await dispatch(
        deleteReview({
          restaurantId: id,
          reviewId: existingReviewId,
        })
      ).unwrap();

      navigate(`/restaurants/${id}`);
    } catch {
      // Error is stored in Redux reviews.error.
    }
  };

  if (loadingRestaurant) {
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
          <Alert variant="danger">Restaurant not found.</Alert>
        )}

        <Link to="/" className="btn btn-outline-danger">
          Back to Restaurants
        </Link>
      </Container>
    );
  }

  const safeAverageRating = Number(restaurant?.average_rating) || 0;
  const safeReviewCount = Number(restaurant?.review_count) || 0;
  const displayError = localError || reviewsError || restaurantError;

  return (
    <div className="restaurant-form-page">
      <Container className="py-4">
        <Row className="justify-content-center">
          <Col lg={9} xl={8}>
            <Card className="restaurant-form-card">
              <Card.Body>
                <div className="form-page-header">
                  <h1>{isEditMode ? "Edit Your Review" : "Write a Review"}</h1>

                  <p className="text-muted">
                    {isEditMode
                      ? "Update your experience for this restaurant."
                      : "Share your experience and help others discover great restaurants."}
                  </p>
                </div>

                <Card className="review-restaurant-summary mb-4">
                  <Card.Body>
                    <div className="summary-header">
                      <div>
                        <h4>{restaurant.name}</h4>

                        <p className="text-muted mb-2">
                          {restaurant.cuisine_type ||
                            restaurant.cuisine ||
                            "Restaurant"}
                        </p>
                      </div>

                      <Badge bg="danger" className="summary-rating-badge">
                        {safeAverageRating.toFixed(1)}
                      </Badge>
                    </div>

                    <div className="summary-stars">
                      <StarRatings
                        rating={safeAverageRating}
                        starDimension="18px"
                        starSpacing="2px"
                        starEmptyColor="#ddd"
                        starRatedColor="#d32323"
                        isSelectable={false}
                      />

                      <span>
                        {safeReviewCount} review
                        {safeReviewCount !== 1 ? "s" : ""}
                      </span>
                    </div>
                  </Card.Body>
                </Card>

                {displayError && (
                  <Alert variant="danger">
                    {formatDisplayError(displayError)}
                  </Alert>
                )}

                {success && <Alert variant="success">{success}</Alert>}

                <Form onSubmit={handleSubmit}>
                  <Form.Group className="mb-4">
                    <Form.Label>Your Rating</Form.Label>

                    <div className="review-rating-input">
                      <StarRatings
                        rating={reviewData.rating}
                        starDimension="34px"
                        starSpacing="4px"
                        starEmptyColor="#ddd"
                        starRatedColor="#d32323"
                        changeRating={(value) => {
                          setReviewData((prev) => ({
                            ...prev,
                            rating: value,
                          }));
                        }}
                      />
                    </div>
                  </Form.Group>

                  <Form.Group className="mb-4">
                    <Form.Label>Your Review</Form.Label>

                    <Form.Control
                      as="textarea"
                      rows={6}
                      placeholder="Describe your experience..."
                      value={reviewData.comment}
                      onChange={(e) => {
                        setReviewData((prev) => ({
                          ...prev,
                          comment: e.target.value,
                        }));
                      }}
                    />
                  </Form.Group>

                  <div className="form-actions d-flex gap-2 flex-wrap">
                    <Link
                      to={`/restaurants/${id}`}
                      className="btn btn-outline-secondary"
                    >
                      Cancel
                    </Link>

                    {isEditMode && (
                      <Button
                        type="button"
                        variant="outline-danger"
                        onClick={handleDelete}
                        disabled={deleting || submitting}
                      >
                        {deleting ? "Deleting..." : "Delete Review"}
                      </Button>
                    )}

                    <Button
                      type="submit"
                      variant="danger"
                      disabled={submitting || deleting}
                    >
                      {submitting ? (
                        <>
                          <Spinner animation="border" size="sm" className="me-2" />
                          {isEditMode ? "Updating..." : "Submitting..."}
                        </>
                      ) : isEditMode ? (
                        "Update Review"
                      ) : (
                        "Submit Review"
                      )}
                    </Button>
                  </div>
                </Form>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default WriteReviewPage;