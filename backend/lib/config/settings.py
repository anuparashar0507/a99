from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    studio_base_url: str = Field(..., alias="STUDIO_BASE_URL")
    pagos_base_url: str = Field(..., alias="PAGOS_BASE_URL")

    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db_name: str = Field(..., alias="MONGODB_DB_NAME")
    rag_url: str = Field(..., alias="RAG_URL")

    apify_api_key: str = Field(..., alias="APIFY_API_KEY")
    perplexity_api_key: str = Field(..., alias="PERPLEXITY_API_KEY")
    rapid_api_key: str = Field(..., alias="RAPID_API_KEY")
    data_magnet_api_key: str = Field(..., alias="DATA_MAGNET_API_KEY")

    ideation_agent_id: str = Field(..., alias="IDEATION_AGENT_ID")
    outline_agent_id: str = Field(..., alias="OUTLINE_AGENT_ID")
    data_sufficiency_agent_id: str = Field(..., alias="DATA_SUFFICIENCY_AGENT_ID")
    query_research_agent_id: str = Field(..., alias="QUERY_RESEARCH_AGENT_ID")
    query_generator_agent_id: str = Field(..., alias="QUERY_GENERATOR_AGENT_ID")
    content_formatter_agent_id: str = Field(..., alias="CONTENT_FORMATTER_AGENT_ID")
    serp_agent_id: str = Field(..., alias="SERP_AGENT_ID")
    content_agent_id: str = Field(..., alias="CONTENT_AGENT_ID")
    news_sourcer_agent_id: str = Field(..., alias="NEWS_SOURCER_AGENT_ID")
    format_source_agent_id: str = Field(..., alias="FORMAT_SOURCE_AGENT_ID")
    manufacturing_metrices_agent_id: str = Field(
        ..., alias="MANUFACTURING_METRICES_AGENT_ID"
    )
    manufacturing_models_agent_id: str = Field(
        ..., alias="MANUFACTURING_MODELS_AGENT_ID"
    )
    news_topic_selector_agent_id: str = Field(..., alias="NEWS_TOPIC_SELECTOR_AGENT_ID")
    format_news_linkedin_agent_id: str = Field(
        ..., alias="FORMAT_NEWS_LINKEDIN_AGENT_ID"
    )
    format_news_twitter_agent_id: str = Field(..., alias="FORMAT_NEWS_TWITTER_AGENT_ID")

    search_engine_id: str = Field(..., alias="SEARCH_ENGINE_ID")
    google_cse_api_key: str = Field(..., alias="GOOGLE_CSE_API_KEY")

    aws_kb_files_bucket_name: str = Field(..., alias="AWS_KB_FILES_BUCKET_NAME")
    aws_access_key_id: str = Field(..., alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., alias="AWS_SECRET_ACCESS_KEY")
    aws_region_name: str = Field(..., alias="AWS_REGION_NAME")

    # for auth bypass
    user_id: str = Field(..., alias="USER_ID")
