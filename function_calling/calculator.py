from typing import Dict
import json
import math

def get_calculator_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluates a mathematical expression and returns the result. Supports basic math and functions like abs, pow, min, max, round, and math module functions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A mathematical expression to evaluate, e.g. '2 + 2 * 3', 'abs(-5)', 'pow(2, 8)', 'math.sqrt(16)'"
                    }
                },
                "required": ["expression"]
            }
        }
    }

SAFE_FUNCTIONS = {
    "abs": abs,
    "pow": pow,
    "min": min,
    "max": max,
    "round": round,
    # Expose all functions from math module
    "math": math,
    # Optionally, expose math functions directly (e.g., sqrt, sin, cos, etc.)
    **{k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
}

async def calculate(expression: str) -> float:
    """Evaluate a mathematical expression (including abs, pow, math functions) and return the result."""
    try:
        if isinstance(expression, str):
            expression = expression.strip()
            if (expression.startswith('"') and expression.endswith('"')) or \
               (expression.startswith("'") and expression.endswith("'")):
                expression = expression[1:-1]
        # Only allow safe characters and function names
        allowed = set("0123456789+-*/().eE% ,_")
        # Allow letters for function names and math module
        allowed.update("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        if not set(expression).issubset(allowed):
            raise ValueError("Expression contains invalid characters")
        # Evaluate the expression with safe functions
        result = eval(expression, {"__builtins__": None}, SAFE_FUNCTIONS)
        return float(result)
    except Exception as e:
        raise ValueError(f"Calculator error: {str(e)}")