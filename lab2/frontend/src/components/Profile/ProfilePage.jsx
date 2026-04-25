import React, { useState, useEffect, useMemo } from "react";
import { Container, Row, Col, Form, Button, Alert, Spinner } from "react-bootstrap";
import { usersAPI } from "../../services/api";
import authService from "../../services/auth";
import "./Profile.css";

function getInitials(name) {
  if (!name) return "U";
  return name
    .split(" ")
    .map((part) => part.trim()[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function ProfilePage() {
  const userId = authService.getUserId();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [selectedPhotoName, setSelectedPhotoName] = useState("");

  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    about_me: "",
    city: "",
    country: "",
    state: "",
    languages: "",
    gender: "",
    profile_photo_data: "",
  });

  useEffect(() => {
    if (!userId) {
      setError("User not logged in. Please login first.");
      setLoading(false);
      return;
    }

    fetchProfile();
  }, [userId]);

  const fetchProfile = async () => {
    try {
      const response = await usersAPI.getProfile(userId);
      const data = response.data;

      setProfile(data);
      setFormData({
        name: data.name || "",
        phone: data.phone || "",
        about_me: data.about_me || "",
        city: data.city || "",
        country: data.country || "",
        state: data.state || "",
        languages: data.languages || "",
        gender: data.gender || "",
        profile_photo_data: data.profile_photo_data || "",
      });
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail || err.message || "Failed to load profile";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const countries = [
    "United States",
    "Canada",
    "United Kingdom",
    "Australia",
    "India",
    "Other",
  ];

  const states = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
  ];

  const effectivePhoto = useMemo(() => {
    return (
      formData.profile_photo_data ||
      profile?.profile_photo_data ||
      ""
    );
  }, [formData.profile_photo_data, profile]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setError("");
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handlePhotoUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedPhotoName(file.name);
    setError("");

    const reader = new FileReader();
    reader.onloadend = () => {
      const result = typeof reader.result === "string" ? reader.result : "";
      setFormData((prev) => ({
        ...prev,
        profile_photo_data: result,
      }));
    };
    reader.readAsDataURL(file);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError("");
    setSuccess("");
    setSelectedPhotoName("");
    setFormData({
      name: profile?.name || "",
      phone: profile?.phone || "",
      about_me: profile?.about_me || "",
      city: profile?.city || "",
      country: profile?.country || "",
      state: profile?.state || "",
      languages: profile?.languages || "",
      gender: profile?.gender || "",
      profile_photo_data: profile?.profile_photo_data || "",
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);

    if (!userId) {
      setError("User not logged in. Please refresh and login again.");
      setSaving(false);
      return;
    }

    try {
      const response = await usersAPI.updateProfile(userId, formData);
      const updatedProfile = response.data;

      setProfile(updatedProfile);
      setFormData({
        name: updatedProfile.name || "",
        phone: updatedProfile.phone || "",
        about_me: updatedProfile.about_me || "",
        city: updatedProfile.city || "",
        country: updatedProfile.country || "",
        state: updatedProfile.state || "",
        languages: updatedProfile.languages || "",
        gender: updatedProfile.gender || "",
        profile_photo_data: updatedProfile.profile_photo_data || "",
      });

      setSelectedPhotoName("");
      setSuccess("Profile updated successfully!");
      setIsEditing(false);
    } catch (err) {
      const errorMessage =
        err.response?.data?.detail || err.message || "Update failed";
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Container className="text-center py-5">
        <Spinner animation="border" variant="danger" />
      </Container>
    );
  }

  return (
    <Container className="profile-container py-5">
      <Row className="justify-content-center">
        <Col lg={9}>
          <div className="profile-card">
            {error && <Alert variant="danger">{error}</Alert>}
            {success && <Alert variant="success">{success}</Alert>}

            {!isEditing ? (
              <>
                <div className="profile-header">
                  <div className="profile-identity">
                    {effectivePhoto ? (
                      <img
                        src={effectivePhoto}
                        alt="Profile"
                        className="profile-avatar"
                      />
                    ) : (
                      <div className="profile-avatar-placeholder">
                        {getInitials(profile?.name)}
                      </div>
                    )}

                    <div>
                      <h2>My Profile</h2>
                      <p className="profile-subtitle">
                        Manage your personal information and profile photo.
                      </p>
                    </div>
                  </div>

                  <Button variant="outline-danger" onClick={() => setIsEditing(true)}>
                    Edit Profile
                  </Button>
                </div>

                <div className="profile-info">
                  <Row>
                    <Col md={6} className="mb-3">
                      <p><strong>Full Name:</strong></p>
                      <p>{profile?.name || "Not provided"}</p>
                    </Col>
                    <Col md={6} className="mb-3">
                      <p><strong>Email:</strong></p>
                      <p>{profile?.email || "Not provided"}</p>
                    </Col>
                  </Row>

                  <Row>
                    <Col md={6} className="mb-3">
                      <p><strong>Phone:</strong></p>
                      <p>{profile?.phone || "Not provided"}</p>
                    </Col>
                    <Col md={6} className="mb-3">
                      <p><strong>City:</strong></p>
                      <p>{profile?.city || "Not provided"}</p>
                    </Col>
                  </Row>

                  <Row>
                    <Col md={6} className="mb-3">
                      <p><strong>Country:</strong></p>
                      <p>{profile?.country || "Not provided"}</p>
                    </Col>
                    <Col md={6} className="mb-3">
                      <p><strong>State:</strong></p>
                      <p>{profile?.state || "Not provided"}</p>
                    </Col>
                  </Row>

                  <Row>
                    <Col md={6} className="mb-3">
                      <p><strong>Languages:</strong></p>
                      <p>{profile?.languages || "Not provided"}</p>
                    </Col>
                    <Col md={6} className="mb-3">
                      <p><strong>Gender:</strong></p>
                      <p>{profile?.gender || "Not provided"}</p>
                    </Col>
                  </Row>

                  <Row>
                    <Col md={12} className="mb-3">
                      <p><strong>About Me:</strong></p>
                      <p>{profile?.about_me || "Not provided"}</p>
                    </Col>
                  </Row>
                </div>
              </>
            ) : (
              <>
                <div className="profile-header">
                  <div className="profile-identity">
                    {effectivePhoto ? (
                      <img
                        src={effectivePhoto}
                        alt="Profile preview"
                        className="profile-avatar"
                      />
                    ) : (
                      <div className="profile-avatar-placeholder">
                        {getInitials(formData.name || profile?.name)}
                      </div>
                    )}

                    <div>
                      <h2>Edit Profile</h2>
                      <p className="profile-subtitle">
                        Upload a photo and update your personal details.
                      </p>
                    </div>
                  </div>
                </div>

                <Form onSubmit={handleSubmit}>
                  <div className="profile-photo-section">
                    <Form.Group className="mb-3">
                      <Form.Label>Profile Photo</Form.Label>
                      <Form.Control
                        type="file"
                        accept="image/*"
                        onChange={handlePhotoUpload}
                      />
                      {selectedPhotoName && (
                        <div className="photo-file-name">
                          Selected file: {selectedPhotoName}
                        </div>
                      )}
                    </Form.Group>
                  </div>

                  <Row>
                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label>Full Name</Form.Label>
                        <Form.Control
                          type="text"
                          name="name"
                          value={formData.name}
                          onChange={handleChange}
                        />
                      </Form.Group>
                    </Col>

                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label>Phone</Form.Label>
                        <Form.Control
                          type="tel"
                          name="phone"
                          value={formData.phone}
                          onChange={handleChange}
                        />
                      </Form.Group>
                    </Col>
                  </Row>

                  <Form.Group className="mb-3">
                    <Form.Label>About Me</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={3}
                      name="about_me"
                      value={formData.about_me}
                      onChange={handleChange}
                      placeholder="Tell us about yourself..."
                    />
                  </Form.Group>

                  <Row>
                    <Col md={4}>
                      <Form.Group className="mb-3">
                        <Form.Label>City</Form.Label>
                        <Form.Control
                          type="text"
                          name="city"
                          value={formData.city}
                          onChange={handleChange}
                        />
                      </Form.Group>
                    </Col>

                    <Col md={4}>
                      <Form.Group className="mb-3">
                        <Form.Label>Country</Form.Label>
                        <Form.Select
                          name="country"
                          value={formData.country}
                          onChange={handleChange}
                        >
                          <option value="">Select Country</option>
                          {countries.map((c) => (
                            <option key={c} value={c}>
                              {c}
                            </option>
                          ))}
                        </Form.Select>
                      </Form.Group>
                    </Col>

                    <Col md={4}>
                      <Form.Group className="mb-3">
                        <Form.Label>State</Form.Label>
                        <Form.Select
                          name="state"
                          value={formData.state}
                          onChange={handleChange}
                        >
                          <option value="">Select State</option>
                          {states.map((s) => (
                            <option key={s} value={s}>
                              {s}
                            </option>
                          ))}
                        </Form.Select>
                      </Form.Group>
                    </Col>
                  </Row>

                  <Row>
                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label>Languages</Form.Label>
                        <Form.Control
                          type="text"
                          name="languages"
                          value={formData.languages}
                          onChange={handleChange}
                          placeholder="e.g., English, Spanish"
                        />
                      </Form.Group>
                    </Col>

                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label>Gender</Form.Label>
                        <Form.Select
                          name="gender"
                          value={formData.gender}
                          onChange={handleChange}
                        >
                          <option value="">Select Gender</option>
                          <option value="Male">Male</option>
                          <option value="Female">Female</option>
                          <option value="Other">Other</option>
                          <option value="Prefer not to say">Prefer not to say</option>
                        </Form.Select>
                      </Form.Group>
                    </Col>
                  </Row>

                  <Button variant="danger" type="submit" className="mt-3 me-2" disabled={saving}>
                    {saving ? "Saving..." : "Save Changes"}
                  </Button>

                  <Button
                    variant="outline-secondary"
                    className="mt-3"
                    type="button"
                    onClick={handleCancel}
                    disabled={saving}
                  >
                    Cancel
                  </Button>
                </Form>
              </>
            )}
          </div>
        </Col>
      </Row>
    </Container>
  );
}

export default ProfilePage;