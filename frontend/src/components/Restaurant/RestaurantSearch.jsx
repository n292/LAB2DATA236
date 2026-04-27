import React, { useEffect, useState } from "react";
import { Container, Row, Col, Card, Form, Button, Alert, Spinner, Badge } from "react-bootstrap";
import { Link } from "react-router-dom";
import { useSelector, useDispatch } from 'react-redux';
import { setRestaurants, setLoading, setError, updateFilters } from '../../redux/slices/restaurantSlice';
import {
  FaMapMarkerAlt,
  FaUtensils,
  FaStar,
  FaRegStar,
  FaPhoneAlt,
  FaCheckCircle,
} from "react-icons/fa";
import "./Restaurant.css";

import { restaurantsAPI, favoritesAPI } from "../../services/api";

const fallbackRestaurantImages = [
  "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=80",
  "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?auto=format&fit=crop&w=1200&q=80",
];

const quickCuisineOptions = ["Italian", "Mexican", "Chinese", "Indian", "Japanese", "American"];

function getListFromValue(value) {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function toSearchableText(value) {
  if (!value) return "";
  if (Array.isArray(value)) return value.map((item) => String(item)).join(" ");
  if (typeof value === "object") return Object.values(value).map((item) => String(item)).join(" ");
  return String(value);
}

function matchesFilters(restaurant, filters) {
  const nameFilter = filters.name?.trim().toLowerCase() || "";
  const cuisineFilter = filters.cuisine?.trim().toLowerCase() || "";
  const cityFilter = filters.city?.trim().toLowerCase() || "";
  const keywordFilter = filters.keyword?.trim().toLowerCase() || "";

  if (nameFilter && !toSearchableText(restaurant.name).toLowerCase().includes(nameFilter)) return false;
  if (cuisineFilter && ![restaurant.cuisine_type, restaurant.cuisine].map(toSearchableText).join(" ").toLowerCase().includes(cuisineFilter)) return false;
  if (cityFilter && ![restaurant.city, restaurant.state].map(toSearchableText).join(" ").toLowerCase().includes(cityFilter)) return false;
  if (keywordFilter) {
    const searchableText = [
      restaurant.name, restaurant.cuisine_type, restaurant.cuisine,
      restaurant.city, restaurant.state, restaurant.description,
      restaurant.amenities, restaurant.keywords, restaurant.pricing_tier,
      restaurant.owner_name,
    ].map(toSearchableText).join(" ").toLowerCase();
    if (!searchableText.includes(keywordFilter)) return false;
  }
  return true;
}

function RestaurantSearch() {
  const dispatch = useDispatch();
  const { user, isLoggedIn } = useSelector((state) => state.auth);
  const { list: restaurants, loading, error, filters } = useSelector((state) => state.restaurants);
  
  const [favoritesLoading, setFavoritesLoading] = useState({});
  const [claimLoading, setClaimLoading] = useState({});
  const [unclaimLoading, setUnclaimLoading] = useState({});
  const [claimMessage, setClaimMessage] = useState("");

  const userId = user?.id;
  const userRole = user?.role;

  useEffect(() => {
    fetchRestaurants();
  }, []);

  const fetchRestaurants = async (customFilters = filters) => {
    dispatch(setLoading());
    setClaimMessage("");

    try {
      const params = {};
      if (customFilters.name?.trim()) params.name = customFilters.name.trim();
      if (customFilters.cuisine?.trim()) params.cuisine = customFilters.cuisine.trim();
      if (customFilters.city?.trim()) params.city = customFilters.city.trim();
      if (customFilters.keyword?.trim()) params.keywords = customFilters.keyword.trim();

      const response = await restaurantsAPI.search(params);
      const restaurantsData = Array.isArray(response?.data) ? response.data : [];

      const filteredRestaurantsData = restaurantsData.filter((restaurant) =>
        matchesFilters(restaurant, customFilters)
      );

      let enrichedRestaurants = filteredRestaurantsData.map((restaurant, index) => ({
        ...restaurant,
        owner_id: restaurant?.owner_id ?? null,
        owner_name: restaurant?.owner_name ?? null,
        isFavorite: false,
        favoriteId: null,
        average_rating: Number(restaurant?.average_rating || 0),
        review_count: Number(restaurant?.review_count || 0),
        image_url: restaurant?.photo_data || fallbackRestaurantImages[index % fallbackRestaurantImages.length],
        amenitiesList: getListFromValue(restaurant?.amenities),
        keywordsList: getListFromValue(restaurant?.keywords),
      }));

      if (userId) {
        try {
          const favoriteChecks = await Promise.all(
            enrichedRestaurants.map(async (restaurant) => {
              try {
                const favRes = await favoritesAPI.check(userId, restaurant.id);
                return {
                  restaurantId: restaurant.id,
                  isFavorite: !!favRes?.data?.is_favorite,
                  favoriteId: favRes?.data?.favorite_id || null,
                };
              } catch {
                return { restaurantId: restaurant.id, isFavorite: false, favoriteId: null };
              }
            })
          );

          enrichedRestaurants = enrichedRestaurants.map((restaurant) => {
            const match = favoriteChecks.find((fav) => fav.restaurantId === restaurant.id);
            return { ...restaurant, isFavorite: match ? match.isFavorite : false, favoriteId: match ? match.favoriteId : null };
          });
        } catch {}
      }

      dispatch(setRestaurants(enrichedRestaurants));
    } catch (err) {
      console.error("Search failed:", err);
      dispatch(setError("Failed to search restaurants"));
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    dispatch(updateFilters({ [name]: value }));
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchRestaurants(filters);
  };

  const handleQuickCuisine = (cuisine) => {
    dispatch(updateFilters({ cuisine }));
    fetchRestaurants({ ...filters, cuisine });
  };

  const clearFilters = () => {
    const reset = { name: "", cuisine: "", city: "", keyword: "" };
    dispatch(updateFilters(reset));
    fetchRestaurants(reset);
  };

  const toggleFavorite = async (restaurantId) => {
    if (!isLoggedIn) {
      alert("Please log in to add favorites");
      return;
    }

    setFavoritesLoading(prev => ({ ...prev, [restaurantId]: true }));

    try {
      const restaurant = restaurants.find(r => r.id === restaurantId);
      if (!restaurant) return;

      if (restaurant.isFavorite) {
        if (restaurant.favoriteId) await favoritesAPI.remove(restaurant.favoriteId);
        dispatch(setRestaurants(restaurants.map(r => r.id === restaurantId ? { ...r, isFavorite: false, favoriteId: null } : r)));
      } else {
        const response = await favoritesAPI.add(restaurantId, userId);
        dispatch(setRestaurants(restaurants.map(r => r.id === restaurantId ? { ...r, isFavorite: true, favoriteId: response?.data?.id || null } : r)));
      }
    } catch (err) {
      console.error("Favorite toggle failed:", err);
    } finally {
      setFavoritesLoading(prev => ({ ...prev, [restaurantId]: false }));
    }
  };

  const handleClaimRestaurant = async (restaurantId) => {
    if (userRole !== "owner") {
      alert("Only owner accounts can claim restaurants");
      return;
    }

    setClaimLoading(prev => ({ ...prev, [restaurantId]: true }));

    try {
      const response = await restaurantsAPI.claim(restaurantId);
      const claimed = response?.data?.restaurant;

      dispatch(setRestaurants(restaurants.map(r => r.id === restaurantId ? { 
        ...r, ...claimed, owner_id: userId, owner_name: claimed?.owner_name || r.owner_name 
      } : r)));

      setClaimMessage(response?.data?.message || "Restaurant claimed successfully");
    } catch (err) {
      dispatch(setError(err?.response?.data?.detail || "Failed to claim restaurant"));
    } finally {
      setClaimLoading(prev => ({ ...prev, [restaurantId]: false }));
    }
  };

  const handleUnclaimRestaurant = async (restaurantId) => {
    if (!window.confirm("Are you sure you want to unclaim?")) return;

    setUnclaimLoading(prev => ({ ...prev, [restaurantId]: true }));

    try {
      const response = await restaurantsAPI.unclaim(restaurantId);
      dispatch(setRestaurants(restaurants.map(r => r.id === restaurantId ? { ...r, owner_id: null, owner_name: null } : r)));
      setClaimMessage(response?.data?.message || "Restaurant unclaimed successfully");
    } catch (err) {
      dispatch(setError(err?.response?.data?.detail || "Failed to unclaim"));
    } finally {
      setUnclaimLoading(prev => ({ ...prev, [restaurantId]: false }));
    }
  };

  return (
    <div className="restaurant-search">
      <section className="search-header">
        <Container>
          <h1>Find the right spot</h1>
          <p>Search restaurants, cuisines, neighborhoods, and keywords.</p>
        </Container>
      </section>

      <Container>
        <section className="search-filters">
          <Card className="filter-card">
            <Card.Body>
              <Form onSubmit={handleSearch}>
                <Row className="g-3 align-items-end">
                  <Col lg={3} md={6}>
                    <Form.Group>
                      <Form.Label>Restaurant Name</Form.Label>
                      <Form.Control type="text" placeholder="Search by name" name="name" value={filters.name} onChange={handleChange} />
                    </Form.Group>
                  </Col>
                  <Col lg={3} md={6}>
                    <Form.Group>
                      <Form.Label>Cuisine</Form.Label>
                      <Form.Control type="text" placeholder="Italian, Indian, Sushi..." name="cuisine" value={filters.cuisine} onChange={handleChange} />
                    </Form.Group>
                  </Col>
                  <Col lg={2} md={6}>
                    <Form.Group>
                      <Form.Label>City</Form.Label>
                      <Form.Control type="text" placeholder="San Jose" name="city" value={filters.city} onChange={handleChange} />
                    </Form.Group>
                  </Col>
                  <Col lg={2} md={6}>
                    <Form.Group>
                      <Form.Label>Keywords</Form.Label>
                      <Form.Control type="text" placeholder="Outdoor seating..." name="keyword" value={filters.keyword} onChange={handleChange} />
                    </Form.Group>
                  </Col>
                  <Col lg={2} md={12} className="d-grid">
                    <Button variant="danger" type="submit">Search</Button>
                  </Col>
                </Row>

                <div className="quick-filters">
                  <div className="quick-filters-label">Popular:</div>
                  <div className="quick-filter-list">
                    {quickCuisineOptions.map((c) => (
                      <Button key={c} type="button" variant="light" className="quick-filter-btn" onClick={() => handleQuickCuisine(c)}>{c}</Button>
                    ))}
                    <Button type="button" variant="outline-secondary" className="quick-filter-btn" onClick={clearFilters}>Clear</Button>
                  </div>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </section>

        <section className="restaurant-results">
          {error && <Alert variant="danger" className="mt-3">{error}</Alert>}
          {claimMessage && <Alert variant="success" className="mt-3">{claimMessage}</Alert>}

          {loading ? (
            <div className="loading-state">
              <Spinner animation="border" />
              <p>Loading restaurants...</p>
            </div>
          ) : restaurants.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-card">
                <h4>No restaurants found</h4>
                <p>Try adjusting your search filters.</p>
              </div>
            </div>
          ) : (
            <>
              <div className="results-toolbar">
                <h3>Restaurants</h3>
                <span>{restaurants.length} result{restaurants.length !== 1 ? "s" : ""}</span>
              </div>
              <Row className="g-4">
                {restaurants.map((restaurant) => {
                  const isClaimed = restaurant.owner_id !== null && restaurant.owner_id !== undefined;
                  const isOwnedByCurrentUser = isClaimed && Number(restaurant.owner_id) === Number(userId);
                  const canClaimRestaurant = userRole === "owner" && !isClaimed;

                  return (
                    <Col key={restaurant.id} lg={4} md={6}>
                      <Card className="restaurant-card h-100">
                        <div className="restaurant-image">
                          <img src={restaurant.image_url} alt={restaurant.name} />
                        </div>
                        <Card.Body>
                          <div className="restaurant-header">
                            <div>
                              <h5>{restaurant.name}</h5>
                              <p className="cuisine-type"><FaUtensils /> {restaurant.cuisine_type || "Restaurant"}</p>
                            </div>
                            <button type="button" className="favorite-btn" onClick={() => toggleFavorite(restaurant.id)} disabled={favoritesLoading[restaurant.id]}>
                              {restaurant.isFavorite ? <FaStar className="active" /> : <FaRegStar />}
                            </button>
                          </div>
                          <div className="rating-section">
                            <Badge bg="danger" className="rating-badge">{(restaurant.average_rating || 0).toFixed(1)}</Badge>
                            <span className="review-count">{restaurant.review_count} review{restaurant.review_count !== 1 ? "s" : ""}</span>
                          </div>
                          <div className="restaurant-info">
                            <p><FaMapMarkerAlt /><span>{restaurant.city || "Location unavailable"}</span></p>
                            <p><span><strong>Owner:</strong> {restaurant.owner_name || "Unclaimed"}</span></p>
                          </div>
                          <div className="card-actions">
                            <Button as={Link} to={`/restaurants/${restaurant.id}`} variant="outline-danger">View Details</Button>
                            {canClaimRestaurant && (
                              <Button variant="outline-primary" onClick={() => handleClaimRestaurant(restaurant.id)} disabled={claimLoading[restaurant.id]}>{claimLoading[restaurant.id] ? "Claiming..." : "Claim"}</Button>
                            )}
                            {isOwnedByCurrentUser && (
                              <Button variant="outline-warning" onClick={() => handleUnclaimRestaurant(restaurant.id)} disabled={unclaimLoading[restaurant.id]}>Unclaim</Button>
                            )}
                          </div>
                        </Card.Body>
                      </Card>
                    </Col>
                  );
                })}
              </Row>
            </>
          )}
        </section>
      </Container>
    </div>
  );
}

export default RestaurantSearch;