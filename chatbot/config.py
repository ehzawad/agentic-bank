from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    bank_name: str = "HSBC"
    model_name: str = "claude-sonnet-4-6"
    max_tokens: int = 4096

    # FAQ confidence thresholds
    faq_high_threshold: float = 0.85
    faq_medium_threshold: float = 0.60

    # Emotion escalation
    emotion_escalation_turns: int = 3
    emotion_escalation_threshold: float = 0.7

    # Auth
    max_auth_attempts: int = 3

    # Persistence
    db_path: str = "data/sessions.db"
    chroma_path: str = "data/chroma"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
