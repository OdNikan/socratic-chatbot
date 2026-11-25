# Socratic Physics Chatbot with Interactive Simulations

An enhanced physics tutor that uses the Socratic method and provides interactive web simulations for better understanding.

## Features

### 1. **Physics Question Detection**
- Uses **typesafe/jev-1.14** model for structured classification
- Falls back to keyword matching for fast detection
- Falls back to LLM-based classification if JEV is unavailable
- Supports both English and Persian (Farsi) questions

### 2. **Socratic Answer Evaluation**
- Uses **typesafe/jev-1.14** model for structured evaluation
- Ensures responses are in the form of guiding questions
- Prevents direct answers or explanations
- Validates that responses contain multiple questions
- Falls back to pattern matching if JEV is unavailable
- Retries with better prompts if response is not Socratic

### 3. **Interactive Simulations**
Pre-built templates for common physics scenarios:
- **Ball with Acceleration & Velocity**: Demonstrates objects with acceleration but zero speed at a point
- **Projectile Motion**: Shows parabolic trajectories under gravity
- **Bouncing Ball**: Illustrates energy conservation and restitution

The chatbot automatically detects when a question matches a simulation and displays it in the chat.

### 4. **Elegant Web Chat Interface**
- Modern, clean design with gradient backgrounds
- Responsive layout that works on mobile and desktop
- Persian/Farsi support
- Typing indicators
- Message history with timestamps
- Seamless simulation integration

### 5. **RAG (Retrieval-Augmented Generation)**
- Uses CSV-based Q&A pairs for context
- Embedding-based similarity search
- Caching for performance

## Installation

```bash
# Clone or download the repository
cd socratic-physics-chatbot

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your API key
nano .env  # or use any text editor
```

## Requirements

Create a `requirements.txt` file:

```
flask>=2.0.0
openai>=1.0.0
numpy>=1.20.0
pandas>=1.3.0
python-dotenv>=0.19.0
scikit-learn>=1.0.0
```

## Configuration

Create a `.env` file:

```
API_KEY=your_openai_api_key
CSV_FILE=qa_pairs.csv
TOP_K=3
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=deepseek-v4-pro
API_BASE_URL=https://api.gapgpt.ir/v1

# JEV Model Configuration (for physics detection and answer evaluation)
JEV_MODEL=typesafe/jev-1.14
JEV_API_URL=https://api.gapgpt.ir/v1/systemone
```

### JEV Model Usage

The chatbot uses **typesafe/jev-1.14** for:
- **Physics question detection**: Classifies if a question is about physics
- **Answer evaluation**: Validates if responses are in Socratic style

The JEV model is called with structured questions in the format:

```json
{
  "model": "typesafe/jev-1.14",
  "state": {
    "text": "Your input text here"
  },
  "questions": {
    "question1": {
      "type": "noul",
      "instructions": {
        "question": "Your question here"
      }
    }
  }
}
```

If JEV is not available, the system falls back to:
- Keyword matching for physics detection
- Pattern matching for answer evaluation

## Usage

### Web Interface (Recommended)

```bash
python socratic_physics_chatbot.py --web
```

Then open your browser to: http://localhost:5000

### CLI Interface

```bash
python socratic_physics_chatbot.py --cli
```

## Example Questions

Try asking the chatbot about:

1. **Acceleration**: "Can an object have acceleration but zero velocity?"
   - Shows simulation of ball with acceleration in different directions

2. **Projectile Motion**: "What is the path of a thrown ball?"
   - Displays projectile motion simulation

3. **Bouncing**: "Why does a ball bounce lower each time?"
   - Shows bouncing ball with energy loss

4. **General Physics**: "What is Newton's first law?"
   - Guides you through questions to understand the concept

## Simulation Templates

The chatbot includes these pre-built simulations:

### 1. Ball with Acceleration and Velocity
- **Concept**: Object can have acceleration even when velocity is zero
- **Example Question**: "Is it possible to have acceleration but speed = 0?"
- **Features**: Adjustable initial velocity and acceleration in X and Y directions

### 2. Projectile Motion
- **Concept**: Parabolic trajectory under gravity
- **Example Question**: "What happens when you throw a ball at an angle?"
- **Features**: Adjustable launch angle, speed, and gravity

### 3. Bouncing Ball
- **Concept**: Energy conservation and coefficient of restitution
- **Example Question**: "Why does a ball not bounce back to the same height?"
- **Features**: Adjustable drop height, restitution coefficient, and gravity

## Customizing Simulations

You can add more simulation templates by:

1. Adding new HTML templates to the `SIMULATION_TEMPLATES` dictionary
2. Adding trigger keywords in the `SIMULATION_TRIGGERS` dictionary

Example:

```python
SIMULATION_TEMPLATES["new_simulation"] = """
<!DOCTYPE html>
<html>...</html>
"""

SIMULATION_TRIGGERS["new_category"] = {
    'templates': ['new_simulation'],
    'keywords': ['keyword1', 'keyword2']
}
```

## CSV File Format

Create a `qa_pairs.csv` file with physics questions and answers:

```csv
question,answer
"What is acceleration?","Acceleration is the rate of change of velocity."
"What is force?","Force is mass times acceleration."
```

## How It Works

1. **Question Analysis**: When you ask a question, the system:
   - Checks if it's a physics question using keywords and LLM
   - Retrieves similar questions from the CSV database (if available)
   - Determines if any simulations match the question

2. **Response Generation**: The LLM generates a Socratic response:
   - Uses system prompts to ensure Socratic method
   - Includes context from similar questions (RAG)
   - Validates the response is in question form

3. **Simulation Integration**: If a matching simulation is found:
   - The HTML is embedded in the chat
   - You can interact with it directly
   - Parameters can be adjusted in real-time

4. **User Interface**: The web interface:
   - Shows conversation history
   - Displays typing indicators
   - Renders simulations inline
   - Supports both English and Persian

## Troubleshooting

### Common Issues

1. **API Key Not Set**: Make sure your `.env` file has `API_KEY=your_key`
2. **No CSV File**: The system works without CSV, but RAG won't be available
3. **Port Already in Use**: Change the port in the code or use `--port` flag
4. **Simulations Not Showing**: Check if your question matches the trigger keywords

### Debug Mode

For more verbose output:

```python
# In socratic_physics_chatbot.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

To add new features:

1. **New Simulations**: Add to `SIMULATION_TEMPLATES` and `SIMULATION_TRIGGERS`
2. **Better Physics Detection**: Add more keywords to `PHYSICS_KEYWORDS`
3. **Improved Socratic Validation**: Modify `_is_socratic_response()` function
4. **New Models**: Update `.env` with different model names

## License

This project is open source and available for educational use.

## Acknowledgments

- Inspired by the Socratic method of teaching
- Built with Flask, OpenAI API, and modern web technologies
- Designed for physics education and understanding
