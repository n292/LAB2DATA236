import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
from app.core.config import settings

logger = logging.getLogger(__name__)

_producer: KafkaProducer | None = None


def get_kafka_producer() -> KafkaProducer | None:
    global _producer
    if not settings.kafka_enabled:
        return None
    if _producer is not None:
        return _producer
    try:
        _producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_server_list,
            client_id=settings.kafka_client_id,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            key_serializer=lambda key: key.encode("utf-8") if key else None,
            acks="all",
            retries=3,
            request_timeout_ms=settings.kafka_request_timeout_ms,
        )
        logger.info("Kafka producer connected to %s", settings.kafka_bootstrap_server_list)
    except Exception as exc: 
        logger.warning("Kafka producer unavailable: %s", exc)
        _producer = None
    return _producer


def publish_event(topic: str, event: dict, key: str | None = None) -> bool:
    producer = get_kafka_producer()
    if producer is None:
        logger.warning("Kafka publish skipped because producer is unavailable. topic=%s", topic)
        return False
    try:
        future = producer.send(topic, key=key, value=event)
        future.get(timeout=10)
        logger.info("Kafka event published. topic=%s entity_id=%s trace_id=%s", topic, event.get("entity", {}).get("entity_id"), event.get("trace_id"))
        return True
    except KafkaError as exc: 
        logger.warning("Kafka publish failed for topic=%s: %s", topic, exc)
        return False


def close_kafka_producer() -> None:
    global _producer
    if _producer is not None:
        try:
            _producer.flush(timeout=5)
            _producer.close(timeout=5)
        except Exception:
            pass
        _producer = None
