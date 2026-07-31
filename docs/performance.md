# Performance Tips

## Model Selection
| RAM | Recommended Model | Speed |
|-----|-------------------|-------|
| 4GB | DeepSeek 1.3B | Fast |
| 8GB | Qwen 2.5 Coder 1.5B | Good |
| 16GB+ | Qwen 2.5 Coder 7B | Best quality |

## Speed Tips
- **Close other apps** — the AI uses your CPU and RAM
- **Lower max tokens** — shorter responses = faster responses
- **Use inline completions** — they're optimized for speed (50 tokens max)
- **Chat uses more tokens** — expect 2-5 seconds for full responses

## Hardware
- **CPU cores**: More cores = faster inference
- **RAM speed**: DDR4+ recommended
- **SSD vs HDD**: Only affects model loading time (1-3 seconds)

## Expected Speed
| Hardware | Tokens/second |
|----------|---------------|
| Old laptop (2015, 4GB) | 5-10 |
| Mid laptop (2020, 8GB) | 15-25 |
| Gaming PC (2022, 16GB) | 30-50 |