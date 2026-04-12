from __future__ import annotations

import json
import os
import re
from typing import Any, Iterable, Optional

from dotenv import load_dotenv
from sqlalchemy import or_
from sqlalchemy.orm import Session

from models import Restaurant, UserPreference

try:
    from langchain_ollama import ChatOllama
    from langchain_core.prompts import ChatPromptTemplate
except Exception: 
    ChatOllama = None
    ChatPromptTemplate = None

try:
    from tavily import TavilyClient
except Exception:  
    TavilyClient = None


load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
MAX_CANDIDATES_FOR_LLM = 18
MAX_RECOMMENDATIONS = 5


def _build_llm() -> Any:
    if ChatOllama is None:
        return None
    try:
        return ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.15,
        )
    except Exception:
        return None


llm = _build_llm()
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if (TavilyClient and TAVILY_API_KEY) else None


def _looks_like_brand_or_chain(text: str) -> bool:
    normalized = normalize_text(text)
    if not normalized:
        return False
    tokens = normalized.split()
    if len(tokens) <= 4:
        return True
    brand_markers = {"chipotle", "starbucks", "subway", "mcdonald", "taco bell", "burger king", "wendy", "panera"}
    return any(marker in normalized for marker in brand_markers)


COMMON_STOPWORDS = {
    "a", "an", "the", "i", "me", "my", "we", "our", "you", "your", "for", "to", "of", "in",
    "on", "at", "with", "and", "or", "is", "it", "be", "am", "are", "was", "were", "want",
    "looking", "find", "give", "show", "need", "please", "tonight", "today", "place", "restaurant",
    "restaurants", "food", "have", "get", "something", "somewhere", "near", "nearby", "around",
    "option", "options", "good", "best", "top", "one", "ones", "me", "us", "from", "that",
    "this", "there", "here", "based", "like", "would", "could", "can", "help",
}

DIETARY_WORDS = {
    "vegan", "vegetarian", "gluten-free", "gluten free", "halal", "kosher",
    "dairy-free", "dairy free", "plant-based", "plant based", "keto",
}

PRICE_WORDS = {
    "$": ["cheap", "budget", "inexpensive", "affordable", "low cost", "low-cost"],
    "$$": ["moderate", "mid range", "mid-range", "reasonable", "not too expensive"],
    "$$$": ["upscale", "expensive", "fancy", "date night"],
    "$$$$": ["luxury", "high end", "high-end", "premium"],
}

MEAL_WORDS = {
    "breakfast": ["breakfast"],
    "brunch": ["brunch"],
    "lunch": ["lunch"],
    "dinner": ["dinner", "tonight", "supper"],
    "late night": ["late night", "late-night"],
}

AMBIANCE_WORDS = {
    "casual": ["casual", "relaxed", "laid back", "laid-back"],
    "romantic": ["romantic", "anniversary", "date", "date night", "date-night"],
    "family-friendly": ["family", "kids", "kid friendly", "kid-friendly"],
    "upscale": ["upscale", "fancy", "elegant", "fine dining", "fine-dining"],
    "outdoor seating": ["patio", "outdoor", "terrace", "rooftop"],
    "quiet": ["quiet", "calm"],
    "trendy": ["trendy", "popular", "hip"],
}

LIVE_INFO_TERMS = {
    "open now", "open", "closed", "close", "closing", "hours", "hour", "reservation",
    "reservations", "menu", "phone", "call", "event", "events", "special", "specials",
    "busy", "wait time", "wait", "today", "tonight", "currently",
}

GREETING_WORDS = {
    "hi", "hello", "hey", "yo", "good morning", "good afternoon", "good evening"
}



def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def safe_json_loads(value: Any, default: Any = None) -> Any:
    if default is None:
        default = []

    if value in (None, "", [], {}, "null"):
        return default
    if isinstance(value, (list, dict)):
        return value

    try:
        return json.loads(value)
    except Exception:
        return default


def safe_parse_llm_json(content: str, default: dict[str, Any]) -> dict[str, Any]:
    cleaned = (content or "").strip()
    if not cleaned:
        return default

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:].strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else default
    except Exception:
        return default


