from pydantic_settings import BaseSettings, SettingsConfigDict


#Валидируем константы из .env
class Settings(BaseSettings): 
    HOST: str
    USER: str
    PASSWORD: str
    DB_NAME: str
    PORT: int = 5432
    TOKEN: str
    ADMIN: str

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB_NAME}"



    model_config = SettingsConfigDict(env_file=r".env")

settings = Settings()

