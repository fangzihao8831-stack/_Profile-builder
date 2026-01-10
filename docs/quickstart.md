# Quickstart

## Prerequisites

1. **AdsPower** installed and running
   - Download from adspower.com
   - Create at least one browser profile
   - Note the profile ID

2. **Ollama** installed with Qwen2.5-VL
   ```bash
   # Install Ollama from ollama.com
   ollama pull qwen2.5-vl:7b
   ```

3. **Python 3.11+**

4. **NVIDIA GPU with CUDA** (RTX 3070+ recommended)

## Installation

```bash
cd C:\Users\fangz\OneDrive\Desktop\profile_builder

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installations
python -c "from paddleocr import PaddleOCR; print('PaddleOCR OK')"
python -c "from humancursor import SystemCursor; print('HumanCursor OK')"
python -c "import ollama; print('Ollama OK')"
```

## Configuration

1. Copy example config:
   ```bash
   cp config.example.json config.json
   ```

2. Edit `config.json`:
   ```json
   {
     "adspower_base": "http://local.adspower.net:50325",
     "ollama_model": "qwen2.5-vl:7b",
     "default_profile": "your_profile_id_here"
   }
   ```

## First Run

```bash
# Run diagnostics
python run.py --diagnose

# Expected output:
# + AdsPower connection OK
# + Ollama connection OK
# + Qwen2.5-VL model loaded
# + PaddleOCR initialized
# + HumanCursor ready
# All systems ready!
```

## Start a Session

```bash
# Start warming session (30 minutes)
python run.py --profile YOUR_PROFILE_ID --duration 30

# With debug output
python run.py --profile YOUR_PROFILE_ID --duration 30 --debug

# Watch mode (visible browser)
python run.py --profile YOUR_PROFILE_ID --duration 30 --visible
```

## Troubleshooting

**"AdsPower not running"**
- Start AdsPower application
- Check it's listening on port 50325

**"Model not found"**
- Run `ollama pull qwen2.5-vl:7b`
- Check `ollama list` shows the model

**"CUDA out of memory"**
- Close other GPU applications
- Try smaller model: `qwen2.5-vl:3b`

**"Click missing target"**
- Run `--diagnose` to check coordinate calibration
- Check DPI scaling settings
