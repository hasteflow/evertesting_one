import re

from pydantic import BaseModel, field_validator

TYPE_FIELD_VALID_INPUTS = [1, 2, 5, 11]
STATUS_FIELD_VALID_INPUTS = ["complete", "incomplete", "cancelled"]


class TaskItem(BaseModel):
    status: str
    type: int
    hash: str

    @field_validator("type")
    def validate_type_field(cls, value):
        assert value in TYPE_FIELD_VALID_INPUTS
        return value

    @field_validator("status")
    def validate_status_field(cls, value):
        assert isinstance(value, str)
        assert value.lower() in STATUS_FIELD_VALID_INPUTS
        return value.lower()

    @field_validator("hash")
    def validate_hash_field(cls, value):
        assert isinstance(value, str)
        assert re.findall(r"([a-fA-F\d]{32})", value)
        return value.lower()
