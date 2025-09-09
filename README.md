# AI PC Manager 🤖💻

An intelligent AI assistant that can manage your entire PC, learn from your commands, and respond with voice using cutting-edge **local** AI technology. No internet required for core functionality!

## 🎯 Key Features

### 🧠 **Local AI Brain (LLM)**
- **DialoGPT Integration** - Microsoft's conversational AI model
- **Transformers Support** - Hugging Face transformers for local processing
- **Memory System** - ChromaDB-powered conversation memory
- **Pattern Learning** - Learns from your commands and improves over time
- **Fallback Systems** - Multiple AI backends for reliability

### 👂 **Local Ears (STT)**
- **Whisper Integration** - OpenAI's state-of-the-art speech recognition
- **Real-time Processing** - Continuous voice recognition with VAD
- **Multi-language Support** - Automatic language detection
- **Noise Suppression** - Advanced audio processing
- **Fallback Recognition** - Google Speech Recognition as backup

### 🗣️ **Local Mouth (TTS)**
- **pyttsx3 Integration** - Cross-platform text-to-speech
- **Coqui TTS Support** - High-quality local voice synthesis
- **Multiple Voice Options** - Wide selection of voices and accents
- **Real-time Synthesis** - Low-latency voice generation
- **Voice Customization** - Adjustable rate, volume, and voice selection

### 🤖 **Smart Hands (OS Control)**
- **Application Management** - Open, close, and search for applications
- **System Control** - Screenshots, system info, and monitoring
- **File Operations** - Search and manage files across your system
- **Automation** - PyAutoGUI, keyboard, and mouse control
- **Smart Discovery** - Automatically finds applications not in database

### 🧠 **Learning System**
- **Command Learning** - Adapts to your commands and preferences
- **Pattern Recognition** - Learns common command patterns
- **Success Tracking** - Monitors and improves command success rates
- **User Preferences** - Remembers your favorite applications and commands
- **Continuous Improvement** - Gets better with every interaction

## 🖥️ System Requirements

### **Minimum Requirements**
- **CPU:** Intel i5-8400 / AMD Ryzen 5 2600 or equivalent
- **RAM:** 8GB (16GB+ recommended for local models)
- **Storage:** 2GB+ free space (for models and data)
- **OS:** Windows 10/11, macOS 10.15+, or Linux Ubuntu 20.04+
- **Python:** 3.8 or higher

### **Recommended for Best Performance**
- **CPU:** Intel i7-12700K / AMD Ryzen 7 5700X or better
- **RAM:** 16GB+ (32GB+ for larger models)
- **Storage:** 5GB+ free space (SSD recommended)
- **GPU:** RTX 3060 / RX 6600 XT or better (for faster AI processing)

## 🚀 Quick Start

### Option 1: Standard Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd ai-pc-manager

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Option 2: GUI Mode
```bash
# Run with graphical interface
python main.py --gui
```

### Option 3: Voice Mode
```bash
# Run with voice recognition
python main.py --voice
```

### Option 4: Interactive Mode
```bash
# Run in interactive command-line mode
python main.py --interactive
```

## 📦 Dependencies

### Core Dependencies
- **Python 3.8+** - Required runtime
- **PyQt6** - Modern UI framework
- **psutil** - System monitoring
- **pyyaml** - Configuration management
- **loguru** - Advanced logging

### AI & Machine Learning
- **torch** - PyTorch for local AI models
- **transformers** - Hugging Face transformers
- **faster-whisper** - High-performance Whisper implementation
- **sentence-transformers** - Embedding models
- **chromadb** - Vector database for memory

### Audio Processing
- **speechrecognition** - Speech recognition library
- **pyaudio** - Audio input/output
- **sounddevice** - Real-time audio streaming
- **pyttsx3** - Text-to-speech synthesis
- **TTS** - Coqui TTS for local voice synthesis

### System Control
- **pyautogui** - GUI automation
- **keyboard** - Keyboard control
- **mouse** - Mouse control

## 📁 Project Structure

