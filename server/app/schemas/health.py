from typing import Literal

from pydantic import BaseModel


class HealthData(BaseModel):
    status: Literal["healthy"]
    environment: str
    version: str


class HealthResponse(BaseModel):
    success: bool
    message: str
    data: HealthData


class DatabaseHealthData(BaseModel):
    status: Literal["connected"]


class DatabaseHealthResponse(BaseModel):
    success: bool
    message: str
    data: DatabaseHealthData
