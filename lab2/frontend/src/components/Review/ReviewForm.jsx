import React, { useState } from 'react';
import { Form, Button, Alert, Container } from 'react-bootstrap';
import { FaStar } from 'react-icons/fa';
import { reviewsAPI } from '../../services/api';
import './Review.css';

function ReviewForm({ restaurantId, userId, onSuccess }) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [hoveredRating, setHoveredRating] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    if (rating === 0) {
      setError('Please select a rating');
      setLoading(false);
      return;
    }

    try {
      const reviewData = {
        rating: rating,
        comment: comment || null,
      };

      await reviewsAPI.create(restaurantId, userId, reviewData);
      setSuccess('Review submitted successfully!');
      setRating(0);
      setComment('');

      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit review');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container className="review-form-container">
      <h3 className="mb-4">Write a Review</h3>

      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <Form onSubmit={handleSubmit}>
        {/* Rating */}
        <Form.Group className="mb-4">
          <Form.Label>Rating</Form.Label>
          <div className="rating-input">
            {[1, 2, 3, 4, 5].map((star) => (
              <FaStar
                key={star}
                size={30}
                className={`star ${
                  star <= (hoveredRating || rating) ? 'active' : 'inactive'
                }`}
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoveredRating(star)}
                onMouseLeave={() => setHoveredRating(0)}
              />
            ))}
          </div>
          <p className="text-muted mt-2">
            {rating > 0 ? `${rating} star${rating > 1 ? 's' : ''}` : 'Click to rate'}
          </p>
        </Form.Group>

        {/* Comment */}
        <Form.Group className="mb-4">
          <Form.Label>Your Review (Optional)</Form.Label>
          <Form.Control
            as="textarea"
            rows={5}
            placeholder="Share your experience at this restaurant..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            maxLength={1000}
          />
          <small className="text-muted">
            {comment.length}/1000 characters
          </small>
        </Form.Group>

        {/* Submit Button */}
        <Button
          variant="danger"
          type="submit"
          disabled={loading}
          className="w-100"
        >
          {loading ? 'Submitting...' : 'Submit Review'}
        </Button>
      </Form>
    </Container>
  );
}

export default ReviewForm;