def serialize_conversation_history(conversation_history: Optional[list[Any]]) -> list[dict[str, str]]:
    if not conversation_history:
        return []

    serialized: list[dict[str, str]] = []
    for msg in conversation_history:
        if hasattr(msg, "model_dump"):
            dumped = msg.model_dump()
            serialized.append(
                {
                    "role": str(dumped.get("role", "user")),
                    "content": str(dumped.get("content", "")),
                }
            )
        elif isinstance(msg, dict):
            serialized.append(
                {
                    "role": str(msg.get("role", "user")),
                    "content": str(msg.get("content", "")),
                }
            )
        else:
            serialized.append(
                {
                    "role": str(getattr(msg, "role", "user")),
                    "content": str(getattr(msg, "content", "")),
                }
            )
    return serialized


def is_greeting(message: str) -> bool:
    return normalize_text(message) in GREETING_WORDS


def unique_nonempty(values: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        key = normalize_text(text)
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def listify_string_or_json(value: Any) -> list[str]:
    parsed = safe_json_loads(value, default=[])
    if isinstance(parsed, list):
        return unique_nonempty(parsed)
    if isinstance(parsed, dict):
        return unique_nonempty([f"{k}: {v}" for k, v in parsed.items()])
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def dictify_hours(value: Any) -> dict[str, Any]:
    parsed = safe_json_loads(value, default={})
    return parsed if isinstance(parsed, dict) else {}


def compact_text(value: Any, limit: int = 600) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."




def get_user_preferences_dict(db: Session, user_id: int) -> dict[str, Any]:
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        return {
            "cuisines": [],
            "price_range": None,
            "preferred_location": None,
            "dietary_restrictions": [],
            "ambiance": [],
            "sort_preference": None,
            "search_radius": 5,
        }

    return {
        "cuisines": listify_string_or_json(pref.cuisines),
        "price_range": pref.price_range,
        "preferred_location": pref.preferred_location,
        "dietary_restrictions": listify_string_or_json(pref.dietary_restrictions),
        "ambiance": listify_string_or_json(pref.ambiance),
        "sort_preference": pref.sort_preference,
        "search_radius": pref.search_radius or 5,
    }


def get_db_city_names(db: Session) -> list[str]:
    rows = db.query(Restaurant.city).distinct().all()
    return unique_nonempty([row[0] for row in rows if row and row[0]])


def restaurant_to_search_blob(restaurant: Restaurant) -> str:
    parts: list[str] = [
        restaurant.name or "",
        restaurant.cuisine_type or "",
        restaurant.description or "",
        restaurant.address or "",
        restaurant.city or "",
        restaurant.zip_code or "",
        restaurant.pricing_tier or "",
        restaurant.phone or "",
        restaurant.email or "",
    ]
    parts.extend(listify_string_or_json(restaurant.amenities))
    hours = dictify_hours(restaurant.hours_of_operation)
    for day, value in hours.items():
        parts.append(f"{day} {value}")
    return normalize_text(" ".join(parts))


def restaurant_to_candidate(restaurant: Restaurant) -> dict[str, Any]:
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "cuisine_type": restaurant.cuisine_type,
        "city": restaurant.city,
        "price_tier": restaurant.pricing_tier,
        "average_rating": float(restaurant.average_rating or 0),
        "review_count": int(restaurant.review_count or 0),
        "description": compact_text(restaurant.description or "", 180),
        "amenities": listify_string_or_json(restaurant.amenities)[:8],
    }




def _extract_price_symbol(text: str) -> Optional[str]:
    match = re.search(r"\${1,4}", text)
    if match:
        return match.group(0)
    for symbol, words in PRICE_WORDS.items():
        if any(word in text for word in words):
            return symbol
    if "cheaper" in text or "more affordable" in text or "less expensive" in text:
        return "CHEAPER"
    if "more expensive" in text or "fancier" in text:
        return "PRICIER"
    return None


def _extract_first_match(text: str, mapping: dict[str, list[str]]) -> Optional[str]:
    for canonical, terms in mapping.items():
        if any(term in text for term in terms):
            return canonical
    return None


def _extract_many_matches(text: str, mapping_or_words: Iterable[str]) -> list[str]:
    found: list[str] = []
    for value in mapping_or_words:
        if normalize_text(value) in text:
            found.append(str(value))
    return unique_nonempty(found)


def _extract_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9&'\-]{1,}", text.lower())
    filtered = [t for t in tokens if t not in COMMON_STOPWORDS and len(t) > 2]
    return unique_nonempty(filtered)[:8]


