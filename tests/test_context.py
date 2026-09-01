import pytest
from jarvis.context import ActiveContext, active_context
from jarvis.command_bus import CommandBus, command_bus

def test_active_context_updates():
    ctx = ActiveContext()
    assert ctx.active_application == "Desktop"
    
    ctx.update_browser_state("https://www.youtube.com/@hasmob002", "hasmob002 - YouTube")
    assert ctx.active_browser_url == "https://www.youtube.com/@hasmob002"
    assert ctx.active_browser_title == "hasmob002 - YouTube"
    assert ctx.active_browser_domain == "www.youtube.com"
    
    ctx.add_turn("user", "Open YouTube and search hasmob002")
    ctx.add_turn("assistant", "Search results displayed.")
    assert len(ctx.conversation_turns) == 2
    
    prompt_str = ctx.format_context_for_prompt()
    assert "www.youtube.com" in prompt_str
    assert "Active Browser Title" in prompt_str

def test_command_bus_queueing():
    bus = CommandBus()
    msg = bus.submit("Open YouTube", source="voice")
    assert msg.source == "voice"
    assert msg.user_request == "Open YouTube"
    assert msg.command_id.startswith("CMD_")

    fetched = bus.get_next(block=False)
    assert fetched is not None
    assert fetched.command_id == msg.command_id
    assert fetched.user_request == "Open YouTube"
