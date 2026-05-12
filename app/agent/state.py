"""
FarmerAgentState — The state schema for the Farming Assistant agent.

Uses LangGraph's MessagesState (which provides the `messages` key with
the `add_messages` reducer) extended with farming-specific context fields.
"""


from langgraph.graph import MessagesState


class FarmerAgentState(MessagesState):
    """Extended state for the farming assistant agent.
    
    Inherits:
        messages: Annotated[list[AnyMessage], add_messages]
    
    Custom fields:
        user_id: Unique identifier for the farmer (for long-term memory).
        farmer_location: Farmer's location (state/district), loaded from memory.
        farmer_crops: List of crops the farmer grows, loaded from memory.
        summary: Running conversation summary for context compression.
    """
    user_id: str = "default"
    farmer_location: str | None = None
    farmer_crops: list[str] | None = None
    summary: str = ""
