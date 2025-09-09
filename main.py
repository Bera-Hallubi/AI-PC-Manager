"""
Main entry point for AI PC Manager
Command-line interface for the AI PC Manager application
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path (PyInstaller compatibility)
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    project_root = os.path.dirname(sys.executable)
else:
    # Running as script
    project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config.settings import settings
from utils.logger import get_logger
from core.ai_manager import ai_manager
from core.system_controller import system_controller
from core.system_monitor import system_monitor
from core.command_learner import command_learner
from interfaces.fast_voice_interface import voice_interface

logger = get_logger(__name__)


def safe_print(text: str):
    """Print text safely in Windows consoles that may not support Unicode.
    Falls back to ASCII by stripping unsupported characters.
    """
    try:
        print(text)
    except Exception:
        try:
            print(text.encode('ascii', 'ignore').decode('ascii'))
        except Exception:
            # As last resort, print repr
            print(repr(text))


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    AI PC Manager v1.0.0                     ║
║              Intelligent PC Management Assistant             ║
║                                                              ║
║  🤖 AI Brain: Local LLM (DialoGPT/Transformers)            ║
║  👂 Ears: Local Speech Recognition (Whisper)                ║
║  🗣️ Mouth: Local Text-to-Speech (pyttsx3/Coqui)            ║
║  🤖 Hands: System Control (PyAutoGUI/psutil)                ║
║  🧠 Memory: Command Learning & Pattern Recognition          ║
╚══════════════════════════════════════════════════════════════╝
    """
    safe_print(banner)


def print_help():
    """Print help information"""
    help_text = """
AI PC Manager - Available Commands:

📱 Application Management:
• "open [app name]" - Launch applications
• "close [app name]" - Close applications
• "search for [name]" - Find apps, files, or folders

📸 System Control:
• "take a screenshot" - Capture screen
• "system info" - Get PC status
• "help" - Show this help

💬 General:
• "hello" - Greet the AI
• Ask questions about your computer
• Request help with tasks

Voice Commands:
• Click the microphone button in the GUI
• Or use the --voice flag for voice mode

Examples:
• python main.py --command "open calculator"
• python main.py --voice
• python main.py --gui
    """
    print(help_text)


