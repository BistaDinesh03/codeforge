from llama_cpp import Llama
import time

print('Loading model...')
start = time.time()

llm = Llama(
    model_path='qwen2.5-coder-1.5b-instruct-q4_k_m.gguf',
    n_ctx=2048,
    n_threads=4,
    verbose=False
)

load_time = time.time() - start
print(f'Model loaded in {load_time:.1f} seconds')

print('Generating response...')
start = time.time()

response = llm.create_chat_completion(
    messages=[{'role': 'user', 'content': 'Write a Python function to add two numbers'}],
    max_tokens=100,
    temperature=0.7
)

gen_time = time.time() - start
tokens = response['usage']['completion_tokens']
speed = tokens / gen_time

print(f'Response:')
print(response['choices'][0]['message']['content'])
print(f'Generated {tokens} tokens in {gen_time:.1f}s ({speed:.1f} tokens/sec)')