from typing import Optional
from src.agent.models import UserContext


def build_system_prompt(base_prompt: str, context: Optional[UserContext]) -> str:
    """
    Builds a personalized system prompt by appending user context to the base prompt.
    
    Args:
        base_prompt: The base SYSTEM_PROMPT string.
        context: The UserContext model containing user-specific data, or None if anonymous.
        
    Returns:
        The full customized system prompt string.
    """
    if not context:
        return base_prompt
        
    context_lines = [
        "",
        "### User Context:",
        f"- Name: {context.name}",
        f"- User ID: {context.user_id}",
    ]
    
    if context.email:
        context_lines.append(f"- Email: {context.email}")
    if context.phone:
        context_lines.append(f"- Phone: {context.phone}")
        
    context_lines.append(f"- Household ID: {context.household_id if context.household_id else 'None'}")
    context_lines.append(f"- Splitwise Connected: {'Yes' if context.has_splitwise_tokens else 'No'}")
    
    if context.discord_user_id:
        context_lines.append(f"- Discord User ID: {context.discord_user_id}")
        
    context_lines.append(f"- Account Status: {context.account_status}")
    if context.join_date:
        context_lines.append(f"- Join Date: {context.join_date.strftime('%Y-%m-%d')}")
        
    # Handle Preferences
    prefs = context.preferences
    has_prefs = any([
        prefs.dietary_restrictions,
        prefs.allergies,
        prefs.favourite_brands,
        prefs.disliked_items
    ])
    
    if has_prefs:
        context_lines.append("")
        context_lines.append("### Dietary Restrictions & Preferences:")
        if prefs.dietary_restrictions:
            context_lines.append(f"- Dietary Restrictions: {', '.join(prefs.dietary_restrictions)}")
        if prefs.allergies:
            context_lines.append(f"- Allergies: {', '.join(prefs.allergies)}")
        if prefs.favourite_brands:
            context_lines.append(f"- Favourite Brands: {', '.join(prefs.favourite_brands)}")
        if prefs.disliked_items:
            context_lines.append(f"- Disliked Items: {', '.join(prefs.disliked_items)}")
            
        context_lines.append("")
        context_lines.append("**CRITICAL PREFERENCE INSTRUCTIONS:**")
        context_lines.append("- NEVER suggest, add, or order items that conflict with the user's allergies or dietary restrictions.")
        context_lines.append("- When making suggestions, prioritize the user's favourite brands if available.")
        context_lines.append("- Avoid suggesting any disliked items.")
        
    return base_prompt + "\n".join(context_lines) + "\n"
