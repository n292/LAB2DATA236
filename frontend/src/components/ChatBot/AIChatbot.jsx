import React, { useState, useEffect, useRef } from "react";
import { Container, Row, Col, Card, Form, Button, Spinner } from "react-bootstrap";
import { Link } from "react-router-dom";
import { aiAssistantAPI } from "../../services/api";
import authService from "../../services/auth";
import { FaRobot, FaUser, FaTrash, FaLink } from "react-icons/fa";
import StarRatings from "react-star-ratings";
import "./ChatBot.css";

function AIChatbot() {
  const userId = authService.getUserId();
  const messagesEndRef = useRef(null);

  const initialMessage = {
    id: 1,
    role: "assistant",
    content:
      "Hi! I'm your restaurant assistant. I can help you find places based on cuisine, vibe, price, and location. What are you in the mood for today?",
  };

  const [messages, setMessages] = useState([initialMessage]);
  const [userInput, setUserInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);

  const quickActions = [
    "Find dinner tonight",
    "Best rated near me",
    "Vegan options",
    "Romantic dinner",
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const safeText = (value, fallback = "") => {
    if (value === null || value === undefined) return fallback;
    if (typeof value === "string" || typeof value === "number") return String(value);
    if (Array.isArray(value)) return value.join(", ");
    return fallback;
  };

  const sendPrompt = async (text) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMessage = {
      id: Date.now(),
      role: "user",
      content: trimmed,
    };

    const updatedMessages = [...messages, userMessage];

    setMessages(updatedMessages);
    setUserInput("");
    setLoading(true);

    try {
      const conversationHistory = updatedMessages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const response = await aiAssistantAPI.chat(trimmed, conversationHistory, userId);

      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content:
          response?.data?.response ||
          "I found some options for you. Let me know if you want something more specific.",
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (Array.isArray(response?.data?.recommendations)) {
        setRecommendations(response.data.recommendations);
      } else {
        setRecommendations([]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: "Sorry, I ran into an error. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await sendPrompt(userInput);
  };

  const clearChat = () => {
    setMessages([initialMessage]);
    setRecommendations([]);
    setUserInput("");
  };

  return (
    <div className="chatbot-page">
      <Container className="py-4">
        <Row className="justify-content-center g-4">
          <Col lg={8}>
            <Card className="chatbot-card">
              <Card.Header className="chatbot-header">
                <div>
                  <h5 className="mb-1">
                    <FaRobot className="me-2" />
                    Restaurant Assistant
                  </h5>
                  <p className="mb-0 text-muted">
                    Ask for restaurant ideas by cuisine, price, location, or vibe.
                  </p>
                </div>

                <Button
                  variant="outline-danger"
                  size="sm"
                  onClick={clearChat}
                  title="Clear chat"
                >
                  <FaTrash />
                </Button>
              </Card.Header>

              <Card.Body className="messages-container">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`message-row ${
                      message.role === "user" ? "message-row-user" : "message-row-assistant"
                    }`}
                  >
                    <div className={`message-bubble message-bubble-${message.role}`}>
                      <div className="message-meta">
                        {message.role === "user" ? <FaUser /> : <FaRobot />}
                        <span>{message.role === "user" ? "You" : "Assistant"}</span>
                      </div>
                      <p>{message.content}</p>
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="message-row message-row-assistant">
                    <div className="message-bubble message-bubble-assistant">
                      <div className="message-meta">
                        <FaRobot />
                        <span>Assistant</span>
                      </div>
                      <div className="thinking-row">
                        <Spinner animation="border" size="sm" variant="danger" />
                        <span>Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </Card.Body>

              <Card.Footer className="chatbot-footer">
                <Form onSubmit={handleSubmit}>
                  <div className="chat-input-row">
                    <Form.Control
                      type="text"
                      placeholder="Ask me anything about restaurants..."
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      disabled={loading}
                    />
                    <Button variant="danger" type="submit" disabled={loading || !userInput.trim()}>
                      Send
                    </Button>
                  </div>
                </Form>

                {messages.length === 1 && (
                  <div className="quick-actions">
                    <p>Try asking:</p>
                    <div className="action-buttons">
                      {quickActions.map((action, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className="quick-action-btn"
                          onClick={() => sendPrompt(action)}
                        >
                          {action}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </Card.Footer>
            </Card>
          </Col>

          <Col lg={4}>
            <Card className="recommendations-card">
              <Card.Header className="recommendations-header">
                <h5 className="mb-0">Recommendations</h5>
              </Card.Header>

              <Card.Body className="recommendations-body">
                {recommendations.length > 0 ? (
                  recommendations.map((rec) => (
                    <Link
                      key={rec.id}
                      to={`/restaurants/${rec.id}`}
                      className="recommendation-item"
                    >
                      <div className="rec-header">
                        <h6>{safeText(rec.name, "Restaurant")}</h6>
                        <span className="price-tier">
                          {safeText(rec.price_tier || rec.pricing_tier, "")}
                        </span>
                      </div>

                      <div className="rec-rating">
                        <StarRatings
                          rating={Number(rec.rating) || 0}
                          starDimension="16px"
                          starSpacing="1px"
                          starEmptyColor="#ddd"
                          starRatedColor="#d32323"
                          isSelectable={false}
                        />
                        <span>{(Number(rec.rating) || 0).toFixed(1)}</span>
                      </div>

                      <p className="rec-cuisine">
                        {safeText(rec.cuisine_type || rec.cuisine, "Restaurant")}
                      </p>

                      {rec.reasoning && (
                        <p className="rec-reasoning">{safeText(rec.reasoning)}</p>
                      )}

                      <div className="rec-link">
                        <FaLink /> View Details
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="empty-state">
                    <p className="text-muted text-center mb-0">
                      Start chatting to get personalized restaurant recommendations.
                    </p>
                  </div>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default AIChatbot;