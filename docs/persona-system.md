# Persona System

## Overview

Each AdsPower profile has a persistent persona that influences AI browsing decisions. This makes behavior patterns unique and human-like.

## Persona Schema

```json
{
  "persona_id": "tech_enthusiast_32",
  "profile_id": "adspower_abc123",

  "demographics": {
    "age": 32,
    "gender": "male",
    "location": "suburban",
    "income_bracket": "middle-upper"
  },

  "interests": {
    "primary": ["technology", "gaming", "gadgets"],
    "secondary": ["fitness", "cooking"],
    "brands": ["Apple", "Sony", "Nike"]
  },

  "behavior": {
    "pace": "medium",
    "patience": 0.7,
    "comparison_tendency": "high",
    "reads_reviews": true,
    "checks_prices_elsewhere": true,
    "distraction_tendency": "medium",
    "cart_abandonment_rate": 0.3,
    "scroll_behavior": "thorough",
    "time_on_page": {
      "min_seconds": 15,
      "max_seconds": 120
    }
  },

  "habits": [
    "always checks product specs first",
    "reads top 3 reviews before deciding",
    "compares at least 2 options",
    "often looks at accessories",
    "adds to cart but sometimes abandons",
    "occasionally gets distracted by deals"
  ],

  "avoids": [
    "popup surveys",
    "newsletter signups",
    "chat widgets"
  ],

  "search_style": {
    "query_length": "medium",
    "uses_filters": true,
    "sorts_by": ["price", "rating", "relevance"]
  }
}
```

## Example Personas

### Tech Enthusiast
```json
{
  "persona_id": "tech_enthusiast_32",
  "demographics": {"age": 32, "interests": ["tech", "gaming"]},
  "behavior": {
    "comparison_tendency": "high",
    "reads_reviews": true,
    "patience": 0.8
  },
  "habits": ["checks specs", "compares 3 options", "reads reviews"]
}
```

### Casual Shopper
```json
{
  "persona_id": "casual_shopper_45",
  "demographics": {"age": 45, "interests": ["home", "garden"]},
  "behavior": {
    "comparison_tendency": "low",
    "reads_reviews": false,
    "patience": 0.4,
    "distraction_tendency": "high"
  },
  "habits": ["quick decisions", "impulse adds to cart", "easily distracted"]
}
```

### Bargain Hunter
```json
{
  "persona_id": "bargain_hunter_28",
  "demographics": {"age": 28, "interests": ["fashion", "deals"]},
  "behavior": {
    "comparison_tendency": "very_high",
    "checks_prices_elsewhere": true,
    "patience": 0.9,
    "cart_abandonment_rate": 0.6
  },
  "habits": ["always checks sale section", "compares prices", "waits for deals"]
}
```

## How Persona Influences AI Decisions

### Prompt Injection
```python
def build_decision_prompt(screenshot, context, persona):
    return f"""
You are browsing as this persona:
- Age: {persona['demographics']['age']}
- Interests: {', '.join(persona['interests']['primary'])}
- Behavior: {persona['behavior']['pace']} pace,
  {'reads reviews' if persona['behavior']['reads_reviews'] else 'skips reviews'},
  {'compares options' if persona['behavior']['comparison_tendency'] == 'high' else 'quick decisions'}

Current context:
- URL: {context['url']}
- Goal: Browse and build natural history
- Recent actions: {context['recent_actions']}

What would this persona do next on this page?

Respond in JSON: {{"action": "...", "target": "...", "reasoning": "..."}}
"""
```

### Behavior Modulation
```python
def modulate_timing(action, persona):
    """Adjust timing based on persona patience"""
    base_delay = get_base_delay(action)
    patience = persona['behavior']['patience']

    # Impatient personas act faster
    # Patient personas take more time
    return base_delay * (0.5 + patience)
```

### Decision Influence Examples

| Persona Trait | Influences |
|---------------|------------|
| high comparison_tendency | AI suggests viewing similar products |
| reads_reviews = true | AI scrolls to reviews section |
| distraction_tendency high | AI occasionally clicks deals/banners |
| checks_prices_elsewhere | AI might search product on Google |
| cart_abandonment_rate 0.3 | 30% chance to abandon after adding |

## Persona Persistence

Each AdsPower profile maps to one persona:

```
data/personas/
├── adspower_abc123.json  -> tech_enthusiast_32
├── adspower_def456.json  -> casual_shopper_45
└── adspower_ghi789.json  -> bargain_hunter_28
```

Persona is loaded when session starts:
```python
def start_session(profile_id):
    persona_file = f"data/personas/{profile_id}.json"

    if not exists(persona_file):
        persona = generate_random_persona()
        save_persona(persona_file, persona)
    else:
        persona = load_persona(persona_file)

    return Session(profile_id, persona)
```