def _extract_location(text: str, city_names: list[str]) -> Optional[str]:
    normalized = normalize_text(text)
    for city in sorted(city_names, key=len, reverse=True):
        if normalize_text(city) and re.search(rf"\b{re.escape(normalize_text(city))}\b", normalized):
            return city

    match = re.search(r"\b(?:in|near|around)\s+([a-zA-Z][a-zA-Z\s]{1,40})", normalized)
    if match:
        candidate = match.group(1).strip(" .,!?")
        if candidate:
            return candidate.title()
    return None


def _mentions_live_info(text: str) -> bool:
    normalized = normalize_text(text)
    return any(term in normalized for term in LIVE_INFO_TERMS)


def _fallback_intent_analysis(user_message: str, conversation_history: list[dict[str, str]], db: Session) -> dict[str, Any]:
    normalized = normalize_text(user_message)
    cities = get_db_city_names(db)
    restaurant_rows = db.query(Restaurant.id, Restaurant.name, Restaurant.cuisine_type).all()
    restaurant_names = unique_nonempty([row[1] for row in restaurant_rows if row[1]])

    restaurant_name = None
    for name in sorted(restaurant_names, key=len, reverse=True):
        if normalize_text(name) in normalized:
            restaurant_name = name
            break

    price_range = _extract_price_symbol(normalized)
    cuisine = None
    if not restaurant_name:
        for _id, name, cuisine_type in restaurant_rows:
            if cuisine_type and normalize_text(cuisine_type) in normalized:
                cuisine = cuisine_type
                break

    dietary_matches = []
    for value in DIETARY_WORDS:
        if value in normalized:
            dietary_matches.append(value.replace(" ", "-"))

    ambiance_matches = []
    for canonical, terms in AMBIANCE_WORDS.items():
        if any(term in normalized for term in terms):
            ambiance_matches.append(canonical)

    meal_time = _extract_first_match(normalized, MEAL_WORDS)
    occasion = None
    if "anniversary" in normalized:
        occasion = "anniversary"
    elif "date" in normalized:
        occasion = "date night"
    elif "birthday" in normalized:
        occasion = "birthday"
    elif "business" in normalized or "client" in normalized:
        occasion = "business meal"

    intent = "restaurant_search"
    if restaurant_name and _mentions_live_info(normalized):
        intent = "restaurant_info"
    elif restaurant_name:
        intent = "restaurant_search"
    elif any(word in normalized for word in ["cheaper", "more affordable", "more expensive", "instead", "another", "else", "similar"]):
        intent = "refine_search"

    return {
        "intent": intent,
        "restaurant_name": restaurant_name,
        "cuisine": cuisine,
        "price_range": price_range,
        "dietary_restrictions": unique_nonempty(dietary_matches),
        "ambiance": unique_nonempty(ambiance_matches),
        "occasion": occasion,
        "location": _extract_location(normalized, cities),
        "meal_time": meal_time,
        "keywords": _extract_keywords(normalized),
        "live_info_needed": _mentions_live_info(normalized),
        "sort_preference": "rating" if any(term in normalized for term in ["best", "top", "highest rated"]) else None,
        "must_use_preferences": True,
        "fallback_allowed": True,
    }


def analyze_user_request_with_llm(
    user_message: str,
    conversation_history: list[dict[str, str]],
    preferences: dict[str, Any],
    db: Session,
) -> dict[str, Any]:
    fallback = _fallback_intent_analysis(user_message, conversation_history, db)
    if llm is None or ChatPromptTemplate is None:
        return fallback

    cities = get_db_city_names(db)
    restaurant_examples = db.query(Restaurant.id, Restaurant.name, Restaurant.cuisine_type, Restaurant.city).limit(60).all()
    restaurant_catalog = [
        {"id": row[0], "name": row[1], "cuisine_type": row[2], "city": row[3]}
        for row in restaurant_examples
    ]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are the intent parser for a restaurant recommendation assistant.
Return ONLY valid JSON with exactly these keys:
intent, restaurant_name, cuisine, price_range, dietary_restrictions, ambiance, occasion, location, meal_time, keywords, live_info_needed, sort_preference, must_use_preferences, fallback_allowed

Rules:
- intent must be one of: greeting, restaurant_search, refine_search, restaurant_info, other.
- restaurant_name is a restaurant or brand name if the user asks for one specific place or chain, else null.
- cuisine is a cuisine type if stated or strongly implied, else null.
- price_range must be one of "$", "$$", "$$$", "$$$$", "CHEAPER", "PRICIER", or null.
- dietary_restrictions must be an array of strings.
- ambiance must be an array of strings.
- keywords must be an array of short strings useful for database matching.
- live_info_needed is true only for current hours, open now, menu, phone, reservations, or time-sensitive business info.
- must_use_preferences should usually be true unless the user explicitly overrides saved preferences.
- fallback_allowed should be true when an exact named restaurant may not exist in the database and similar options would still be helpful.
- Use conversation history to resolve follow-ups like "cheaper ones", "something more casual", or "what about Chipotle".
- Never invent restaurants that are not in the provided catalog.
- Do not wrap the JSON in markdown.
""",
            ),
            (
                "human",
                """
Saved user preferences:
{preferences}

Conversation history:
{conversation_history}

Known cities in the database:
{cities}

Sample restaurant catalog from the database:
{restaurant_catalog}

Current user message:
{user_message}
""",
            ),
        ]
    )

    try:
        chain = prompt | llm
        result = chain.invoke(
            {
                "preferences": json.dumps(preferences, ensure_ascii=False),
                "conversation_history": json.dumps(conversation_history, ensure_ascii=False),
                "cities": json.dumps(cities[:60], ensure_ascii=False),
                "restaurant_catalog": json.dumps(restaurant_catalog, ensure_ascii=False),
                "user_message": user_message,
            }
        )
        parsed = safe_parse_llm_json(getattr(result, "content", ""), fallback)
        parsed.setdefault("dietary_restrictions", [])
        parsed.setdefault("ambiance", [])
        parsed.setdefault("keywords", [])
        return parsed
    except Exception:
        return fallback


def merge_request_with_preferences(analysis: dict[str, Any], preferences: dict[str, Any]) -> dict[str, Any]:
    merged = dict(analysis)

    if merged.get("intent") == "greeting":
        return merged

    explicit_cuisine = bool(merged.get("cuisine") or merged.get("restaurant_name"))
    explicit_price = merged.get("price_range") not in (None, "", [])
    explicit_location = bool(merged.get("location"))
    explicit_dietary = bool(merged.get("dietary_restrictions"))
    explicit_ambiance = bool(merged.get("ambiance"))

    if merged.get("must_use_preferences", True):
        if not explicit_cuisine and preferences.get("cuisines"):
            merged["preferred_cuisines"] = preferences["cuisines"]
        else:
            merged["preferred_cuisines"] = preferences.get("cuisines", [])

        if not explicit_price and preferences.get("price_range"):
            merged["effective_price_range"] = preferences["price_range"]
        else:
            merged["effective_price_range"] = None if merged.get("price_range") in ("CHEAPER", "PRICIER") else merged.get("price_range")

        if not explicit_location and preferences.get("preferred_location"):
            merged["effective_location"] = preferences["preferred_location"]
        else:
            merged["effective_location"] = merged.get("location")

        if not explicit_dietary and preferences.get("dietary_restrictions"):
            merged["effective_dietary"] = preferences["dietary_restrictions"]
        else:
            merged["effective_dietary"] = merged.get("dietary_restrictions", [])

        if not explicit_ambiance and preferences.get("ambiance"):
            merged["effective_ambiance"] = preferences["ambiance"]
        else:
            merged["effective_ambiance"] = merged.get("ambiance", [])
    else:
        merged["preferred_cuisines"] = preferences.get("cuisines", [])
        merged["effective_price_range"] = None if merged.get("price_range") in ("CHEAPER", "PRICIER") else merged.get("price_range")
        merged["effective_location"] = merged.get("location")
        merged["effective_dietary"] = merged.get("dietary_restrictions", [])
        merged["effective_ambiance"] = merged.get("ambiance", [])

    return merged



def _broad_restaurant_query(db: Session, request: dict[str, Any]) -> list[Restaurant]:
    query = db.query(Restaurant)

    restaurant_name = request.get("restaurant_name")
    cuisine = request.get("cuisine")
    price_range = request.get("effective_price_range")
    location = request.get("effective_location")
    dietary = request.get("effective_dietary", []) or []
    ambiance = request.get("effective_ambiance", []) or []
    keywords = request.get("keywords", []) or []
    preferred_cuisines = request.get("preferred_cuisines", []) or []

    if restaurant_name:
        query = query.filter(Restaurant.name.ilike(f"%{restaurant_name}%"))
        results = query.all()
        if results:
            return results
        return []

    query = db.query(Restaurant)
    filters = []

    if cuisine:
        filters.append(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    for pref_cuisine in preferred_cuisines[:2]:
        filters.append(Restaurant.cuisine_type.ilike(f"%{pref_cuisine}%"))
    if location:
        filters.append(Restaurant.city.ilike(f"%{location}%"))
    if price_range:
        filters.append(Restaurant.pricing_tier == price_range)
    for item in dietary[:3]:
        filters.append(Restaurant.amenities.ilike(f"%{item}%"))
        filters.append(Restaurant.description.ilike(f"%{item}%"))
    for item in ambiance[:3]:
        filters.append(Restaurant.amenities.ilike(f"%{item}%"))
        filters.append(Restaurant.description.ilike(f"%{item}%"))
    for keyword in keywords[:5]:
        filters.append(Restaurant.name.ilike(f"%{keyword}%"))
        filters.append(Restaurant.description.ilike(f"%{keyword}%"))
        filters.append(Restaurant.cuisine_type.ilike(f"%{keyword}%"))
        filters.append(Restaurant.city.ilike(f"%{keyword}%"))

    if filters:
        results = query.filter(or_(*filters)).all()
        if results:
            return results

    return db.query(Restaurant).all()


def _candidate_keyword_score(restaurant: Restaurant, request: dict[str, Any], preferences: dict[str, Any]) -> tuple[float, list[str]]:
    blob = restaurant_to_search_blob(restaurant)
    score = 0.0
    reasons: list[str] = []

    name_norm = normalize_text(restaurant.name)
    cuisine_norm = normalize_text(restaurant.cuisine_type)
    city_norm = normalize_text(restaurant.city)
    price_tier = restaurant.pricing_tier or ""
    rating = float(restaurant.average_rating or 0)
    review_count = int(restaurant.review_count or 0)

    restaurant_name = normalize_text(request.get("restaurant_name"))
    cuisine = normalize_text(request.get("cuisine"))
    location = normalize_text(request.get("effective_location"))
    dietary = [normalize_text(x) for x in request.get("effective_dietary", []) or []]
    ambiance = [normalize_text(x) for x in request.get("effective_ambiance", []) or []]
    keywords = [normalize_text(x) for x in request.get("keywords", []) or []]
    preferred_cuisines = [normalize_text(x) for x in preferences.get("cuisines", []) or []]

    if restaurant_name:
        if restaurant_name == name_norm:
            score += 120
            reasons.append("exact restaurant name match")
        elif restaurant_name in name_norm:
            score += 70
            reasons.append("close restaurant name match")
        else:
            score -= 40

    if cuisine:
        if cuisine in cuisine_norm or cuisine in blob:
            score += 45
            reasons.append(f"matches your {request['cuisine']} request")
        else:
            score -= 12

    for pref_cuisine in preferred_cuisines[:3]:
        if pref_cuisine and pref_cuisine in cuisine_norm:
            score += 14
            if len(reasons) < 3:
                reasons.append(f"fits your {pref_cuisine} preference")
            break

    effective_price = request.get("effective_price_range")
    requested_price = request.get("price_range")
    if effective_price:
        if price_tier == effective_price:
            score += 24
            reasons.append(f"fits your {effective_price} budget")
        elif price_tier and abs(len(price_tier) - len(effective_price)) == 1:
            score += 8
        elif price_tier:
            score -= 8
    elif requested_price == "CHEAPER":
        if price_tier in ("$", "$$"):
            score += 14
            reasons.append("leans cheaper")
    elif requested_price == "PRICIER":
        if price_tier in ("$$$", "$$$$"):
            score += 14
            reasons.append("leans more upscale")

    if location:
        if location in city_norm or location in blob:
            score += 20
            reasons.append("in your preferred area")
        else:
            score -= 5

    for item in dietary[:3]:
        if item and item in blob:
            score += 18
            if len(reasons) < 3:
                reasons.append(f"supports {item} dining")

    for item in ambiance[:3]:
        if item and item in blob:
            score += 15
            if len(reasons) < 3:
                reasons.append(f"has a {item} vibe")

    meal_time = normalize_text(request.get("meal_time"))
    occasion = normalize_text(request.get("occasion"))
    if meal_time and meal_time in blob:
        score += 6
    if occasion and occasion in blob:
        score += 8

    for keyword in keywords[:5]:
        if keyword in blob:
            score += 8

    score += rating * 6
    score += min(review_count, 30) * 0.6

    if not reasons:
        if rating >= 4.5:
            reasons.append("highly rated")
        elif restaurant.cuisine_type:
            reasons.append(f"good {restaurant.cuisine_type} option")
        else:
            reasons.append("relevant to your request")

    return score, unique_nonempty(reasons)[:3]


def _llm_rank_candidates(
    request: dict[str, Any],
    preferences: dict[str, Any],
    candidates: list[Restaurant],
    conversation_history: list[dict[str, str]],
) -> dict[int, dict[str, Any]]:
    if llm is None or ChatPromptTemplate is None or not candidates:
        return {}

    candidate_payload = [restaurant_to_candidate(c) for c in candidates[:MAX_CANDIDATES_FOR_LLM]]
    default = {"selected": []}

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You rank database restaurants for a recommendation assistant.
Return ONLY valid JSON in this format:
{"selected":[{"id":123,"reasoning":"...","confidence":0.0}]}

Rules:
- Choose between 0 and 5 restaurants.
- You may ONLY use ids that appear in the candidate list.
- Prefer restaurants that best match the user's current request first, then saved preferences.
- If the user asked for a specific restaurant or chain name, strongly prefer exact or close name matches.
- If no candidate is a good fit, return an empty selected array.
- Reasoning must be short and concrete.
- confidence must be between 0 and 1.
- Do not include markdown.
""",
            ),
            (
                "human",
                """
Structured request:
{request}

Saved preferences:
{preferences}

Conversation history:
{conversation_history}

Candidate restaurants:
{candidates}
""",
            ),
        ]
    )

    try:
        chain = prompt | llm
        result = chain.invoke(
            {
                "request": json.dumps(request, ensure_ascii=False),
                "preferences": json.dumps(preferences, ensure_ascii=False),
                "conversation_history": json.dumps(conversation_history, ensure_ascii=False),
                "candidates": json.dumps(candidate_payload, ensure_ascii=False),
            }
        )
        parsed = safe_parse_llm_json(getattr(result, "content", ""), default)
        items = parsed.get("selected", []) if isinstance(parsed.get("selected", []), list) else []
        llm_choices: dict[int, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                rid = int(item.get("id"))
            except Exception:
                continue
            llm_choices[rid] = {
                "reasoning": compact_text(item.get("reasoning", "Relevant to your request"), 120),
                "confidence": max(0.0, min(1.0, float(item.get("confidence", 0.5) or 0.5))),
            }
        return llm_choices
    except Exception:
        return {}


def rank_restaurants(
    restaurants: list[Restaurant],
    request: dict[str, Any],
    preferences: dict[str, Any],
    conversation_history: list[dict[str, str]],
) -> list[dict[str, Any]]:
    prelim: list[dict[str, Any]] = []
    for restaurant in restaurants:
        score, reasons = _candidate_keyword_score(restaurant, request, preferences)
        prelim.append({
            "restaurant": restaurant,
            "base_score": score,
            "reasons": reasons,
        })

    prelim.sort(
        key=lambda item: (
            item["base_score"],
            float(item["restaurant"].average_rating or 0),
            int(item["restaurant"].review_count or 0),
        ),
        reverse=True,
    )

    top_for_llm = [item["restaurant"] for item in prelim[:MAX_CANDIDATES_FOR_LLM]]
    llm_rank = _llm_rank_candidates(request, preferences, top_for_llm, conversation_history)

    ranked: list[dict[str, Any]] = []
    for item in prelim:
        restaurant = item["restaurant"]
        total_score = float(item["base_score"])
        reasoning = list(item["reasons"])
        llm_choice = llm_rank.get(restaurant.id)
        if llm_choice:
            total_score += 45 * llm_choice["confidence"]
            if llm_choice["reasoning"]:
                reasoning.insert(0, llm_choice["reasoning"])
        ranked.append(
            {
                "restaurant": restaurant,
                "score": total_score,
                "reasons": unique_nonempty(reasoning)[:3],
                "llm_selected": bool(llm_choice),
            }
        )

    ranked.sort(
        key=lambda item: (
            item["llm_selected"],
            item["score"],
            float(item["restaurant"].average_rating or 0),
            int(item["restaurant"].review_count or 0),
        ),
        reverse=True,
    )

    positive = [item for item in ranked if item["score"] > 0]
    return (positive or ranked)[:MAX_RECOMMENDATIONS]


def format_restaurants_for_response(ranked_restaurants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted: list[dict[str, Any]] = []
    for item in ranked_restaurants:
        restaurant = item["restaurant"]
        formatted.append(
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "rating": float(restaurant.average_rating or 0),
                "price_tier": restaurant.pricing_tier or "Unknown",
                "cuisine_type": restaurant.cuisine_type or "Unknown",
                "reasoning": "; ".join(unique_nonempty(item["reasons"])[:2]) or "Relevant to your request",
            }
        )
    return formatted




def _summarize_tavily_results(title_and_content: list[str], subject_name: Optional[str] = None) -> str:
    if not title_and_content:
        return ""

    combined = "\n".join(title_and_content[:3])

    if llm is not None and ChatPromptTemplate is not None:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
Summarize live restaurant web info in 1 or 2 short sentences.
Only use the provided text.
Do not dump raw snippets.
If the info is uncertain, say it could not be fully confirmed.
""",
                ),
                (
                    "human",
                    """
Restaurant: {subject_name}
Web snippets:
{combined}
""",
                ),
            ]
        )
        try:
            chain = prompt | llm
            result = chain.invoke({"subject_name": subject_name or "unknown", "combined": combined})
            text = compact_text(getattr(result, "content", "").strip(), 220)
            if text:
                return text
        except Exception:
            pass

    text = compact_text(combined, 500)
    return text


def get_live_context_note(
    request: dict[str, Any],
    recommendations: list[dict[str, Any]],
    preferences: dict[str, Any],
) -> str:
    if not tavily_client or not request.get("live_info_needed"):
        return ""

    subject_name = request.get("restaurant_name")
    location = request.get("effective_location") or preferences.get("preferred_location")
    queries: list[str] = []

    if subject_name:
        query = f"{subject_name} restaurant {location or ''} hours menu"
        queries.append(query.strip())
    else:
        for rec in recommendations[:2]:
            query = f"{rec['name']} restaurant {location or ''} hours"
            queries.append(query.strip())

    if not queries:
        return ""

    snippets: list[str] = []
    for query in queries[:2]:
        try:
            result = tavily_client.search(query=query, search_depth="basic", max_results=2)
            for item in result.get("results", [])[:2]:
                title = compact_text(item.get("title", ""), 80)
                content = compact_text(item.get("content", ""), 160)
                if title or content:
                    snippets.append(f"{title}: {content}")
        except Exception:
            continue

    summary = _summarize_tavily_results(snippets, subject_name)
    return summary


def _search_named_restaurant_live(restaurant_name: str, location: Optional[str]) -> list[dict[str, str]]:
    if not tavily_client or not restaurant_name:
        return []

    query = f"{restaurant_name} near {location}".strip() if location else restaurant_name
    try:
        result = tavily_client.search(query=query, search_depth="basic", max_results=3)
    except Exception:
        return []

    matches: list[dict[str, str]] = []
    for item in result.get("results", [])[:3]:
        matches.append({
            "title": compact_text(item.get("title", ""), 90),
            "content": compact_text(item.get("content", ""), 180),
            "url": str(item.get("url", "") or ""),
        })
    return matches


def _build_live_named_restaurant_response(request: dict[str, Any], live_matches: list[dict[str, str]]) -> str:
    restaurant_name = request.get("restaurant_name") or "That restaurant"
    location = request.get("effective_location") or request.get("location")
    if not live_matches:
        if location:
            return f"I couldn't confirm a {restaurant_name} location near {location}. Try a nearby city or ask for current hours instead."
        return f"I couldn't confirm a current {restaurant_name} location from live web results."

    first = live_matches[0]
    title = first.get("title", "")
    content = first.get("content", "")
    parts = []
    if location:
        parts.append(f"I couldn't find {restaurant_name} in the local database, but I checked live results for {location}.")
    else:
        parts.append(f"I couldn't find {restaurant_name} in the local database, but I checked live results.")
    if title:
        parts.append(title)
    if content:
        parts.append(content)
    return compact_text(" ".join(parts), 700)



def _fallback_response(
    request: dict[str, Any],
    preferences: dict[str, Any],
    recommendations: list[dict[str, Any]],
    live_note: str,
    exact_name_found: bool,
) -> str:
    if not recommendations:
        if request.get("restaurant_name") and not exact_name_found:
            base = f"I couldn't find {request['restaurant_name']} in the restaurant database."
            if request.get("fallback_allowed"):
                base += " I also could not find strong similar matches worth recommending."
            if live_note:
                base += f" Live info: {live_note}"
            return base

        base = "I couldn't find strong matches in the restaurant database for that request."
        if live_note:
            base += f" Live info: {live_note}"
        return base

    if request.get("restaurant_name") and not exact_name_found:
        intro = f"I couldn't find {request['restaurant_name']} exactly in the database, but here are the closest useful options"
    else:
        intro = "Here are some restaurant options that fit your request"

    lines = []
    for idx, rec in enumerate(recommendations[:2], start=1):
        lines.append(
            f"{idx}. {rec['name']} ({rec['rating']:.1f}★, {rec['price_tier']}, {rec['cuisine_type']})"
        )

    response = intro + ": " + " ".join(lines)
    if live_note:
        response += f" Live note: {live_note}"
    return response


def generate_ai_response_with_llm(
    user_message: str,
    request: dict[str, Any],
    preferences: dict[str, Any],
    recommendations: list[dict[str, Any]],
    conversation_history: list[dict[str, str]],
    live_note: str,
    exact_name_found: bool,
) -> str:
    fallback = _fallback_response(request, preferences, recommendations, live_note, exact_name_found)
    if llm is None or ChatPromptTemplate is None:
        return fallback

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are a helpful restaurant assistant.
Write a conversational response grounded ONLY in the provided recommendations and live note.

Rules:
- Do not mention any restaurant not present in the Recommendations list.
- If the user asked for a specific restaurant and it was not found exactly, say so clearly.
- If Recommendations is empty, say that no strong database matches were found.
- Use the user's saved preferences naturally when relevant.
- Keep the response under 180 words.
- Prefer 1 to 2 natural paragraphs when helpful.
- Do not output JSON.
""",
            ),
            (
                "human",
                """
User message:
{user_message}

Structured request:
{request}

Saved preferences:
{preferences}

Conversation history:
{conversation_history}

Recommendations:
{recommendations}

Exact named restaurant found:
{exact_name_found}

Optional live note:
{live_note}
""",
            ),
        ]
    )

    try:
        chain = prompt | llm
        result = chain.invoke(
            {
                "user_message": user_message,
                "request": json.dumps(request, ensure_ascii=False),
                "preferences": json.dumps(preferences, ensure_ascii=False),
                "conversation_history": json.dumps(conversation_history, ensure_ascii=False),
                "recommendations": json.dumps(recommendations, ensure_ascii=False),
                "exact_name_found": json.dumps(exact_name_found),
                "live_note": live_note or "",
            }
        )
        text = compact_text(getattr(result, "content", "").strip(), 900)
        return text or fallback
    except Exception:
        return fallback




