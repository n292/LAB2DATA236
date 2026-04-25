import React, { useState } from 'react';
import { Card, Button, Alert, Modal, Form } from 'react-bootstrap';
import { FaStar, FaEdit, FaTrash } from 'react-icons/fa';
import { reviewsAPI } from '../../services/api';
import './Review.css';

function ReviewCard({ review, onDeleted }) {
  const [isEditing, setIsEditing] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editRating, setEditRating] = useState(review.rating);
  const [editComment, setEditComment] = useState(review.comment || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [hoveredRating, setHoveredRating] = useState(0);

  const userId = localStorage.getItem('user_id');
  const isOwnReview = review.author && review.author.id == userId;

  const handleEditClick = () => {
    setEditRating(review.rating);
    setEditComment(review.comment || '');
    setShowEditModal(true);
  };

  const handleSaveEdit = async () => {
    setLoading(true);
    setError('');

    try {
      await reviewsAPI.update(review.id, {
        rating: editRating,
        comment: editComment || null,
      });
      setShowEditModal(false);
      setIsEditing(false);
      if (onDeleted) {
        onDeleted();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update review');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this review?')) {
      setLoading(true);
      setError('');

      try {
        await reviewsAPI.delete(review.id);
        if (onDeleted) {
          onDeleted();
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to delete review');
      } finally {
        setLoading(false);
      }
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <>
      <Card className="review-card mb-3">
        <Card.Body>
          {error && <Alert variant="danger" className="mb-3">{error}</Alert>}

          <div className="review-header">
            <div>
              <p className="reviewer-name">
                {review.author?.name || 'Anonymous'}
              </p>
              <div className="review-rating">
                {[...Array(5)].map((_, i) => (
                  <FaStar
                    key={i}
                    size={16}
                    className={i < review.rating ? 'star active' : 'star inactive'}
                  />
                ))}
              </div>
              <p className="review-date">{formatDate(review.created_at)}</p>
            </div>

            {isOwnReview && (
              <div className="review-actions">
                <Button
                  variant="light"
                  size="sm"
                  onClick={handleEditClick}
                  disabled={loading}
                  title="Edit review"
                >
                  <FaEdit />
                </Button>
                <Button
                  variant="light"
                  size="sm"
                  onClick={handleDelete}
                  disabled={loading}
                  title="Delete review"
                >
                  <FaTrash />
                </Button>
              </div>
            )}
          </div>

          {review.comment && (
            <p className="review-comment mt-3">{review.comment}</p>
          )}
        </Card.Body>
      </Card>

      {/* Edit Modal */}
      <Modal show={showEditModal} onHide={() => setShowEditModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Review</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger">{error}</Alert>}

          <Form.Group className="mb-4">
            <Form.Label>Rating</Form.Label>
            <div className="rating-input">
              {[1, 2, 3, 4, 5].map((star) => (
                <FaStar
                  key={star}
                  size={30}
                  className={`star ${
                    star <= (hoveredRating || editRating) ? 'active' : 'inactive'
                  }`}
                  onClick={() => setEditRating(star)}
                  onMouseEnter={() => setHoveredRating(star)}
                  onMouseLeave={() => setHoveredRating(0)}
                />
              ))}
            </div>
          </Form.Group>

          <Form.Group className="mb-4">
            <Form.Label>Comment</Form.Label>
            <Form.Control
              as="textarea"
              rows={4}
              value={editComment}
              onChange={(e) => setEditComment(e.target.value)}
              maxLength={1000}
            />
            <small className="text-muted">
              {editComment.length}/1000 characters
            </small>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="secondary"
            onClick={() => setShowEditModal(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleSaveEdit}
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}

export default ReviewCard;
