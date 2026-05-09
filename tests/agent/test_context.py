import pytest
from src.agent.models import UserContext, UserPreferences
from src.agent.context import build_system_prompt
from src.agent.prompts import SYSTEM_PROMPT


def test_build_system_prompt_no_context():
    result = build_system_prompt("BASE", None)
    assert result == "BASE"

def test_build_system_prompt_with_basic_context():
    context = UserContext(
        user_id="user_123",
        name="Alice",
        household_id="house_456"
    )
    result = build_system_prompt("BASE", context)
    
    assert "BASE" in result
    assert "### User Context:" in result
    assert "- Name: Alice" in result
    assert "- User ID: user_123" in result
    assert "- Household ID: house_456" in result
    assert "### Dietary Restrictions" not in result

def test_build_system_prompt_with_preferences():
    prefs = UserPreferences(
        dietary_restrictions=["Vegan"],
        allergies=["Peanuts", "Shellfish"],
        favourite_brands=["Oatly"],
        disliked_items=["Mushrooms"]
    )
    context = UserContext(
        user_id="user_123",
        name="Bob",
        preferences=prefs
    )
    result = build_system_prompt("BASE", context)
    
    assert "### Dietary Restrictions & Preferences:" in result
    assert "- Dietary Restrictions: Vegan" in result
    assert "- Allergies: Peanuts, Shellfish" in result
    assert "- Favourite Brands: Oatly" in result
    assert "- Disliked Items: Mushrooms" in result
    assert "**CRITICAL PREFERENCE INSTRUCTIONS:**" in result
    assert "NEVER suggest, add, or order items that conflict" in result
