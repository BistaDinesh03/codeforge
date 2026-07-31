# Troubleshooting

## Server won't start
- Check if port 8000 is in use: `netstat -ano | findstr :8000`
- Try another port: `uvicorn app.main:app --port 8001`

## Extension can't connect
- Is the server running? Check `http://localhost:8000/health`
- Both computers on same network?
- Firewall blocking port 8000?
- Try manual URL in VS Code settings

## Model fails to load
- Check RAM: `http://localhost:8000/health/diagnostics`
- Try a smaller model
- Corrupted download? Delete and re-download

## Slow responses
- Close other applications
- Use smaller model (1.5B instead of 7B)
- CPU speed is the main factor

## "No module named app" error
- Make sure you're in the `server/` directory
- Activate virtual environment