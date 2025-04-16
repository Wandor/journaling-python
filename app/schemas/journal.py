from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date

def capitalize_field_value(value: str) -> str:
    return value.upper() if value else value

class CategorySchema(BaseModel):
    category_name: str = Field(..., alias="categoryName")

    @field_validator("category_name", mode="before")
    def capitalize_category_name(cls, value):
        return capitalize_field_value(value)

    class Config:
        validate_by_name = True


class TagSchema(BaseModel):
    tag_name: str = Field(..., alias="tagName")

    @field_validator("tag_name", mode="before")
    def capitalize_tag_name(cls, value):
        return capitalize_field_value(value)

    class Config:
        validate_by_name = True


class CreateJournalEntrySchema(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255, description="Title must be at least 3 characters long and at most 255 characters.")
    content: str = Field(..., min_length=10, description="Content must be at least 10 characters long.")
    entry_date: date = Field(default_factory=date.today, description="Entry date defaults to today's date.")
    tags: Optional[List[str]] = Field([], description="Optional list of tags.")
    categories: Optional[List[str]] = Field([], description="Optional list of categories.")

    class Config:
        str_min_length = 1
        str_strip_whitespace = True