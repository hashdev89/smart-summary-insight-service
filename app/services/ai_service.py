"""AI service for LLM interactions with pluggable provider design."""
from typing import Optional, Dict, Any, List
import time
import json
from anthropic import Anthropic
from app.config import settings
from app.services.prompt_builder import PromptBuilder
from app.models.schemas import AnalyzeResponse, Insight, NextAction, Metadata


class AIService:
    """Service for interacting with LLM providers (pluggable design)."""
    
    def __init__(self):
        """Initialize AI service with Claude API client."""
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
        self.prompt_builder = PromptBuilder()
    
    async def analyze(
        self,
        structured_data: Optional[Dict[str, Any]],
        notes: List[str]
    ) -> AnalyzeResponse:
        """
        Analyze structured data and notes using LLM.
        
        Args:
            structured_data: Optional structured JSON data
            notes: List of free-text notes
            
        Returns:
            AnalyzeResponse with summary, insights, actions, and metadata
        """
        start_time = time.time()
        
        # Build prompts with context management
        system_prompt = self.prompt_builder.SYSTEM_PROMPT
        user_prompt = self.prompt_builder.build_user_prompt(structured_data, notes)
        
        # Manage context size - truncate if needed (optimized for speed)
        user_prompt = self.prompt_builder.truncate_if_needed(
            user_prompt,
            max_tokens=6000  # Reduced for faster processing
        )
        
        try:
            # Call Claude API using messages API (newer SDK versions)
            if hasattr(self.client, 'messages'):
                # New messages API
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ]
                )
                # Extract response text - handle different block types safely
                response_text = ""
                for block in message.content:
                    # Use getattr to safely access text attribute (only TextBlock has it)
                    # Type checker may complain, but getattr handles missing attributes safely
                    text_content = getattr(block, 'text', None)  # type: ignore
                    if text_content and isinstance(text_content, str):
                        response_text += text_content
                
                if not response_text:
                    raise AIServiceError("No text content found in API response")
                
                api_response = message
            else:
                # Fallback to completions API (older SDK versions)
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                completion = self.client.completions.create(
                    model=self.model,
                    max_tokens_to_sample=self.max_tokens,
                    temperature=self.temperature,
                    prompt=full_prompt
                )
                response_text = completion.completion
                api_response = completion
            
            # Parse JSON response
            try:
                parsed_response = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from markdown code blocks
                response_text = self._extract_json_from_markdown(response_text)
                parsed_response = json.loads(response_text)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Build response model
            return self._build_response(parsed_response, processing_time_ms, api_response)
            
        except Exception as e:
            # Enhanced error handling
            raise AIServiceError(f"Failed to analyze data: {str(e)}") from e
    
    def _extract_json_from_markdown(self, text: str) -> str:
        """Extract JSON from markdown code blocks if present."""
        import re
        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        # Try to find JSON object directly
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        raise ValueError("Could not extract JSON from response")
    
    def _build_response(
        self,
        parsed: Dict[str, Any],
        processing_time_ms: float,
        api_message: Any
    ) -> AnalyzeResponse:
        """Build AnalyzeResponse from parsed LLM output."""
        # Extract insights
        insights = [
            Insight(
                title=insight.get("title", "Untitled"),
                description=insight.get("description", ""),
                category=insight.get("category"),
                priority=insight.get("priority", "medium")
            )
            for insight in parsed.get("insights", [])
        ]
        
        # Extract next actions
        next_actions = [
            NextAction(
                action=action.get("action", ""),
                priority=action.get("priority", "medium"),
                rationale=action.get("rationale")
            )
            for action in parsed.get("next_actions", [])
        ]
        
        # Build metadata
        # Extract token usage safely (completions API may not have usage info)
        # Try to get it from the response object
        tokens_used = None
        if hasattr(api_message, 'usage'):
            usage = api_message.usage
            if usage:
                tokens_used = getattr(usage, 'input_tokens', 0) + getattr(usage, 'output_tokens', 0)
        elif hasattr(api_message, 'stop_reason'):
            # For completions API, we can estimate tokens (rough: 1 token ≈ 4 chars)
            # This is just an approximation
            pass
        
        metadata = Metadata(
            confidence_score=float(parsed.get("confidence_score", 0.5)),
            model_version=self.model,
            processing_time_ms=processing_time_ms,
            tokens_used=tokens_used,
        )
        
        return AnalyzeResponse(
            summary=parsed.get("summary", "No summary generated"),
            insights=insights,
            next_actions=next_actions,
            metadata=metadata
        )


class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass

