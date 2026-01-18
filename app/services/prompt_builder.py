"""Thoughtful prompt construction for LLM interactions."""
from typing import Optional, Dict, Any, List
from app.config import settings


class PromptBuilder:
    """Builds structured prompts for LLM analysis with context management."""
    
    # System prompt template - optimized for speed
    SYSTEM_PROMPT = """You are a business analyst. Analyze the data and return JSON only:

{
  "summary": "2-3 sentence summary",
  "insights": [{"title": "brief", "description": "concise", "category": "type", "priority": "high|medium|low"}],
  "next_actions": [{"action": "brief action", "priority": "high|medium|low", "rationale": "short reason"}],
  "confidence_score": 0.0-1.0
}

Be concise and actionable. Prioritize by importance."""

    @staticmethod
    def build_user_prompt(
        structured_data: Optional[Dict[str, Any]],
        notes: List[str]
    ) -> str:
        """
        Constructs a well-structured user prompt with proper context organization.
        
        Args:
            structured_data: Optional structured JSON data
            notes: List of free-text notes
            
        Returns:
            Formatted prompt string
        """
        parts = []
        
        # Add structured data section if present (more compact)
        if structured_data and structured_data.get("data"):
            parts.append("## Data")
            parts.append(_format_json_compact(structured_data["data"]))
        
        # Add notes section (more compact)
        if notes:
            parts.append("## Notes")
            for note in notes:
                parts.append(f"- {note.strip()}")
        
        # Add analysis instructions (simplified)
        parts.append("\nAnalyze and return JSON only.")
        
        return "\n".join(parts)
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters for English text).
        Used for context size management.
        """
        return len(text) // 4
    
    @staticmethod
    def truncate_if_needed(text: str, max_tokens: int = 8000) -> str:
        """
        Truncates text if it exceeds token limit to manage context size.
        Preserves structure by truncating from the middle.
        """
        estimated_tokens = PromptBuilder.estimate_tokens(text)
        
        if estimated_tokens <= max_tokens:
            return text
        
        # Truncate from middle, preserving beginning and end
        max_chars = max_tokens * 4
        half = max_chars // 2
        
        return (
            text[:half] + 
            "\n\n[... content truncated for length ...]\n\n" + 
            text[-half:]
        )


def _format_json_compact(data: Dict[str, Any], indent: int = 0) -> str:
    """Format JSON in a compact but readable way."""
    import json
    return json.dumps(data, indent=2, ensure_ascii=False)

