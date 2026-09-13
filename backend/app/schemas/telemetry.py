from datetime import datetime

from pydantic import BaseModel


class TelemetryCreate(BaseModel):
    station_id: str
    timestamp: datetime
    temperature: float
    humidity: float
    pressure: float
