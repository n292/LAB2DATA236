from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from models import Review, Restaurant, User
from schemas import ReviewCreate, ReviewUpdate, ReviewResponse
from database import get_db
from utils.security import decode_token

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


def get_current_user_from_header(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


def recalculate_restaurant_stats(db: Session, restaurant_id: int):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        return

    stats = db.query(
        func.count(Review.id).label("review_count"),
        func.avg(Review.rating).label("average_rating")
    ).filter(Review.restaurant_id == restaurant_id).first()

    restaurant.review_count = int(stats.review_count or 0)
    restaurant.average_rating = float(stats.average_rating or 0.0)


@router.get("/restaurant/{restaurant_id}", response_model=list[ReviewResponse])
def get_restaurant_reviews(
    restaurant_id: int,
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    reviews = (
        db.query(Review)
        .options(selectinload(Review.author))
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return reviews


@router.get("/user/{user_id}", response_model=list[ReviewResponse])
def get_user_reviews(
    user_id: int,
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    reviews = (
        db.query(Review)
        .options(selectinload(Review.author))
        .filter(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return reviews


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    review = (
        db.query(Review)
        .options(selectinload(Review.author))
        .filter(Review.id == review_id)
        .first()
    )

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    return review


@router.post("/restaurant/{restaurant_id}", response_model=ReviewResponse)
def create_review(
    restaurant_id: int,
    review_data: ReviewCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if review_data.rating < 1 or review_data.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )

    existing_review = db.query(Review).filter(
        Review.restaurant_id == restaurant_id,
        Review.user_id == current_user.id
    ).first()

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this restaurant"
        )

    new_review = Review(
        user_id=current_user.id,
        restaurant_id=restaurant_id,
        rating=review_data.rating,
        comment=review_data.comment.strip() if review_data.comment else None
    )

    db.add(new_review)
    db.flush()

    recalculate_restaurant_stats(db, restaurant_id)

    db.commit()
    db.refresh(new_review)

    return (
        db.query(Review)
        .options(selectinload(Review.author))
        .filter(Review.id == new_review.id)
        .first()
    )


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)

    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own review"
        )

    if review_data.rating is not None and (review_data.rating < 1 or review_data.rating > 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )

    update_data = (
        review_data.model_dump(exclude_unset=True)
        if hasattr(review_data, "model_dump")
        else review_data.dict(exclude_unset=True)
    )

    if "comment" in update_data:
        update_data["comment"] = update_data["comment"].strip() if update_data["comment"] else None

    for field, value in update_data.items():
        setattr(review, field, value)

    db.flush()

    recalculate_restaurant_stats(db, review.restaurant_id)

    db.commit()
    db.refresh(review)

    return (
        db.query(Review)
        .options(selectinload(Review.author))
        .filter(Review.id == review.id)
        .first()
    )


@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)

    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own review"
        )

    restaurant_id = review.restaurant_id

    db.delete(review)
    db.flush()

    recalculate_restaurant_stats(db, restaurant_id)

    db.commit()

    return {"message": "Review deleted successfully"}