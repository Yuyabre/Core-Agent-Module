from src.agent.tools import AGENT_TOOLS

def test_agent_tools_exist():
    assert len(AGENT_TOOLS) == 16

def test_tool_schemas_valid():
    for tool in AGENT_TOOLS:
        assert tool.name
        assert tool.description
