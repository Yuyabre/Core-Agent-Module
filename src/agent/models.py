from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    dietary_restrictions: List[str] = Field(default_factory=list, description="e.g., vegan, vegetarian, keto")
    allergies: List[str] = Field(default_factory=list, description="e.g., peanuts, lactose")
    favourite_brands: List[str] = Field(default_factory=list, description="e.g., Oatly, Heinz")
    disliked_items: List[str] = Field(default_factory=list, description="e.g., mushrooms, coriander")


class UserContext(BaseModel):
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    
    household_id: Optional[str] = None
    
    # Integrations
    has_splitwise_tokens: bool = False
    discord_user_id: Optional[str] = None
    
    # Preferences
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    # Meta
    account_status: str = "active"
    join_date: Optional[datetime] = None
