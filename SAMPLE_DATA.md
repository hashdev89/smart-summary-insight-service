# Sample Data for Testing

## Sample 1: Customer Support Ticket

### Free-Text Notes:
```
Customer reported login issues after system update
Issue persists after password reset attempt
Customer mentioned they are unable to access critical business data
Customer is frustrated and mentioned considering alternative solutions
Multiple support tickets opened in the past week
```

### Structured Data (JSON):
```json
{
  "customer_id": "CUST-12345",
  "event_type": "support_ticket",
  "priority": "high",
  "status": "open",
  "created_at": "2024-01-15T10:30:00Z",
  "assigned_to": "support_team_alpha",
  "ticket_count_week": 3,
  "customer_tier": "enterprise"
}
```

---

## Sample 2: Sales Opportunity

### Free-Text Notes:
```
Prospect showed strong interest in enterprise plan
Budget approved for Q2 2024
Decision maker is CTO, technical evaluation scheduled
Competitor mentioned: CompetitorX
Timeline: 30-45 days for decision
```

### Structured Data (JSON):
```json
{
  "opportunity_id": "OPP-78901",
  "company_name": "TechCorp Inc",
  "deal_size": 50000,
  "stage": "evaluation",
  "probability": 0.65,
  "expected_close_date": "2024-03-15",
  "industry": "technology"
}
```

---

## Sample 3: Product Feedback

### Free-Text Notes:
```
Users reporting slow performance in dashboard
Feature request: Export to Excel functionality
Positive feedback on new mobile app design
Bug reported: Data not syncing between devices
Request for dark mode theme
```

### Structured Data (JSON):
```json
{
  "feedback_type": "mixed",
  "source": "user_survey",
  "response_count": 127,
  "sentiment_score": 0.6,
  "categories": ["performance", "feature_request", "bug_report"],
  "priority_issues": 2
}
```

---

## Sample 4: Simple Test (Minimal Data)

### Free-Text Notes:
```
Customer reported payment processing error
Transaction failed multiple times
```

### Structured Data (JSON):
```json
{
  "customer_id": "12345",
  "transaction_amount": 99.99,
  "error_code": "PAYMENT_FAILED"
}
```

---

## Sample 5: Operations Incident

### Free-Text Notes:
```
Server downtime detected at 2:30 AM
Affected 500+ users
Root cause: Database connection pool exhaustion
Incident resolved at 3:15 AM
Post-mortem scheduled for tomorrow
```

### Structured Data (JSON):
```json
{
  "incident_id": "INC-2024-001",
  "severity": "high",
  "duration_minutes": 45,
  "affected_users": 523,
  "service": "api_gateway",
  "status": "resolved"
}
```

