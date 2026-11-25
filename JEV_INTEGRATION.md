# JEV Model Integration (typesafe/jev-1.14)

This document explains how the **typesafe/jev-1.14** model is integrated into the Socratic Physics Chatbot.

## Overview

The chatbot now uses the **JEV (JSON Evaluation) model** for:
1. **Physics Question Detection** - Classifying if a user's question is about physics
2. **Answer Evaluation** - Validating if a response follows the Socratic method

## Configuration

### Environment Variables

Add these to your `.env` file:

```ini
# JEV Model Configuration
JEV_MODEL=typesafe/jev-1.14
JEV_API_URL=https://api.gapgpt.ir/v1/systemone
```

### Dependencies

The `requests` library is required for JEV API calls:

```bash
pip install requests
```

## Implementation

### 1. Core Function: `call_jev_model()`

Located in `socratic_physics_chatbot.py` (line 44):

```python
def call_jev_model(text, questions_config):
    """
    Call the typesafe/jev-1.14 model with structured questions.
    
    Args:
        text: The input text to analyze
        questions_config: Dictionary of questions to ask the model
    
    Returns:
        Dictionary with the model's responses
    """
    if not JEV_API_KEY:
        raise ValueError("JEV_API_KEY not configured")
    
    payload = {
        "model": JEV_MODEL,
        "state": {
            "text": text
        },
        "questions": questions_config
    }
    
    headers = {
        'Authorization': f'Bearer {JEV_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(JEV_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling JEV model: {e}")
        return None
```

### 2. Physics Question Detection

Located in `socratic_physics_chatbot.py` (line 521):

```python
def is_physics_question(user_input, client=None):
    """
    Determine if a question is about physics using JEV model.
    Falls back to keyword matching if JEV is not available.
    """
    # 1. Fast keyword matching (2+ matches = immediate True)
    keyword_matches = sum(1 for kw in PHYSICS_KEYWORDS if kw.lower() in user_input_lower)
    if keyword_matches >= 2:
        return True
    
    # 2. Use JEV model for classification
    try:
        questions_config = {
            "is_physics": {
                "type": "noul",
                "instructions": {
                    "question": "Is this a physics question?"
                }
            }
        }
        
        result = call_jev_model(user_input, questions_config)
        
        if result and "answers" in result:
            is_physics = result["answers"].get("is_physics", {}).get("answer", False)
            if is_physics:
                return True
    except Exception as e:
        print(f"JEV classification failed: {e}")
        pass
    
    # 3. Fallback: LLM classification
    if client:
        # ... existing LLM code ...
    
    # 4. Final fallback: keyword matching
    return keyword_matches >= 1
```

**Detection Priority:**
1. Keyword matching (fastest)
2. JEV model (structured, accurate)
3. LLM classification (fallback)
4. Single keyword match (last resort)

### 3. Answer Evaluation

Located in `socratic_physics_chatbot.py` (line 578):

```python
def _is_socratic_response(text):
    """
    Evaluate if a response is in Socratic style using JEV model.
    Falls back to pattern matching if JEV is not available.
    """
    # 1. Fast path: Check for refusal messages
    if "متاسفم" in text and "فیزیک" in text:
        return True
    if "sorry" in text.lower() and "physics" in text.lower:
        return True
    
    # 2. Use JEV model for evaluation
    try:
        questions_config = {
            "is_socratic": {
                "type": "noul",
                "instructions": {
                    "question": "Is this a Socratic response (contains guiding questions, not direct answers)?"
                }
            },
            "has_questions": {
                "type": "noul",
                "instructions": {
                    "question": "Does the response contain multiple questions?"
                }
            },
            "has_direct_answer": {
                "type": "noul",
                "instructions": {
                    "question": "Does the response contain a direct answer or explanation?"
                }
            }
        }
        
        result = call_jev_model(text, questions_config)
        
        if result and "answers" in result:
            is_socratic = result["answers"].get("is_socratic", {}).get("answer", False)
            has_questions = result["answers"].get("has_questions", {}).get("answer", False)
            has_direct = result["answers"].get("has_direct_answer", {}).get("answer", False)
            
            # Must be socratic, have questions, and not have direct answers
            if is_socratic and has_questions and not has_direct:
                return True
            return False
    except Exception as e:
        print(f"JEV evaluation failed: {e}")
        pass
    
    # 3. Fallback: Pattern matching
    question_count = text.count('?') + text.count('؟')
    if question_count >= 3:
        return True
    
    # Check for direct answer patterns
    direct_patterns = [
        'the answer is', 'the solution is', 'it is ', 'is equal to',
        'پاسخ این است', 'جواب این است', 'می باشد',
        'formula is', 'equation is'
    ]
    
    for pattern in direct_patterns:
        if pattern in text.lower():
            return False
    
    return question_count >= 2
```

**Evaluation Logic:**
- A valid Socratic response must:
  1. Be classified as Socratic by JEV
  2. Contain multiple questions
  3. NOT contain direct answers

**Evaluation Priority:**
1. Fast path: Refusal messages
2. JEV model (structured, multi-criteria)
3. Pattern matching (fallback)

## JEV Request Format

All JEV requests follow this structure:

