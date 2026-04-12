import React, { useEffect, useMemo, useState } from "react";
import { Container, Card, Form, Button, Alert, Row, Col, Spinner } from "react-bootstrap";
import { useNavigate, Link, useParams } from "react-router-dom";
import { restaurantsAPI } from "../../services/api";
import "./RestaurantForms.css";

function getErrorMessage(err, fallback = "Failed to save restaurant.") {
  const detail = err?.response?.data?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item?.msg && Array.isArray(item?.loc)) {
          return `${item.loc.join(" → ")}: ${item.msg}`;
        }
        if (item?.msg) return item.msg;
        return JSON.stringify(item);
      })
      .join(" | ");
  }

  if (detail && typeof detail === "object") {
    return detail.msg || JSON.stringify(detail);
  }

  return err?.response?.data?.message || err?.message || fallback;
}

const createDefaultHours = () => ({
  monday: "",
  tuesday: "",
  wednesday: "",
  thursday: "",
  friday: "",
  saturday: "",
  sunday: "",
});

const createDefaultFormData = () => ({
  name: "",
  cuisine_type: "",
  address: "",
  city: "",
  state: "",
  zip_code: "",
  phone: "",
  pricing_tier: "$$",
  description: "",
  amenities: "",
  hours_of_operation: createDefaultHours(),
});

function AddRestaurantForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditMode = Boolean(id);

  const [formData, setFormData] = useState(createDefaultFormData);
  const [uploadedImageDataUrl, setUploadedImageDataUrl] = useState("");
  const [photoName, setPhotoName] = useState("");
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(isEditMode);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const effectivePreview = useMemo(() => uploadedImageDataUrl || "", [uploadedImageDataUrl]);

  useEffect(() => {
    if (!isEditMode) {
      setInitialLoading(false);
      return;
    }

    const fetchRestaurant = async () => {
      try {
        setInitialLoading(true);
        setError("");

        const response = await restaurantsAPI.getDetails(id);
        const restaurant = response?.data || {};

        setFormData({
          name: restaurant.name || "",
          cuisine_type: restaurant.cuisine_type || "",
          address: restaurant.address || "",
          city: restaurant.city || "",
          state: restaurant.state || "",
          zip_code: restaurant.zip_code || "",
          phone: restaurant.phone || "",
          pricing_tier: restaurant.pricing_tier || "$$",
          description: restaurant.description || "",
          amenities: Array.isArray(restaurant.amenities)
            ? restaurant.amenities.join(", ")
            : typeof restaurant.amenities === "string"
              ? restaurant.amenities
              : "",
          hours_of_operation:
            restaurant.hours_of_operation && typeof restaurant.hours_of_operation === "object"
              ? { ...createDefaultHours(), ...restaurant.hours_of_operation }
              : createDefaultHours(),
        });

        setUploadedImageDataUrl(restaurant.photo_data || "");
      } catch (err) {
        console.error("Load restaurant error:", err);
        setError(getErrorMessage(err, "Failed to load restaurant."));
      } finally {
        setInitialLoading(false);
      }
    };

    fetchRestaurant();
  }, [id, isEditMode]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setError("");
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleHoursChange = (day, value) => {
    setError("");
    setFormData((prev) => ({
      ...prev,
      hours_of_operation: {
        ...prev.hours_of_operation,
        [day]: value,
      },
    }));
  };

  const handlePhotoUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setPhotoName(file.name);
    setError("");

    const reader = new FileReader();
    reader.onloadend = () => {
      const result = typeof reader.result === "string" ? reader.result : "";
      setUploadedImageDataUrl(result);
    };
    reader.readAsDataURL(file);
  };

  const validateForm = () => {
    if (!formData.name.trim()) return "Restaurant name is required.";
    if (!formData.cuisine_type.trim()) return "Cuisine type is required.";
    if (!formData.address.trim()) return "Address is required.";
    if (!formData.city.trim()) return "City is required.";
    if (!formData.description.trim()) return "Description is required.";
    return "";
  };

  const parseAmenities = (value) => {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);

    try {
      const cleanedHours = Object.fromEntries(
        Object.entries(formData.hours_of_operation).map(([day, value]) => [day, value.trim()])
      );

      const payload = {
        ...formData,
        name: formData.name.trim(),
        cuisine_type: formData.cuisine_type.trim(),
        address: formData.address.trim(),
        city: formData.city.trim(),
        state: formData.state.trim(),
        zip_code: formData.zip_code.trim(),
        phone: formData.phone.trim(),
        pricing_tier: formData.pricing_tier,
        description: formData.description.trim(),
        amenities: parseAmenities(formData.amenities),
        hours_of_operation: cleanedHours,
        photo_data: uploadedImageDataUrl || undefined,
      };

      const response = isEditMode
        ? await restaurantsAPI.update(id, payload)
        : await restaurantsAPI.create(payload);

      const savedRestaurantId = response?.data?.id || id;

      setSuccess(`Restaurant ${isEditMode ? "updated" : "created"} successfully.`);

      if (savedRestaurantId) {
        navigate(`/restaurants/${savedRestaurantId}`);
      } else {
        navigate("/");
      }
    } catch (err) {
      console.error("Save restaurant error:", err);
      setError(
        getErrorMessage(
          err,
          isEditMode ? "Failed to update restaurant." : "Failed to create restaurant."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const days = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
  ];

  if (initialLoading) {
    return (
      <Container className="py-5 text-center">
        <Spinner animation="border" variant="danger" />
      </Container>
    );
  }

  return (
    <div className="restaurant-form-page">
      <Container className="py-4">
        <Row className="justify-content-center">
          <Col lg={10} xl={9}>
            <Card className="restaurant-form-card">
              <Card.Body>
                <div className="form-page-header">
                  <h1>{isEditMode ? "Edit Restaurant" : "Add Restaurant"}</h1>
                  <p className="text-muted">
                    {isEditMode
                      ? "Update your restaurant listing details and stored photo."
                      : "Create a new restaurant listing with details and a stored photo."}
                  </p>
                </div>

                {error && <Alert variant="danger">{error}</Alert>}
                {success && <Alert variant="success">{success}</Alert>}

                <Form onSubmit={handleSubmit}>
                  <Row className="g-3">
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label>Restaurant Name</Form.Label>
                        <Form.Control
                          name="name"
                          value={formData.name}
                          onChange={handleChange}
                          placeholder="e.g., Bella Pasta"
                          required
                        />
                      </Form.Group>
                    </Col>

                    <Col md={6}>
                      <Form.Group>
                        <Form.Label>Cuisine Type</Form.Label>
                        <Form.Control
                          name="cuisine_type"
                          value={formData.cuisine_type}
                          onChange={handleChange}
                          placeholder="e.g., Italian"
                          required
                        />
                      </Form.Group>
                    </Col>

                    <Col md={8}>
                      <Form.Group>
                        <Form.Label>Address</Form.Label>
                        <Form.Control
                          name="address"
                          value={formData.address}
                          onChange={handleChange}
                          placeholder="Street address"
                          required
                        />
                      </Form.Group>
                    </Col>

                    <Col md={4}>
                      <Form.Group>
                        <Form.Label>City</Form.Label>
                        <Form.Control
                          name="city"
                          value={formData.city}
                          onChange={handleChange}
                          placeholder="San Jose"
                          required
                        />
                      </Form.Group>
                    </Col>

                    <Col md={4}>
                      <Form.Group>
                        <Form.Label>State</Form.Label>
                        <Form.Control
                          name="state"
                          value={formData.state}
                          onChange={handleChange}
                          placeholder="CA"
                        />
                      </Form.Group>
                    </Col>

                    <Col md={4}>
                      <Form.Group>
                        <Form.Label>ZIP Code</Form.Label>
                        <Form.Control
                          name="zip_code"
                          value={formData.zip_code}
                          onChange={handleChange}
                          placeholder="95112"
                        />
                      </Form.Group>
                    </Col>

                    <Col md={4}>
                      <Form.Group>
                        <Form.Label>Pricing Tier</Form.Label>
                        <Form.Select
                          name="pricing_tier"
                          value={formData.pricing_tier}
                          onChange={handleChange}
                        >
                          <option value="$">$</option>
                          <option value="$$">$$</option>
                          <option value="$$$">$$$</option>
                          <option value="$$$$">$$$$</option>
                        </Form.Select>
                      </Form.Group>
                    </Col>

                    <Col md={6}>
                      <Form.Group>
                        <Form.Label>Phone</Form.Label>
                        <Form.Control
                          name="phone"
                          value={formData.phone}
                          onChange={handleChange}
                          placeholder="(408) 555-1234"
                        />
                      </Form.Group>
                    </Col>

                    <Col xs={12}>
                      <div className="preferences-section">
                        <h5>Hours of Operation</h5>
                        <Row className="g-3">
                          {days.map((day) => (
                            <Col md={6} key={day}>
                              <Form.Group>
                                <Form.Label>
                                  {day.charAt(0).toUpperCase() + day.slice(1)}
                                </Form.Label>
                                <Form.Control
                                  value={formData.hours_of_operation[day]}
                                  onChange={(e) => handleHoursChange(day, e.target.value)}
                                  placeholder="11 AM - 10 PM"
                                />
                              </Form.Group>
                            </Col>
                          ))}
                        </Row>
                      </div>
                    </Col>

                    <Col xs={12}>
                      <Form.Group>
                        <Form.Label>Description</Form.Label>
                        <Form.Control
                          as="textarea"
                          rows={4}
                          name="description"
                          value={formData.description}
                          onChange={handleChange}
                          placeholder="Tell people about the restaurant..."
                          required
                        />
                      </Form.Group>
                    </Col>

                    <Col xs={12}>
                      <Form.Group>
                        <Form.Label>Amenities</Form.Label>
                        <Form.Control
                          type="text"
                          name="amenities"
                          value={formData.amenities}
                          onChange={handleChange}
                          placeholder="e.g., Outdoor seating, Wi-Fi, Parking"
                        />
                        <Form.Text className="text-muted">
                          Separate amenities with commas.
                        </Form.Text>
                      </Form.Group>
                    </Col>

                    <Col xs={12}>
                      <Form.Group>
                        <Form.Label>Restaurant Photo</Form.Label>
                        <Form.Control
                          type="file"
                          accept="image/*"
                          onChange={handlePhotoUpload}
                        />
                        <Form.Text className="text-muted">
                          This photo is stored in the backend database.
                        </Form.Text>
                      </Form.Group>
                    </Col>

                    <Col xs={12}>
                      <div className="photo-preview-wrap">
                        {effectivePreview ? (
                          <>
                            <div className="photo-preview-card">
                              <img
                                src={effectivePreview}
                                alt="Restaurant preview"
                                onError={(e) => {
                                  e.currentTarget.style.display = "none";
                                }}
                              />
                            </div>
                            {photoName && (
                              <p className="preview-caption">Selected file: {photoName}</p>
                            )}
                          </>
                        ) : (
                          <div className="photo-placeholder">No photo selected yet.</div>
                        )}
                      </div>
                    </Col>
                  </Row>

                  <div className="form-actions">
                    <Link
                      to={isEditMode ? `/restaurants/${id}` : "/"}
                      className="btn btn-outline-secondary"
                    >
                      Cancel
                    </Link>

                    <Button type="submit" variant="danger" disabled={loading}>
                      {loading ? (
                        <>
                          <Spinner animation="border" size="sm" className="me-2" />
                          {isEditMode ? "Updating..." : "Creating..."}
                        </>
                      ) : isEditMode ? (
                        "Update Restaurant"
                      ) : (
                        "Create Restaurant"
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

export default AddRestaurantForm;