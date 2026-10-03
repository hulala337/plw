"""Validated API request contracts."""

from pydantic import BaseModel, Field, field_validator, ConfigDict


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TodoIn(RequestModel):
    title: str = Field(min_length=1, max_length=500)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class TodoPatch(RequestModel):
    done: bool


class SettingsPatch(RequestModel):
    autostart: bool | None = None
    idle_seconds: int | None = Field(default=None, ge=30, le=900)
    weather_enabled: bool | None = None
    desktop_pet: bool | None = None
    sounds_enabled: bool | None = None


class EquipmentPatch(RequestModel):
    slot: str = Field(min_length=1, max_length=40)
    item_id: str = Field(min_length=1, max_length=128)
