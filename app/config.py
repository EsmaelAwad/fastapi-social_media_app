from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str 
    algorithm: str 
    access_token_expire_minutes: int 
    host: str 
    database: str 
    user: str 
    password: str 
    port: str 
    database_url: str 
    
    class Config:
        env_file = ".env"

settings = Settings()
