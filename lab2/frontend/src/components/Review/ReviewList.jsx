import React, { useState, useEffect } from 'react';
import { Container, Spinner, Alert } from 'react-bootstrap';
import { reviewsAPI } from '../../services/api';
import ReviewCard from './ReviewCard';
import './Review.css';

function ReviewList({ restaurantId, onReviewDeleted }) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const LIMIT = 5;

  useEffect(() => {
    fetchReviews();
  }, [restaurantId]);

  const fetchReviews = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await reviewsAPI.getByRestaurant(restaurantId, {
        skip: skip,
        limit: LIMIT,
      });
      setReviews(response.data);
      setHasMore(response.data.length === LIMIT);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load reviews');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = async () => {
    try {
      const response = await reviewsAPI.getByRestaurant(restaurantId, {
        skip: skip + LIMIT,
        limit: LIMIT,
      });
      setReviews([...reviews, ...response.data]);
      setSkip(skip + LIMIT);
      setHasMore(response.data.length === LIMIT);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load more reviews');
    }
  };

  const handleReviewDeleted = () => {
    if (onReviewDeleted) {
      onReviewDeleted();
    }
    fetchReviews();
  };

  if (loading && reviews.length === 0) {
    return (
      <Container className="review-list-container">
        <div className="text-center">
          <Spinner animation="border" variant="danger" />
        </div>
      </Container>
    );
  }

  return (
    <Container className="review-list-container">
      <h3 className="mb-4">Customer Reviews</h3>

      {error && <Alert variant="danger">{error}</Alert>}

      {reviews.length === 0 ? (
        <Alert variant="info">No reviews yet. Be the first to review!</Alert>
      ) : (
        <>
          <div className="reviews-list">
            {reviews.map((review) => (
              <ReviewCard
                key={review.id}
                review={review}
                onDeleted={handleReviewDeleted}
              />
            ))}
          </div>

          {hasMore && (
            <button className="btn btn-outline-danger w-100 mt-3" onClick={handleLoadMore}>
              Load More Reviews
            </button>
          )}
        </>
      )}
    </Container>
  );
}

export default ReviewList;