```
ai-pc-manager/
├── core/                   # Core AI and system logic
│   ├── ai_manager.py       # AI command processing and learning
│   ├── system_controller.py # System operations and app management
│   ├── system_monitor.py   # System monitoring and metrics
│   └── command_learner.py  # Command learning and pattern recognition
├── interfaces/             # System interfaces
│   └── fast_voice_interface.py # Voice recognition and TTS
├── ui_qt/                  # Modern PyQt6 UI components
│   ├── main_qt.py          # PyQt6 application entry point
│   └── qt_main_window.py   # Main window with professional UI
├── config/                 # Configuration files
│   ├── config.yaml         # Main configuration
│   └── settings.py         # Settings management
├── utils/                  # Utility functions
│   └── logger.py           # Logging configuration
├── data/                   # Data storage and learning
│   ├── command_history.json # Command history
│   ├── discovered_apps.json # Discovered applications
│   ├── learned_patterns.json # Learned command patterns
│   └── monitoring/         # System monitoring data
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
└── test_comprehensive.py   # Comprehensive test suite
```

## 🎯 Usage Examples

### Command Line Interface
```bash
# Single command
python main.py --command "open calculator"

# Interactive mode
python main.py --interactive

# Voice mode
python main.py --voice

# GUI mode
python main.py --gui

# System status
python main.py --status
```

### Available Commands
- **"open [app name]"** - Launch applications
- **"close [app name]"** - Close applications
- **"search for [name]"** - Find apps, files, or folders
- **"take a screenshot"** - Capture screen
- **"system info"** - Get PC status
- **"help"** - Show available commands

### Voice Commands
- Click the microphone button in the GUI
- Or use `--voice` flag for voice-only mode
- Say commands naturally: "Open calculator", "Take a screenshot"

## 🔧 Configuration

### Main Configuration (`config/config.yaml`)
```yaml
# AI Brain Configuration
ai:
  primary_model: "microsoft/DialoGPT-medium"
  fallback_model: "distilgpt2"
  memory_enabled: true
  temperature: 0.7

# Speech Recognition
stt:
  engine: "whisper"
  whisper_model: "base"
  device: "cpu"
  language: "en"

# Text-to-Speech
tts:
  engine: "pyttsx3"
  voice_rate: 200
  voice_volume: 0.8

# System Control
system:
  auto_discover_apps: true
  search_depth: 10
  search_timeout: 30
```

### Customization
- **Themes:** Dark/Light mode support
- **Voice Settings:** Adjustable rate, volume, and voice selection
- **AI Models:** Switch between different local models
- **Learning:** Enable/disable command learning
- **Monitoring:** Configure system monitoring intervals

## 🧪 Testing

### Run Comprehensive Tests
```bash
python test_comprehensive.py
```

### Test Coverage
- **Unit Tests** - Core functionality validation
- **Integration Tests** - End-to-end system testing
- **Performance Tests** - Speed and efficiency testing
- **Stress Tests** - High load handling

## 🚀 Performance Optimization

### For Local Models
- Use CPU for smaller models (base, small)
- Use GPU for larger models (medium, large) if available
- Adjust batch sizes based on your hardware
- Enable model quantization for memory efficiency

### For System Performance
- Close unnecessary applications before running
- Use SSD storage for better model loading
- Ensure sufficient RAM for model operations
- Monitor system resources during use

## 🛠️ Troubleshooting

### Common Issues

1. **Voice Recognition Not Working**
   - Check microphone permissions
   - Ensure audio drivers are installed
   - Try different audio devices

2. **AI Models Not Loading**
   - Check internet connection for initial download
   - Ensure sufficient disk space
   - Verify Python and PyTorch installation

3. **Application Not Found**
   - Check if application is installed
   - Try using full application name
   - Use search functionality to locate apps

4. **Performance Issues**
   - Close other applications
   - Use smaller AI models
   - Check system resources

### Debug Mode
```bash
# Run with debug logging
python main.py --interactive --debug

# Check system requirements
python -c "from utils.system_check import check_requirements; check_requirements()"
```

## 🔒 Privacy & Security

- **100% Local Processing** - No data sent to external servers
- **No Internet Required** - Works completely offline
- **Local Data Storage** - All data stored locally
- **No Tracking** - No telemetry or usage tracking
- **Open Source** - Full source code available for review

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Hugging Face** - For transformer models and libraries
- **OpenAI** - For Whisper speech recognition
- **Microsoft** - For DialoGPT conversational AI
- **PyQt6** - For the modern UI framework
- **Python Community** - For the amazing ecosystem

## 📞 Support

- **Issues** - Report bugs and request features on GitHub
- **Documentation** - Check the wiki for detailed guides
- **Community** - Join our Discord server for help and discussion

---

**Made with ❤️ for the AI and automation community**

*Transform your PC into an intelligent assistant that learns and adapts to your needs!*
