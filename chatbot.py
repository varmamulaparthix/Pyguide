import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from config import (
    PYTHON_KEYWORDS,
    KNOWLEDGE_BASE,
    NON_PYTHON_RESPONSE,
    UNKNOWN_PYTHON_RESPONSE,
    OPENROUTER_MODEL,
    OPENROUTER_TEMPERATURE,
    OPENROUTER_BASE_URL
)

load_dotenv()


PYTHON_ALIASES = {"py", "python", "python3", "py3"}
FOLLOW_UP_TERMS = {"detail", "detailed", "explain", "explanation", "above", "more", "elaborate"}
GREETING_WORDS = {"hi", "hello", "hey", "hii", "hiii", "hola"}

DETAILED_LOCAL_ANSWERS = {
    "python": """[Python — detailed explanation]

Python is a high-level, general-purpose programming language. It is popular with beginners because its syntax is clear and close to English, while still being powerful enough for professional applications.

### Why Python is popular

- **Easy to read:** Python uses simple, clean syntax.
- **Versatile:** It is used for web apps, automation, data science, AI, testing, and scripting.
- **Large library ecosystem:** Packages such as `requests`, `pandas`, and `Django` help developers build projects faster.
- **Cross-platform:** The same code can run on Windows, macOS, and Linux.

### Your first Python program

```python
name = "Vamsi"
print(f"Hello, {name}!")
```

`name` stores text in a variable. `print()` displays a result in the terminal.

Python programs are saved with the `.py` extension and run with:

```bash
python filename.py
```

Start by learning variables, conditions, loops, functions, lists, dictionaries, and file handling.""",
    "module": """[Python modules — detailed explanation]

A **module** is simply a Python file (`.py`) that contains reusable code: functions, classes, variables, or constants. Instead of writing the same code again in every program, you put it in a module and import what you need.

### Built-in modules

Python includes useful modules such as `math`, `random`, and `json`.

```python
import math

print(math.sqrt(16))  # 4.0
print(math.pi)        # 3.141592...
```

`import math` makes the whole module available. Use `math.` before its functions so Python knows where they come from.

### Import one item

```python
from random import randint

number = randint(1, 10)
print(number)
```

This imports only `randint`, so you can call it directly without writing `random.randint`.

### Create your own module

Create `calculator.py`:

```python
def add(a, b):
    return a + b
```

Then, in another file in the same folder:

```python
import calculator

print(calculator.add(2, 3))  # 5
```

Modules keep programs organized, reduce duplicate code, and make code easier to test and reuse."""
}


def _matches_topic(text, topic):
    """Match a topic as a word and allow common plural forms."""
    escaped_topic = re.escape(topic)
    pattern = rf"(?<![a-z]){escaped_topic}(?:s|es)?(?![a-z])"
    return re.search(pattern, text) is not None


def _clean_local_answer(answer):
    """Remove legacy leading emoji markers from local lesson text."""
    return re.sub(r"^[^\w\s]+\s+", "", answer)


def _is_python_question(text):
    """Return True for Python terms, including short forms such as 'py'."""
    words = set(re.findall(r"[a-z0-9_+#.-]+", text))
    if words & PYTHON_ALIASES:
        return True
    return any(_matches_topic(text, keyword) for keyword in PYTHON_KEYWORDS)


def _is_follow_up(text):
    words = set(re.findall(r"[a-z]+", text))
    asks_for_examples = bool(re.search(r"\b\d+\s*(?:example|examples|program|programs)\b", text))
    asks_for_examples = asks_for_examples or bool(words & {"example", "examples", "program", "programs"})
    return bool(words & FOLLOW_UP_TERMS) or asks_for_examples


def _wants_detailed_explanation(text):
    words = set(re.findall(r"[a-z]+", text))
    return bool(words & {"detail", "detailed", "explain", "explanation", "elaborate"})


def _is_greeting(text):
    words = set(re.findall(r"[a-z]+", text))
    return bool(words) and words <= GREETING_WORDS


def _previous_topic(history):
    """Find the most recent known Python topic in the conversation."""
    for message in reversed(history or []):
        if message.get("role") != "user":
            continue
        content = message.get("content", "").lower()
        for keyword in KNOWLEDGE_BASE:
            if _matches_topic(content, keyword):
                return keyword
        if set(re.findall(r"[a-z0-9_+#.-]+", content)) & PYTHON_ALIASES:
            return "python"
    return None


