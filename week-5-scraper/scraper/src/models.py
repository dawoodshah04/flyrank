from typing import Optional
from pydantic import BaseModel,ConfigDict,field_validator

class RawBook(BaseModel):
    model_config = ConfigDict(extra='forbid')

    title:str
    product_url:str
    price_text:str
    availability_text:str
    rating_text:str
    description:str
    source_page:str
    fetched_at:str


class Book(RawBook):
    price_gbp:float
    @field_validator("product_url","source_lage")
    @classmethod
    def must_be_https(cls,value:str)->str:
        if not value.startswith("https://"):
            raise ValueError("Url must start with https://")
        return value

    @field_validator("price_gbp")
    @classmethod
    def valide_price(cls,value:float)->float:
        if value < 0:
            raise ValueError("price_gbp cannot be negative")
        return value