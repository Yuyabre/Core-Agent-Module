from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# --- Schemas ---

class GetInventorySnapshotInput(BaseModel):
    dish: Optional[str] = Field(None, description="Optional name of a dish to filter inventory for (e.g., 'pasta').")
    search: Optional[str] = Field(None, description="Optional keyword search to filter items.")

class InventoryItemInput(BaseModel):
    name: str = Field(..., description="Name of the item")
    quantity: float = Field(..., description="Quantity to add")
    unit: str = Field(..., description="Unit of measurement (e.g., 'kg', 'liters', 'pieces')")
    category: str = Field(..., description="Category (e.g., 'produce', 'dairy')")
    shared: bool = Field(True, description="Whether this item is shared with the household")

class AddInventoryItemsInput(BaseModel):
    items: List[InventoryItemInput] = Field(..., description="List of items to add to inventory")

class UpdateInventoryItemInput(BaseModel):
    item_id: str = Field(..., description="The ID or exact name of the item to update")
    quantity: Optional[float] = Field(None, description="New quantity")
    threshold: Optional[float] = Field(None, description="New low-stock threshold")
    unit: Optional[str] = Field(None, description="New unit of measurement")
    category: Optional[str] = Field(None, description="New category")
    notes: Optional[str] = Field(None, description="Additional notes")

class OrderItemInput(BaseModel):
    name: str = Field(..., description="Name of the item to order")
    quantity: float = Field(..., description="Quantity needed")

class PlaceOrderInput(BaseModel):
    items: List[OrderItemInput] = Field(..., description="List of items to order")

class GetRecentOrdersInput(BaseModel):
    limit: int = Field(5, description="Maximum number of recent orders to fetch")

class GetOrderEtaInput(BaseModel):
    order_id: str = Field(..., description="The ID of the order")

class GetGroupOrderStatusInput(BaseModel):
    order_id: str = Field(..., description="The ID of the pending group order")

class CreateSplitwiseExpenseInput(BaseModel):
    amount: float = Field(..., description="The total amount of the expense")
    description: str = Field(..., description="Description of the expense")
    participant_names: List[str] = Field(..., description="Names of housemates involved in the split")

class GetSplitwiseExpensesInput(BaseModel):
    limit: int = Field(5, description="Maximum number of expenses to retrieve")

class UpdateUserPreferencesInput(BaseModel):
    add_dietary_restrictions: List[str] = Field(default_factory=list, description="Dietary restrictions to add")
    remove_dietary_restrictions: List[str] = Field(default_factory=list, description="Dietary restrictions to remove")
    add_allergies: List[str] = Field(default_factory=list, description="Allergies to add")
    remove_allergies: List[str] = Field(default_factory=list, description="Allergies to remove")
    add_brands: List[str] = Field(default_factory=list, description="Favourite brands to add")
    remove_brands: List[str] = Field(default_factory=list, description="Favourite brands to remove")
    add_dislikes: List[str] = Field(default_factory=list, description="Disliked items to add")
    remove_dislikes: List[str] = Field(default_factory=list, description="Disliked items to remove")

class GetHousematesInput(BaseModel):
    include_contact_info: bool = Field(False, description="Whether to include phone numbers/emails")

class SendDiscordMessageInput(BaseModel):
    message: str = Field(..., description="The message content to send to the household Discord channel")

class CheckDiscordMessageResponsesInput(BaseModel):
    context_id: str = Field(..., description="The context ID of the message to check responses for")

class SendWhatsappMessageInput(BaseModel):
    message: str = Field(..., description="The message content")
    target: str = Field(..., description="Target: 'household' or a specific phone number")


# --- Tools ---

@tool("get_inventory_snapshot", args_schema=GetInventorySnapshotInput)
def get_inventory_snapshot(dish: Optional[str] = None, search: Optional[str] = None) -> Dict[str, Any]:
    """Fetch current stock. Use dish or search keyword to filter."""
    return {"status": "success", "items": [], "notes": "Dummy implementation"}

@tool("add_inventory_items", args_schema=AddInventoryItemsInput)
def add_inventory_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Add or increment items in the inventory."""
    return {"status": "success", "added_count": len(items)}

@tool("update_inventory_item", args_schema=UpdateInventoryItemInput)
def update_inventory_item(item_id: str, quantity: Optional[float] = None, threshold: Optional[float] = None, 
                          unit: Optional[str] = None, category: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
    """Edit a single inventory item's details."""
    return {"status": "success", "updated_item": item_id}

