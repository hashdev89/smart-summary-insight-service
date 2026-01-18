"""Tests for prompt builder."""
from app.services.prompt_builder import PromptBuilder


def test_prompt_builder_with_structured_data():
    """Test prompt building with structured data."""
    builder = PromptBuilder()
    
    structured_data = {"data": {"customer_id": "123", "status": "active"}}
    notes = ["Customer reported issue", "Follow up needed"]
    
    prompt = builder.build_user_prompt(structured_data, notes)
    
    assert "Structured Data" in prompt
    assert "Free-Text Notes" in prompt
    assert "customer_id" in prompt
    assert "Customer reported issue" in prompt


def test_prompt_builder_without_structured_data():
    """Test prompt building without structured data."""
    builder = PromptBuilder()
    
    notes = ["Just a note"]
    prompt = builder.build_user_prompt(None, notes)
    
    assert "Free-Text Notes" in prompt
    assert "Just a note" in prompt


def test_token_estimation():
    """Test token estimation."""
    builder = PromptBuilder()
    
    text = "This is a test " * 100  # ~1500 characters
    tokens = builder.estimate_tokens(text)
    
    assert tokens > 0
    assert tokens < len(text)  # Should be roughly 1/4 of characters


def test_truncation():
    """Test text truncation."""
    builder = PromptBuilder()
    
    long_text = "A" * 100000  # Very long text
    truncated = builder.truncate_if_needed(long_text, max_tokens=100)
    
    assert len(truncated) < len(long_text)
    assert "truncated" in truncated.lower()

