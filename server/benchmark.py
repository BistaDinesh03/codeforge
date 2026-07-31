"""Quick benchmark script for model loading and inference speed."""

import time
import sys
sys.path.insert(0, ".")

from app.services.model_manager import ModelManager
from app.services.inference import chat, generate_code

manager = ModelManager()

# List available models
print("Available models:")
for model in manager.list_available_models():
    print(f"  - {model.name} ({model.size_mb} MB)")
print()

# Load model
model_name = "Qwen2.5-Coder-1.5B-Instruct-Q4_K_M"
print(f"Loading model: {model_name}")
start = time.time()

try:
    manager.load_model(model_name)
    load_time = time.time() - start
    print(f"Loaded in {load_time:.1f} seconds")
except Exception as e:
    print(f"Failed to load: {e}")
    sys.exit(1)

# Test 1: Simple chat
print("\n--- Test 1: Simple chat ---")
start = time.time()
result = chat("Write a function to add two numbers in Python.", max_tokens=100)
print(f"Response ({result.tokens_per_second:.1f} tokens/sec):")
print(result.text[:200])
print(f"Time: {result.time_seconds:.1f}s, Tokens: {result.tokens_generated}")

# Test 2: Code generation
print("\n--- Test 2: Code generation ---")
start = time.time()
result = generate_code("Sort a list of dictionaries by a key", language="python")
print(f"Response ({result.tokens_per_second:.1f} tokens/sec):")
print(result.text[:200])
print(f"Time: {result.time_seconds:.1f}s, Tokens: {result.tokens_generated}")

# Unload
manager.unload_model()
print("\nModel unloaded.")