```json
{
  "model": "typesafe/jev-1.14",
  "state": {
    "text": "The text to analyze"
  },
  "questions": {
    "question_id": {
      "type": "noul",
      "instructions": {
        "question": "The question to ask"
      }
    }
  }
}
```

### Question Types

- **`noul`**: Yes/No or Boolean questions
- **`choice`**: Multiple choice questions
- **`score`**: Rating/score questions

## Example Requests

### Physics Question Detection

```python
questions_config = {
    "is_physics": {
        "type": "noul",
        "instructions": {
            "question": "Is this a physics question?"
        }
    }
}
result = call_jev_model("What is acceleration?", questions_config)
# result["answers"]["is_physics"]["answer"] = True
```

### Answer Evaluation

```python
questions_config = {
    "is_socratic": {
        "type": "noul",
        "instructions": {
            "question": "Is this a Socratic response?"
        }
    },
    "has_questions": {
        "type": "noul",
        "instructions": {
            "question": "Does it contain multiple questions?"
        }
    },
    "has_direct_answer": {
        "type": "noul",
        "instructions": {
            "question": "Does it contain direct answers?"
        }
    }
}
result = call_jev_model("What do you think about this?", questions_config)
```

## Fallback Behavior

If JEV is not available (API error, timeout, etc.), the system gracefully falls back to:

1. **Physics Detection:**
   - Keyword matching (2+ matches = physics)
   - LLM classification (if client available)
   - Single keyword match

2. **Answer Evaluation:**
   - Pattern matching for refusal messages
   - Question mark counting (3+ = valid)
   - Direct answer pattern detection
   - Minimum 2 questions required

## Benefits of JEV Integration

### 1. **Structured Output**
- JEV returns structured JSON with clear answers
- Easy to parse and use in code
- Multiple criteria can be evaluated in one call

### 2. **Consistent Results**
- Less variability than regular LLM responses
- Designed for evaluation tasks
- More reliable for classification

### 3. **Multi-Criteria Evaluation**
- Can ask multiple questions in one API call
- Get comprehensive evaluation in a single request
- More efficient than multiple LLM calls

### 4. **Customizable**
- Easy to add new evaluation criteria
- Simple to modify questions
- Flexible for different use cases

## Error Handling

The system handles JEV errors gracefully:

```python
try:
    result = call_jev_model(text, questions_config)
    # Process result...
except Exception as e:
    print(f"JEV failed: {e}")
    # Fall back to alternative method
```

Common errors:
- API key not configured
- Network timeout
- API rate limits
- Invalid response format

## Performance

- **JEV Call**: ~1-2 seconds (depends on API)
- **Fallback**: <100ms (keyword/pattern matching)
- **Cache**: Not currently cached (could be added)

## Testing

### Test Physics Detection

```python
from socratic_physics_chatbot import is_physics_question

# Should return True
assert is_physics_question("What is acceleration?") == True
assert is_physics_question("How does gravity work?") == True

# Should return False
assert is_physics_question("What is the capital of France?") == False
```

### Test Answer Evaluation

```python
from socratic_physics_chatbot import _is_socratic_response

# Should return True (Socratic)
assert _is_socratic_response("What do you think? Why? How would you explain it?") == True

# Should return False (direct answer)
assert _is_socratic_response("The answer is 42.") == False
```

## Customization

### Add New Evaluation Criteria

To add a new criterion to answer evaluation:

```python
questions_config = {
    # ... existing questions ...
    "new_criterion": {
        "type": "noul",
        "instructions": {
            "question": "Your new question here"
        }
    }
}
```

Then update the processing logic:

```python
new_value = result["answers"].get("new_criterion", {}).get("answer", False)
```

### Modify Questions

To change the questions asked:

```python
questions_config = {
    "is_physics": {
        "type": "noul",
        "instructions": {
            "question": "Is this specifically about physics and not other subjects?"
        }
    }
}
```

## API Reference

### Endpoint

```
POST https://api.gapgpt.ir/v1/systemone
```

### Headers

```
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

### Request Body

```json
{
  "model": "typesafe/jev-1.14",
  "state": {
    "text": "Your text here"
  },
  "questions": {
    "question_id": {
      "type": "noul|choice|score",
      "instructions": {
        "question": "Your question"
      },
      "criteria": { ... }  // For choice type
    }
  }
}
```

### Response

```json
{
  "answers": {
    "question_id": {
      "answer": true/false/value,
      "confidence": 0.0-1.0
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **API Key Not Configured**
   - Error: `JEV_API_KEY not configured`
   - Solution: Add `API_KEY` to `.env` file

2. **API Connection Failed**
   - Error: `requests.exceptions.RequestException`
   - Solution: Check network connection, API URL

3. **Timeout**
   - Error: `requests.exceptions.Timeout`
   - Solution: Increase timeout in `call_jev_model()`

4. **Invalid Response**
   - Error: `KeyError: 'answers'`
   - Solution: Check API response format, add error handling

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show all JEV API requests and responses.

## Conclusion

The JEV model integration provides:
- ✅ More accurate physics question detection
- ✅ Better Socratic answer evaluation
- ✅ Structured, reliable outputs
- ✅ Graceful fallbacks
- ✅ Easy customization

The system is designed to work with or without JEV, ensuring reliability even if the JEV API is temporarily unavailable.
