from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    POSTGRES_URL: str = os.getenv("POSTGRES_URL", "postgresql+asyncpg://user:password@localhost/dbname")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = REDIS_URL

    # App settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "FastAPI App")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    DOMAIN: str = os.getenv("DOMAIN", "http://localhost:3000")

    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "your-paystack-secret-key")
    
    # Auth Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "secret")
    ACCESS_TOKEN_EXPIRY: int = int(os.getenv("ACCESS_TOKEN_EXPIRY", 172800))
    REFRESH_TOKEN_EXPIRY: int = int(os.getenv("REFRESH_TOKEN_EXPIRY", 604800))


    # Email Settings
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "your-brevo-api-key")

    # AWS S3 Settings
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "your-bucket-name")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "your-access-key-id")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "your-secret-access-key")

    # Oauth Secrets
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "your-google-client-id")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "your-google-client-secret")
    GOOGLE_REDIRECT_URL : str = os.getenv("GOOGLE_REDIRECT_URL", "http://localhost:8000/api/v1/auth/callback/google")

    # Firebase Settings
    FIREBASE_TYPE: str = os.getenv("FIREBASE_TYPE", "service_account")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "your-project-id")
    FIREBASE_PRIVATE_KEY_ID: str = os.getenv("FIREBASE_PRIVATE_KEY_ID", "your-private-key-id")
    FIREBASE_PRIVATE_KEY: str = os.getenv("FIREBASE_PRIVATE_KEY", "your-private-key").replace('\\n', '\n')
    FIREBASE_CLIENT_EMAIL: str = os.getenv("FIREBASE_CLIENT_EMAIL", "your-client-email")
    FIREBASE_CLIENT_ID: str = os.getenv("FIREBASE_CLIENT_ID", "your-client-id")
    FIREBASE_AUTH_URI: str = os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
    FIREBASE_TOKEN_URI: str = os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token")
    FIREBASE_AUTH_PROVIDER_X509_CERT_URL: str = os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs")
    FIREBASE_CLIENT_X509_CERT_URL: str = os.getenv("FIREBASE_CLIENT_X509_CERT_URL", "your-client-cert-url")
    FIREBASE_UNIVERSE_DOMAIN: str = os.getenv("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com")


    class Config:
        env_file = ".env"  # Load from .env file
        env_file_encoding = "utf-8"


# Create an instance of settings
settings = Settings()
