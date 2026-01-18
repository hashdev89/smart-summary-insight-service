#!/usr/bin/env python3
"""Example script demonstrating how to use the Smart Summary & Insight Service API."""
import requests
import json

# Service URL
BASE_URL = "http://localhost:8000/api/v1"

def example_analyze():
    """Example of calling the /analyze endpoint."""
    
    # Example request data
    request_data = {
        "structured_data": {
            "data": {
                "customer_id": "CUST-12345",
                "event_type": "support_ticket",
                "priority": "high",
                "status": "open",
                "created_at": "2024-01-15T10:30:00Z",
                "assigned_to": "support_team_alpha"
            }
        },
        "notes": [
            "Customer reported login issues after system update",
            "Issue persists after password reset attempt",
            "Customer mentioned they are unable to access critical business data",
            "Customer is frustrated and mentioned considering alternative solutions"
        ]
    }
    
    print("Sending analysis request...")
    print(f"Request data:\n{json.dumps(request_data, indent=2)}\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        
        result = response.json()
        
        print("=" * 60)
        print("ANALYSIS RESULT")
        print("=" * 60)
        print(f"\nSummary:\n{result['summary']}\n")
        
        print("Key Insights:")
        for i, insight in enumerate(result['insights'], 1):
            print(f"  {i}. [{insight.get('priority', 'medium').upper()}] {insight['title']}")
            print(f"     {insight['description']}")
            if insight.get('category'):
                print(f"     Category: {insight['category']}")
        
        print("\nSuggested Next Actions:")
        for i, action in enumerate(result['next_actions'], 1):
            print(f"  {i}. [{action['priority'].upper()}] {action['action']}")
            if action.get('rationale'):
                print(f"     Rationale: {action['rationale']}")
        
        print("\nMetadata:")
        metadata = result['metadata']
        print(f"  Confidence Score: {metadata['confidence_score']:.2f}")
        print(f"  Model Version: {metadata['model_version']}")
        if metadata.get('processing_time_ms'):
            print(f"  Processing Time: {metadata['processing_time_ms']:.2f} ms")
        if metadata.get('tokens_used'):
            print(f"  Tokens Used: {metadata['tokens_used']}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the service.")
        print("Make sure the service is running on http://localhost:8000")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")


def example_health_check():
    """Example of calling the health check endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        print("Service is healthy!")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Health check failed: {e}")


if __name__ == "__main__":
    print("Smart Summary & Insight Service - Example Usage\n")
    
    # Check health first
    print("1. Checking service health...")
    example_health_check()
    print("\n")
    
    # Run analysis example
    print("2. Running analysis example...")
    example_analyze()

