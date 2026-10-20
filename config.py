# ============================================
# CONFIGURATION FILE
# ============================================

# --- App Settings ---
APP_TITLE = "Python Learning Assistant"
APP_ICON = "<>"
APP_DESCRIPTION = "Welcome! Ask me anything about Python programming."
PAGE_LAYOUT = "centered"

# --- Domain Filter ---
PYTHON_KEYWORDS = [
    "python", "variable", "loop", "function", "list", "tuple",
    "dictionary", "dict", "string", "int", "float", "class",
    "object", "oop", "if", "else", "for", "while", "def",
    "return", "import", "module", "pip", "install", "error",
    "bug", "debug", "syntax", "indentation", "array", "set",
    "print", "input", "code", "program", "script", "method",
    "inheritance", "exception", "try", "except", "file", "read",
    "write", "append", "lambda", "map", "filter", "comprehension",
    "recursion", "iterator", "generator", "decorator", "module",
    "package", "library", "framework", "api", "json", "csv",
    "database", "sql", "algorithm", "data structure", "conditional",
    "if-else", "elif", "statement", "condition", "index", "slice",
    "format", "enumerate", "polymorphism", "encapsulation", "monkey", "patching", "patch", "mock", "unittest"
]

# --- Knowledge Base ---
KNOWLEDGE_BASE = {
    "variable": "📦 **Variable**: A variable is like a labeled box that stores data.\n\nExample: `x = 5` stores the number 5 in a box named `x`.",
    
    "loop": "🔄 **Loop**: A loop repeats code multiple times.\n\n- `for` loop: repeats for each item in a sequence\n- `while` loop: repeats as long as a condition is true",
    
    "function": "⚙️ **Function**: A reusable block of code that performs a specific task.\n\nExample:\n```python\ndef greet(name):\n    return f\"Hello, {name}!\"\n```",
    
    "list": "📋 **List**: An ordered, changeable collection of items.\n\nExample: `fruits = ['apple', 'banana', 'cherry']`",
    
    "tuple": "📦 **Tuple**: Like a list, but cannot be changed after creation (immutable).\n\nExample: `coordinates = (10, 20)`",
    
    "dict": "🗂️ **Dictionary**: Stores data as key-value pairs.\n\nExample: `student = {'name': 'Ravi', 'age': 20}`",
    
    "class": "🏗️ **Class**: A blueprint for creating objects in Object-Oriented Programming (OOP).\n\nExample:\n```python\nclass Dog:\n    def bark(self):\n        print(\"Woof!\")\n```",
    
    "inheritance": "🧬 **Inheritance**: When a class gets properties and methods from another class.\n\nExample:\n```python\nclass Animal:\n    def speak(self):\n        pass\n\nclass Dog(Animal):\n    def speak(self):\n        return \"Woof!\"\n```",
    
    "exception": "⚠️ **Exception**: An error that occurs during program execution.\n\nUse `try` and `except` to handle errors gracefully:\n```python\ntry:\n    result = 10 / 0\nexcept ZeroDivisionError:\n    print(\"Cannot divide by zero!\")\n```",
    
    "lambda": "λ **Lambda Function**: A small, anonymous function written in one line.\n\nExample:\n```python\nsquare = lambda x: x ** 2\nprint(square(5))  # Output: 25\n```\n\nUseful for short operations where defining a full function is unnecessary.",
    
    "recursion": "🔄 **Recursion**: When a function calls itself to solve a problem.\n\nExample — factorial:\n```python\ndef factorial(n):\n    if n == 1:\n        return 1\n    return n * factorial(n - 1)\n\nprint(factorial(5))  # Output: 120\n```",
    
    "comprehension": "⚡ **List Comprehension**: A concise way to create lists.\n\nExample:\n```python\n# Traditional way\nsquares = []\nfor x in range(5):\n    squares.append(x**2)\n\n# List comprehension\nsquares = [x**2 for x in range(5)]\nprint(squares)  # [0, 1, 4, 9, 16]\n```",
    
    "decorator": "🎁 **Decorator**: A function that modifies another function's behavior.\n\nExample:\n```python\ndef my_decorator(func):\n    def wrapper():\n        print(\"Before function\")\n        func()\n        print(\"After function\")\n    return wrapper\n\n@my_decorator\ndef say_hello():\n    print(\"Hello!\")\n\nsay_hello()\n```",
    
    "file": "📁 **File Handling**: Reading and writing files in Python.\n\nExample:\n```python\n# Writing to a file\nwith open('data.txt', 'w') as f:\n    f.write('Hello, Python!')\n\n# Reading from a file\nwith open('data.txt', 'r') as f:\n    content = f.read()\n    print(content)\n```",
    
    "string": "🔤 **String**: A sequence of characters (text) in Python.\n\nExample:\n```python\nname = \"Python\"\nprint(name.upper())      # PYTHON\nprint(name.lower())      # python\nprint(len(name))         # 6\nprint(name[0])           # P (indexing)\n```",
    
    "set": "🎯 **Set**: An unordered collection of unique items.\n\nExample:\n```python\nfruits = {'apple', 'banana', 'apple', 'cherry'}\nprint(fruits)  # {'apple', 'banana', 'cherry'} — duplicates removed\n\n# Set operations\na = {1, 2, 3}\nb = {3, 4, 5}\nprint(a & b)  # Intersection: {3}\nprint(a | b)  # Union: {1, 2, 3, 4, 5}\n```",
    
    "if-else": "🔄 **Conditional Statements**: Making decisions in code using `if`, `elif`, and `else`.\n\nExample:\n```python\nmarks = 75\n\nif marks >= 90:\n    print(\"Grade A\")\nelif marks >= 70:\n    print(\"Grade B\")\nelse:\n    print(\"Grade C\")\n```",
    
    "module": "📦 **Module**: A Python file containing functions and variables that you can reuse.\n\nExample:\n```python\n# math is a built-in module\nimport math\nprint(math.sqrt(16))   # 4.0\nprint(math.pi)         # 3.14159...\n\n# Import specific function\nfrom random import randint\nprint(randint(1, 10))  # Random number between 1 and 10\n```",
    
    "json": "📋 **JSON Handling**: Python can read and write JSON files easily.\n\nExample:\n```python\nimport json\n\n# Python dictionary to JSON string\ndata = {\"name\": \"Ravi\", \"age\": 20}\njson_string = json.dumps(data)\nprint(json_string)\n\n# JSON string back to Python dictionary\nparsed = json.loads(json_string)\nprint(parsed[\"name\"])  # Ravi\n```",
    
    "pip": "📥 **PIP**: Python's package manager. It installs external libraries.\n\nCommon commands:\n```bash\npip install numpy          # Install a package\npip install -r requirements.txt  # Install from file\npip list                   # Show installed packages\npip uninstall numpy        # Remove a package\n```",
    
    "generator": "⚡ **Generator**: A function that returns an iterator using `yield` instead of `return`. Memory-efficient for large data.\n\nExample:\n```python\ndef count_up_to(n):\n    count = 1\n    while count <= n:\n        yield count\n        count += 1\n\nfor num in count_up_to(5):\n    print(num)  # 1, 2, 3, 4, 5\n```",
    
    "map": "🗺️ **map() and filter()**: Built-in functions for processing collections.\n\nExample:\n```python\n# map: apply function to every item\nnumbers = [1, 2, 3, 4]\nsquares = list(map(lambda x: x**2, numbers))\nprint(squares)  # [1, 4, 9, 16]\n\n# filter: keep items that match condition\nevens = list(filter(lambda x: x % 2 == 0, numbers))\nprint(evens)    # [2, 4]\n```",
    
    "try": "🛡️ **Try-Except**: Handling errors gracefully so your program doesn't crash.\n\nExample:\n```python\ntry:\n    number = int(input(\"Enter a number: \"))\n    result = 10 / number\n    print(f\"Result: {result}\")\nexcept ValueError:\n    print(\"That's not a valid number!\")\nexcept ZeroDivisionError:\n    print(\"Cannot divide by zero!\")\nfinally:\n    print(\"This always runs.\")\n```",
    
    "oop": "🏛️ **OOP (Object-Oriented Programming)**: Programming using classes and objects.\n\nKey concepts:\n- **Class**: Blueprint (like a car design)\n- **Object**: Instance (like your actual car)\n- **Encapsulation**: Bundling data and methods\n- **Inheritance**: Reusing parent class features\n- **Polymorphism**: Same method, different behavior\n\nExample:\n```python\nclass Animal:\n    def speak(self):\n        pass\n\nclass Dog(Animal):\n    def speak(self):\n        return \"Woof!\"\n\nclass Cat(Animal):\n    def speak(self):\n        return \"Meow!\"\n\nfor animal in [Dog(), Cat()]:\n    print(animal.speak())\n```",
}

# --- Response Messages ---
NON_PYTHON_RESPONSE = "This assistant is focused on Python programming. Ask about Python code, concepts, errors, libraries, or an attached Python file."
UNKNOWN_PYTHON_RESPONSE = "I understand this is a Python question, but I do not have a local answer for it yet. Try asking about variables, loops, functions, lists, tuples, dictionaries, classes, inheritance, or exceptions."

# --- OpenRouter API Settings ---
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
OPENROUTER_TEMPERATURE = 0.3