def process_command_interactive():
    """Interactive command processing mode"""
    print("🤖 AI PC Manager - Interactive Mode")
    print("Type 'help' for available commands, 'quit' to exit")
    print("=" * 50)
    
    while True:
        try:
            # Get user input
            command = input("\n💬 You: ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if command.lower() == 'help':
                print_help()
                continue
            
            # Process command
            print("🔄 Processing...")
            result = ai_manager.process_command(command)
            
            # Display response
            response = result.get('response', 'No response')
            action = result.get('action', 'unknown')
            success = result.get('success', False)
            
            if success:
                print(f"✅ AI: {response}")
            else:
                print(f"❌ AI: {response}")
            
            # Execute action if needed
            if action == 'open_app' and result.get('target'):
                print(f"🚀 Opening {result['target']}...")
                app_result = system_controller.open_application(result['target'])
                if app_result.get('success'):
                    print(f"✅ {app_result.get('message', 'Application opened')}")
                else:
                    print(f"❌ {app_result.get('message', 'Failed to open application')}")
            
            elif action == 'close_app' and result.get('target'):
                print(f"🛑 Closing {result['target']}...")
                app_result = system_controller.close_application(result['target'])
                if app_result.get('success'):
                    print(f"✅ {app_result.get('message', 'Application closed')}")
                else:
                    print(f"❌ {app_result.get('message', 'Failed to close application')}")
            
            elif action == 'screenshot':
                print("📸 Taking screenshot...")
                screenshot_result = system_controller.take_screenshot()
                if screenshot_result.get('success'):
                    print(f"✅ {screenshot_result.get('message', 'Screenshot taken')}")
                else:
                    print(f"❌ {screenshot_result.get('message', 'Screenshot failed')}")
            
            elif action == 'system_info':
                print("📊 Getting system information...")
                info_result = system_controller.get_system_info()
                if info_result.get('success'):
                    info = info_result.get('system_info', {})
                    print(f"💻 System: {info.get('platform', 'Unknown')}")
                    print(f"🖥️ CPU: {info.get('cpu', {}).get('count', 0)} cores, {info.get('cpu', {}).get('usage_percent', 0):.1f}% usage")
                    print(f"🧠 Memory: {info.get('memory', {}).get('total_gb', 0):.1f}GB total, {info.get('memory', {}).get('usage_percent', 0):.1f}% used")
                    print(f"💾 Disk: {info.get('disk', {}).get('total_gb', 0):.1f}GB total, {info.get('disk', {}).get('usage_percent', 0):.1f}% used")
                else:
                    print(f"❌ {info_result.get('message', 'Failed to get system info')}")
            
            elif action == 'search' and result.get('target'):
                print(f"🔍 Searching for {result['target']}...")
                search_result = system_controller.search_application(result['target'])
                if search_result:
                    print(f"✅ Found: {search_result['name']}")
                    print(f"📍 Path: {search_result['path']}")
                else:
                    print(f"❌ No application found matching '{result['target']}'")
            
            # Learn from command
            command_learner.learn_from_command(
                command,
                action,
                success,
                response,
                result.get('metadata', {})
            )
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            logger.error(f"Error in interactive mode: {e}")


def process_single_command(command: str, speak: bool = False):
    """Process a single command"""
    try:
        print(f"🔄 Processing command: {command}")
        
        # Process with AI
        result = ai_manager.process_command(command)
        response = result.get('response', 'No response')
        action = result.get('action', 'unknown')
        success = result.get('success', False)
        
        print(f"🤖 AI Response: {response}")
        if speak and response:
            try:
                voice_interface.speak(response, blocking=False)
            except Exception as _e:
                logger.warning(f"TTS speak failed: {_e}")
        
        # Execute action if needed
        if action == 'open_app' and result.get('target'):
            app_result = system_controller.open_application(result['target'])
            print(f"🚀 App Result: {app_result.get('message', 'No message')}")
        
        elif action == 'close_app' and result.get('target'):
            app_result = system_controller.close_application(result['target'])
            print(f"🛑 App Result: {app_result.get('message', 'No message')}")
        
        elif action == 'screenshot':
            screenshot_result = system_controller.take_screenshot()
            print(f"📸 Screenshot: {screenshot_result.get('message', 'No message')}")
        
        elif action == 'system_info':
            info_result = system_controller.get_system_info()
            if info_result.get('success'):
                info = info_result.get('system_info', {})
                print(f"💻 System: {info.get('platform', 'Unknown')}")
                print(f"🖥️ CPU: {info.get('cpu', {}).get('count', 0)} cores")
                print(f"🧠 Memory: {info.get('memory', {}).get('total_gb', 0):.1f}GB")
            else:
                print(f"❌ System Info Error: {info_result.get('message', 'Unknown error')}")
        
        # Learn from command
        command_learner.learn_from_command(
            command,
            action,
            success,
            response,
            result.get('metadata', {})
        )
        
    except Exception as e:
        print(f"❌ Error processing command: {str(e)}")
        logger.error(f"Error processing single command: {e}")


def voice_mode():
    """Voice interaction mode"""
    try:
        if not voice_interface.is_available():
            print("❌ Voice interface not available. Please check your audio setup.")
            return
        
        print("🎤 Voice Mode - Speak your commands")
        print("Say 'stop' or press Ctrl+C to exit")
        print("=" * 50)
        
        def on_voice_command(command: str):
            print(f"🎤 Heard: {command}")
            process_single_command(command, speak=True)
        
        # Start voice recognition
        voice_interface.start_listening(on_voice_command)
        
        # Keep running until interrupted
        try:
            while True:
                import time
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping voice recognition...")
            voice_interface.stop_listening()
            print("👋 Goodbye!")
    
    except Exception as e:
        print(f"❌ Error in voice mode: {str(e)}")
        logger.error(f"Error in voice mode: {e}")


def gui_mode():
    """Launch GUI mode"""
    try:
        print("🖥️ Launching GUI...")
        from ui_qt.main_qt import main as gui_main
        gui_main()
    except Exception as e:
        print(f"❌ Error launching GUI: {str(e)}")
        logger.error(f"Error launching GUI: {e}")


def show_system_status():
    """Show current system status"""
    try:
        safe_print("📊 System Status")
        safe_print("=" * 50)
        
        # Get system summary
        summary = system_monitor.get_system_summary()
        safe_print(f"Health Score: {summary.get('health_score', 0):.1f}/100 ({summary.get('status', 'Unknown')})")
        
        # Get detailed metrics
        metrics = system_monitor.get_current_metrics()
        
        if 'cpu' in metrics:
            cpu = metrics['cpu']
            safe_print(f"CPU: {cpu.get('usage_percent', 0):.1f}% usage, {cpu.get('count', 0)} cores")
        
        if 'memory' in metrics:
            memory = metrics['memory']
            safe_print(f"Memory: {memory.get('usage_percent', 0):.1f}% usage, {memory.get('total_gb', 0):.1f}GB total")
        
        if 'disk' in metrics:
            for device, disk_info in metrics['disk'].items():
                if isinstance(disk_info, dict) and 'usage_percent' in disk_info:
                    safe_print(f"Disk {device}: {disk_info['usage_percent']:.1f}% usage")
        
        # Get learning statistics
        stats = command_learner.get_command_statistics()
        safe_print(f"\nAI Learning: {stats.get('total_commands', 0)} commands, {stats.get('overall_success_rate', 0):.1f}% success rate")
        
    except Exception as e:
        print(f"❌ Error getting system status: {str(e)}")
        logger.error(f"Error getting system status: {e}")


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="AI PC Manager - Intelligent PC Management Assistant")
    parser.add_argument("--command", "-c", help="Execute a single command")
    parser.add_argument("--voice", "-v", action="store_true", help="Enable voice mode")
    parser.add_argument("--gui", "-g", action="store_true", help="Launch GUI mode")
    parser.add_argument("--status", "-s", action="store_true", help="Show system status")
    parser.add_argument("--help-commands", action="store_true", help="Show available commands")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Initialize components
    try:
        logger.info("Initializing AI PC Manager components...")
        
        # Start system monitoring
        system_monitor.start_monitoring()
        logger.info("System monitoring started")
        
    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        print(f"❌ Error initializing components: {str(e)}")
        return 1
    
    try:
        # Handle different modes
        if args.help_commands:
            print_help()
        elif args.status:
            show_system_status()
        elif args.command:
            process_single_command(args.command)
        elif args.voice:
            voice_mode()
        elif args.gui:
            gui_mode()
        elif args.interactive:
            process_command_interactive()
        else:
            # Default: if running as bundled EXE, open GUI; otherwise interactive
            if getattr(sys, 'frozen', False):
                gui_mode()
            else:
                process_command_interactive()
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"❌ Error: {str(e)}")
        return 1
    
    finally:
        # Cleanup
        try:
            logger.info("Cleaning up components...")
            system_monitor.stop_monitoring()
            ai_manager.cleanup()
            system_controller.cleanup()
            command_learner.cleanup()
            voice_interface.cleanup()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
