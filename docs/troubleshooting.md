# Troubleshooting

## Server won't start
**Problem:** Double-click the shortcut but nothing happens.

**Try these:**
1. Make sure Python 3.11+ is installed: open Command Prompt, type `python --version`
2. Check if port 8000 is in use: `netstat -ano | findstr :8000`
3. Try running manually: open `C:\CodeForge` and double-click `Start Server.bat`

## Extension says "Disconnected"
**Problem:** Status bar shows red "CodeForge" icon.

**Try these:**
1. Is the server running? Open `http://localhost:8000` in your browser
2. Both computers on the same WiFi network?
3. Firewall might be blocking port 8000
4. Press Ctrl+Shift+P → "CodeForge: Reconnect"

## "No AI model loaded"
**Problem:** Chat returns an error about no model.

**Fix:**
1. Open `http://localhost:8000` in your browser
2. Click "Download Recommended Model"
3. Wait for download to finish
4. Click "Start Server"

## AI is very slow
**Problem:** Responses take 10+ seconds.

**Tips:**
- Close other programs to free RAM
- Use a smaller model (Qwen 1.5B instead of 7B)
- CPU speed matters — old laptops are slower

## Still stuck?
Open a [GitHub Issue](https://github.com/codeforge/codeforge/issues) or start a [Discussion](https://github.com/codeforge/codeforge/discussions).