def process_chat_message(
    user_message: str,
    db: Session,
    user_id: int,
    conversation_history: Optional[list[Any]] = None,
) -> dict[str, Any]:
    history = serialize_conversation_history(conversation_history)

    if is_greeting(user_message):
        return {
            "response": "Hi! I can help you find restaurants by cuisine, price, location, or vibe. What are you in the mood for today?",
            "recommendations": [],
            "filters_used": {},
        }

    preferences = get_user_preferences_dict(db, user_id)
    analysis = analyze_user_request_with_llm(user_message, history, preferences, db)
    request = merge_request_with_preferences(analysis, preferences)

    candidates = _broad_restaurant_query(db, request)
    ranked = rank_restaurants(candidates, request, preferences, history)
    recommendations = format_restaurants_for_response(ranked)

    exact_name_found = False
    if request.get("restaurant_name"):
        requested_name = normalize_text(request["restaurant_name"])
        exact_name_found = any(normalize_text(rec["name"]) == requested_name for rec in recommendations)

    if request.get("restaurant_name") and not exact_name_found and request.get("fallback_allowed") is False:
        recommendations = []

    live_note = get_live_context_note(request, recommendations, preferences)

    live_chain_matches: list[dict[str, str]] = []
    if request.get("restaurant_name") and not exact_name_found and _looks_like_brand_or_chain(request.get("restaurant_name", "")):
        live_chain_matches = _search_named_restaurant_live(
            request["restaurant_name"],
            request.get("effective_location") or request.get("location"),
        )

    if request.get("restaurant_name") and not exact_name_found and live_chain_matches:
        response_text = _build_live_named_restaurant_response(request, live_chain_matches)
        recommendations = []
    else:
        response_text = generate_ai_response_with_llm(
            user_message=user_message,
            request=request,
            preferences=preferences,
            recommendations=recommendations,
            conversation_history=history,
            live_note=live_note,
            exact_name_found=exact_name_found,
        )

    return {
        "response": response_text,
        "recommendations": recommendations,
        "filters_used": request,
    }
