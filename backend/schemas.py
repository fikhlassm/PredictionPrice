"""
Skema request/response untuk API prediksi harga rumah.
Validasi dilakukan dengan Pydantic v2.
"""

from typing import Literal
from pydantic import BaseModel, Field, model_validator

# 5 kategori ocean_proximity persis seperti pada data training
OceanProximity = Literal[
    "NEAR BAY", "<1H OCEAN", "INLAND", "NEAR OCEAN", "ISLAND"
]


class HouseFeaturesRequest(BaseModel):
    longitude: float = Field(..., ge=-125.0, le=-113.0,
                              description="Longitude California, kira-kira -125..-113")
    latitude: float = Field(..., ge=32.0, le=43.0,
                             description="Latitude California, kira-kira 32..43")
    housing_median_age: float = Field(..., gt=0, le=100)
    total_rooms: float = Field(..., gt=0)
    total_bedrooms: float = Field(..., gt=0)
    population: float = Field(..., gt=0)
    households: float = Field(..., gt=0)
    median_income: float = Field(..., gt=0, le=50,
                                  description="Dalam puluhan ribu USD, misal 8.3252")
    ocean_proximity: OceanProximity

    @model_validator(mode="after")
    def check_bedrooms_vs_rooms(self):
        if self.total_bedrooms > self.total_rooms:
            raise ValueError(
                "total_bedrooms tidak boleh lebih besar dari total_rooms"
            )
        if self.households > self.population:
            raise ValueError(
                "households tidak masuk akal jika lebih besar dari population"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "longitude": -122.23,
                "latitude": 37.88,
                "housing_median_age": 41,
                "total_rooms": 880,
                "total_bedrooms": 129,
                "population": 322,
                "households": 126,
                "median_income": 8.3252,
                "ocean_proximity": "NEAR BAY",
            }
        }
    }


class PredictionResponse(BaseModel):
    predicted_price: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    use_pca: bool


class ErrorResponse(BaseModel):
    detail: str
