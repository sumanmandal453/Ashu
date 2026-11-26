from pydantic import BaseModel, Field


class DigiiSyncRequest(BaseModel):
    sync_courses: bool = True
    sync_assignments: bool = True
    sync_feed: bool = False


class TelegramConnectRequest(BaseModel):
    chat_id: str = Field(min_length=1, max_length=100)


class WhatsAppConnectRequest(BaseModel):
    phone_number: str = Field(min_length=5, max_length=30)
