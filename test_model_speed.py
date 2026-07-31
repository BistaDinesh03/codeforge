from llama_cpp import Llama
import time

llm = Llama(
    model_path='qwen2.5-coder-1.5b-instruct-q4_k_m.gguf',
    n_ctx=2048,
    n_threads=4,
    verbose=False
)

start = time.time()
response = llm.create_chat_completion(
    messages=[{'role': 'user', 'content': 'def fibonacci(n):'}],
    max_tokens=50,
    temperature=0.2
)
elapsed = time.time() - start
tokens = response['usage']['completion_tokens']

print(f'Speed: {tokens/elapsed:.1f} tokens/sec')
print('Response:')
print(response['choices'][0]['message']['content'])