@tool("check_low_stock")
def check_low_stock() -> Dict[str, Any]:
    """Return all items currently below their required threshold."""
    return {"status": "success", "low_stock_items": []}

@tool("place_order", args_schema=PlaceOrderInput)
def place_order(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a grocery order. Triggers a group order if shared items are detected."""
    return {"status": "success", "is_group_order": False, "order_id": "dummy_order_id"}

@tool("get_recent_orders", args_schema=GetRecentOrdersInput)
def get_recent_orders(limit: int = 5) -> Dict[str, Any]:
    """Fetch recent order history."""
    return {"status": "success", "orders": []}

@tool("get_order_eta", args_schema=GetOrderEtaInput)
def get_order_eta(order_id: str) -> Dict[str, Any]:
    """Get the estimated time of arrival for a specific order."""
    return {"status": "success", "order_id": order_id, "eta": "20 minutes"}

@tool("get_group_order_status", args_schema=GetGroupOrderStatusInput)
def get_group_order_status(order_id: str) -> Dict[str, Any]:
    """Check housemate responses (yes/no) for a pending group order."""
    return {"status": "success", "order_id": order_id, "responses": {}}

@tool("create_splitwise_expense", args_schema=CreateSplitwiseExpenseInput)
def create_splitwise_expense(amount: float, description: str, participant_names: List[str]) -> Dict[str, Any]:
    """Log a cost split to Splitwise for the specified housemates."""
    return {"status": "success", "expense_id": "dummy_expense_id"}

@tool("get_splitwise_expenses", args_schema=GetSplitwiseExpensesInput)
def get_splitwise_expenses(limit: int = 5) -> Dict[str, Any]:
    """Retrieve recent shared expenses from Splitwise."""
    return {"status": "success", "expenses": []}

@tool("get_user_info")
def get_user_info() -> Dict[str, Any]:
    """Fetch the current user's full profile."""
    return {"status": "success", "user": {"name": "Dummy User"}}

@tool("update_user_preferences", args_schema=UpdateUserPreferencesInput)
def update_user_preferences(
    add_dietary_restrictions: List[str] = [], remove_dietary_restrictions: List[str] = [],
    add_allergies: List[str] = [], remove_allergies: List[str] = [],
    add_brands: List[str] = [], remove_brands: List[str] = [],
    add_dislikes: List[str] = [], remove_dislikes: List[str] = []
) -> Dict[str, Any]:
    """Add or remove dietary restrictions, allergies, favourite brands, or disliked items."""
    return {"status": "success", "message": "Preferences updated (dummy)"}

@tool("get_housemates", args_schema=GetHousematesInput)
def get_housemates(include_contact_info: bool = False) -> Dict[str, Any]:
    """List household members and optionally their contact info."""
    return {"status": "success", "housemates": []}

@tool("send_discord_message", args_schema=SendDiscordMessageInput)
def send_discord_message(message: str) -> Dict[str, Any]:
    """Send a message to the household Discord channel. Always prefer this over WhatsApp."""
    return {"status": "success", "message_id": "dummy_msg_id", "context_id": "dummy_ctx_id"}

@tool("check_discord_message_responses", args_schema=CheckDiscordMessageResponsesInput)
def check_discord_message_responses(context_id: str) -> Dict[str, Any]:
    """Poll for housemate responses to a previously sent Discord message."""
    return {"status": "success", "context_id": context_id, "responses": {}}

@tool("send_whatsapp_message", args_schema=SendWhatsappMessageInput)
def send_whatsapp_message(message: str, target: str) -> Dict[str, Any]:
    """Fallback tool: send a message via WhatsApp to the household or a specific number."""
    return {"status": "success", "message_id": "dummy_wa_id"}

# Export all tools as a list
AGENT_TOOLS = [
    get_inventory_snapshot,
    add_inventory_items,
    update_inventory_item,
    check_low_stock,
    place_order,
    get_recent_orders,
    get_order_eta,
    get_group_order_status,
    create_splitwise_expense,
    get_splitwise_expenses,
    get_user_info,
    update_user_preferences,
    get_housemates,
    send_discord_message,
    check_discord_message_responses,
    send_whatsapp_message
]
