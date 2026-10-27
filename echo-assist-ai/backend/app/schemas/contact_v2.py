from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ContactCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=120)
    relationship: str = Field(min_length=1, max_length=50)
    phone_number: str = Field(min_length=5, max_length=20)
    email: EmailStr | None = None


class ContactUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, max_length=120)
    relationship: str | None = Field(default=None, max_length=50)
    phone_number: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None


class ContactResponse(BaseModel):
    id: int
    name: str
    relationship_type: str
    phone_number: str
    email: EmailStr | None = None

    model_config = {"from_attributes": True}