def _python_overview_request(text):
    """Return True only for a direct request to define Python itself."""
    words = set(re.findall(r"[a-z0-9_+#.-]+", text))
    if not words & PYTHON_ALIASES:
        return False
    allowed_words = {
        "what", "is", "are", "python", "python3", "py", "py3", "means",
        "mean", "about", "tell", "me", "the", "a", "an", "in", "detail",
        "detailed", "explain", "explanation",
    }
    return words <= allowed_words


def get_response(user_input, history=None, attached_files=None):
    """
    Hybrid chatbot brain:
    1. Check if question is Python-related
    2. Check local knowledge base for instant answer (smart matching)
    3. If no match, ask OpenRouter AI
    """
    
    user_input_lower = user_input.lower().strip()
    history = history or []
    attached_files = attached_files or []
    follow_up_topic = _previous_topic(history) if _is_follow_up(user_input_lower) else None
    effective_input = f"{follow_up_topic} {user_input_lower}" if follow_up_topic else user_input_lower
    if attached_files:
        effective_input = f"python code {effective_input}"

    if _is_greeting(user_input_lower):
        return "[Hello] I’m PyGuide. Ask me anything about Python—variables, loops, functions, modules, or beginner programs."
    
    # --- Step 1: Domain Filter ---
    is_python = _is_python_question(effective_input)
    
    if not is_python:
        return NON_PYTHON_RESPONSE
    
    # --- Step 2: Knowledge Base Lookup (Smart Matching) ---
    # This prevents "class" from matching inside "metaclass"
    if follow_up_topic == "python" and _wants_detailed_explanation(user_input_lower):
        return DETAILED_LOCAL_ANSWERS["python"]

    if _python_overview_request(effective_input):
        if _wants_detailed_explanation(user_input_lower):
            return DETAILED_LOCAL_ANSWERS["python"]
        return (
            "[Python] Python is a beginner-friendly programming language used for "
            "web development, automation, data science, AI, and more.\n\n"
            "Example:\n```python\nprint(\"Hello, Python!\")\n```"
        )

    for keyword, answer in KNOWLEDGE_BASE.items():
        if _matches_topic(effective_input, keyword):
            # Requests for additional examples should go to the AI with chat context.
            # Detailed explanations have high-quality local lessons available offline.
            if _wants_detailed_explanation(user_input_lower) and keyword in DETAILED_LOCAL_ANSWERS:
                return DETAILED_LOCAL_ANSWERS[keyword]
            if not (follow_up_topic and _is_follow_up(user_input_lower)):
                return _clean_local_answer(answer)
    
    # --- Step 3: OpenRouter AI Fallback ---
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key or api_key == "sk-or-v1-your_actual_key_here":
        return UNKNOWN_PYTHON_RESPONSE
    
    try:
        client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
            timeout=20.0,
            max_retries=0,
        )
        
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Python Learning Assistant named PyGuide. "
                        "You ONLY answer questions related to Python programming. "
                        "If the user asks about anything else (politics, weather, jokes, etc.), "
                        "politely refuse and remind them you only answer Python questions. "
                        "Keep answers beginner-friendly and use markdown formatting. Include a "
                        "simple code example whenever useful. For a request for multiple examples "
                        "or programs, provide every requested example with compact code; otherwise, "
                        "keep the answer under 250 words."
                    )
                },
                *[
                    {"role": message["role"], "content": message["content"]}
                    for message in history[-6:]
                    if message.get("role") in {"user", "assistant"}
                ],
                {"role": "user", "content": user_input}
            ],
            temperature=OPENROUTER_TEMPERATURE
        )
        
        return response.choices[0].message.content
        
    except Exception:
        if follow_up_topic in DETAILED_LOCAL_ANSWERS:
            return (
                "[Service unavailable] Here is a detailed explanation "
                "of the topic you were discussing:\n\n"
                + DETAILED_LOCAL_ANSWERS[follow_up_topic]
            )
        return (
            "[Service unavailable] I couldn't reach the AI service right now. "
            "Please try again in a moment.\n\n"
            + UNKNOWN_PYTHON_RESPONSE
        )
