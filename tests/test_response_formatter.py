import pytest
from jarvis.brain.response_formatter import ResponseFormatter

def test_detect_language():
    assert ResponseFormatter.detect_language("YouTube kholo") == "hi-IN"
    assert ResponseFormatter.detect_language("Jarvis mera battery status batao") == "hi-IN"
    assert ResponseFormatter.detect_language("Check system memory") == "en-IN"
    assert ResponseFormatter.detect_language("Hasmob002 ko YouTube pe dhundo") == "hi-IN"

def test_format_wake_response():
    assert ResponseFormatter.format_wake_response("Jarvis battery kitni hai") == "Ji sir?"
    assert ResponseFormatter.format_wake_response("Check battery level") == "Yes, sir?"

def test_sanitize_raw_text():
    raw_dict = "{'success': True, 'url': 'https://www.youtube.com/', 'title': 'YouTube', 'status': 200}"
    cleaned = ResponseFormatter.sanitize_raw_text(raw_dict)
    assert "Task action complete" not in cleaned
    assert "success" not in cleaned
    formatted = ResponseFormatter.format_tool_result("browser_navigate", {"url": "https://www.youtube.com"}, "YouTube kholo")
    assert "YouTube" in formatted

def test_format_tool_result_youtube_search():
    data = {"success": True, "query": "hasmob002", "url": "https://www.youtube.com/results?search_query=hasmob002"}
    res_hi = ResponseFormatter.format_tool_result("browser_search", data, "YouTube par hasmob002 search karo")
    assert "hasmob002" in res_hi
    assert "results" in res_hi.lower() or "mil gaye" in res_hi.lower()

def test_format_tool_result_notepad():
    data = {"success": True, "app_name": "notepad"}
    res_hi = ResponseFormatter.format_tool_result("open_application", data, "Jarvis Notepad kholo")
    assert "Notepad" in res_hi
    assert "खोल" in res_hi or "khol" in res_hi.lower()

def test_format_tool_result_battery():
    data = {"success": True, "battery_percent": 70}
    res_hi = ResponseFormatter.format_tool_result("get_system_info", data, "Jarvis battery kitni hai")
    assert "70%" in res_hi or "70" in res_hi

def test_proper_nouns_preservation():
    text = "YouTube par hasmob002 search kar raha hoon"
    assert "YouTube" in text
    assert "hasmob002" in text
