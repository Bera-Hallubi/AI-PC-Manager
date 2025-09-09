"""
Main PyQt6 Window for AI PC Manager
Modern, professional UI with dark/light theme support
"""

import sys
import os
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
    QTabWidget, QProgressBar, QGroupBox, QScrollArea,
    QFrame, QSplitter, QListWidget, QListWidgetItem,
    QSystemTrayIcon, QMenu, QMessageBox, QStatusBar,
    QApplication, QStyleFactory
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QRect, QSize
)

# Import performance configuration
from ui_qt.performance_config import get_performance_config, apply_performance_optimizations
from PyQt6.QtGui import (
    QFont, QPixmap, QIcon, QPalette, QColor,
    QLinearGradient, QBrush, QPainter, QPen
)

from config.settings import settings
from utils.logger import get_logger
from core.ai_manager import ai_manager
from core.system_controller import system_controller
from core.system_monitor import system_monitor
from core.command_learner import command_learner
from interfaces.fast_voice_interface import voice_interface

logger = get_logger(__name__)


class SystemMetricsWidget(QWidget):
    """Widget for displaying system metrics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # CPU Usage
        self.cpu_group = QGroupBox("CPU Usage")
        cpu_layout = QVBoxLayout()
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_label = QLabel("0%")
        cpu_layout.addWidget(self.cpu_progress)
        cpu_layout.addWidget(self.cpu_label)
        self.cpu_group.setLayout(cpu_layout)
        
        # Memory Usage
        self.memory_group = QGroupBox("Memory Usage")
        memory_layout = QVBoxLayout()
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_label = QLabel("0%")
        memory_layout.addWidget(self.memory_progress)
        memory_layout.addWidget(self.memory_label)
        self.memory_group.setLayout(memory_layout)
        
        # Disk Usage
        self.disk_group = QGroupBox("Disk Usage")
        disk_layout = QVBoxLayout()
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        self.disk_label = QLabel("0%")
        disk_layout.addWidget(self.disk_progress)
        disk_layout.addWidget(self.disk_label)
        self.disk_group.setLayout(disk_layout)
        
        layout.addWidget(self.cpu_group)
        layout.addWidget(self.memory_group)
        layout.addWidget(self.disk_group)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_metrics(self):
        try:
            metrics = system_monitor.get_current_metrics()
            
            # Update CPU
            if 'cpu' in metrics and 'usage_percent' in metrics['cpu']:
                cpu_usage = metrics['cpu']['usage_percent']
                self.cpu_progress.setValue(int(cpu_usage))
                self.cpu_label.setText(f"{cpu_usage:.1f}%")
                
                # Color coding
                if cpu_usage > 80:
                    self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #BF616A; }")
                elif cpu_usage > 60:
                    self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #EBCB8B; }")
                else:
                    self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #A3BE8C; }")
            
            # Update Memory
            if 'memory' in metrics and 'usage_percent' in metrics['memory']:
                memory_usage = metrics['memory']['usage_percent']
                self.memory_progress.setValue(int(memory_usage))
                self.memory_label.setText(f"{memory_usage:.1f}%")
                
                # Color coding
                if memory_usage > 85:
                    self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #BF616A; }")
                elif memory_usage > 70:
                    self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #EBCB8B; }")
                else:
                    self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #A3BE8C; }")
            
            # Update Disk (use first available disk)
            if 'disk' in metrics:
                max_disk_usage = 0
                for device, disk_info in metrics['disk'].items():
                    if isinstance(disk_info, dict) and 'usage_percent' in disk_info:
                        max_disk_usage = max(max_disk_usage, disk_info['usage_percent'])
                
                self.disk_progress.setValue(int(max_disk_usage))
                self.disk_label.setText(f"{max_disk_usage:.1f}%")
                
                # Color coding
                if max_disk_usage > 90:
                    self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #BF616A; }")
                elif max_disk_usage > 75:
                    self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #EBCB8B; }")
                else:
                    self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #A3BE8C; }")
                    
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")


class CommandInputWidget(QWidget):
    """Widget for command input and display"""
    
    command_sent = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_voice_interface()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Command input
        input_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Type your command here or use voice...")
        self.command_input.returnPressed.connect(self.send_command)
        
        # Voice button
        self.voice_button = QPushButton("🎤")
        self.voice_button.setFixedSize(40, 40)
        self.voice_button.setToolTip("Click to speak")
        self.voice_button.clicked.connect(self.toggle_voice)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_command)
        
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.voice_button)
        input_layout.addWidget(self.send_button)
        
        # AI Activity display
        self.activity_label = QLabel("🤖 AI Activity")
        self.activity_display = QTextEdit()
        self.activity_display.setMaximumHeight(150)
        self.activity_display.setReadOnly(True)
        
        layout.addLayout(input_layout)
        layout.addWidget(self.activity_label)
        layout.addWidget(self.activity_display)
        
        self.setLayout(layout)
    
    def setup_voice_interface(self):
        """Setup voice interface"""
        self.is_listening = False
        self.voice_button.setStyleSheet("QPushButton { background-color: #5E81AC; }")
    
    def send_command(self):
        """Send command to AI"""
        command = self.command_input.text().strip()
        if command:
            self.command_sent.emit(command)
            self.command_input.clear()
    
    def toggle_voice(self):
        """Toggle voice recognition"""
        if not self.is_listening:
            self.start_voice_listening()
        else:
            self.stop_voice_listening()
    
    def start_voice_listening(self):
        """Start voice recognition"""
        try:
            if voice_interface.is_available():
                self.is_listening = True
                self.voice_button.setStyleSheet("QPushButton { background-color: #BF616A; }")
                self.voice_button.setText("🔴")
                self.add_activity("🎤 Listening...", "info")
                
                # Start listening
                voice_interface.start_listening(self.on_voice_command)
            else:
                self.add_activity("❌ Voice interface not available", "error")
        except Exception as e:
            logger.error(f"Error starting voice recognition: {e}")
            self.add_activity(f"❌ Voice error: {str(e)}", "error")
    
    def stop_voice_listening(self):
        """Stop voice recognition"""
        try:
            self.is_listening = False
            self.voice_button.setStyleSheet("QPushButton { background-color: #5E81AC; }")
            self.voice_button.setText("🎤")
            voice_interface.stop_listening()
            self.add_activity("🎤 Voice recognition stopped", "info")
        except Exception as e:
            logger.error(f"Error stopping voice recognition: {e}")
    
    def on_voice_command(self, command: str):
        """Handle voice command"""
        self.command_input.setText(command)
        self.send_command()
    
    def add_activity(self, message: str, activity_type: str = "info"):
        """Add activity message to display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding
        if activity_type == "success":
            icon = "✅"
            color = "#A3BE8C"
        elif activity_type == "error":
            icon = "❌"
            color = "#BF616A"
        elif activity_type == "warning":
            icon = "⚠️"
            color = "#EBCB8B"
        elif activity_type == "info":
            icon = "ℹ️"
            color = "#5E81AC"
        else:
            icon = "📝"
            color = "#ECEFF4"
        
        formatted_message = f"[{timestamp}] {icon} {message}"
        
        # Add to display
        self.activity_display.append(formatted_message)
        
        # Scroll to bottom
        scrollbar = self.activity_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_activity(self):
        """Clear activity display"""
        self.activity_display.clear()


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI PC Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.init_ui()
        self.setup_theme()
        self.setup_system_tray()
        self.setup_timers()
        
        # Start system monitoring
        system_monitor.start_monitoring(self.on_system_update)
        
        logger.info("Main window initialized")
    
    def init_ui(self):
        """Initialize user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Left panel - Command interface
        left_panel = QWidget()
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout()
        
        # Command input
        self.command_widget = CommandInputWidget()
        self.command_widget.command_sent.connect(self.process_command)
        left_layout.addWidget(self.command_widget)
        
        # Quick actions
        quick_actions_group = QGroupBox("Quick Actions")
        quick_layout = QGridLayout()
        
        # Quick action buttons
        self.open_calc_btn = QPushButton("Open Calculator")
        self.open_calc_btn.clicked.connect(lambda: self.process_command("open calculator"))
        
        self.open_notepad_btn = QPushButton("Open Notepad")
        self.open_notepad_btn.clicked.connect(lambda: self.process_command("open notepad"))
        
        self.screenshot_btn = QPushButton("Take Screenshot")
        self.screenshot_btn.clicked.connect(lambda: self.process_command("take screenshot"))
        
        self.system_info_btn = QPushButton("System Info")
        self.system_info_btn.clicked.connect(lambda: self.process_command("system info"))
        
        quick_layout.addWidget(self.open_calc_btn, 0, 0)
        quick_layout.addWidget(self.open_notepad_btn, 0, 1)
        quick_layout.addWidget(self.screenshot_btn, 1, 0)
        quick_layout.addWidget(self.system_info_btn, 1, 1)
        
        quick_actions_group.setLayout(quick_layout)
        left_layout.addWidget(quick_actions_group)
        
        # Command history
        history_group = QGroupBox("Recent Commands")
        history_layout = QVBoxLayout()
        self.command_history = QListWidget()
        self.command_history.itemDoubleClicked.connect(self.replay_command)
        history_layout.addWidget(self.command_history)
        history_group.setLayout(history_layout)
        left_layout.addWidget(history_group)
        
        left_panel.setLayout(left_layout)
        
        # Right panel - System monitoring and tabs
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # System metrics
        self.metrics_widget = SystemMetricsWidget()
        right_layout.addWidget(self.metrics_widget)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        
        # System Status tab
        self.status_tab = QWidget()
        status_layout = QVBoxLayout()
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        self.status_tab.setLayout(status_layout)
        self.tab_widget.addTab(self.status_tab, "System Status")
        
        # Learning tab
        self.learning_tab = QWidget()
        learning_layout = QVBoxLayout()
        self.learning_text = QTextEdit()
        self.learning_text.setReadOnly(True)
        learning_layout.addWidget(self.learning_text)
        self.learning_tab.setLayout(learning_layout)
        self.tab_widget.addTab(self.learning_tab, "AI Learning")
        
        right_layout.addWidget(self.tab_widget)
        right_panel.setLayout(right_layout)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def setup_theme(self):
        """Setup application theme"""
        theme = settings.get_theme()
        
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2E3440;
                    color: #ECEFF4;
                }
                QWidget {
                    background-color: #2E3440;
                    color: #ECEFF4;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #3B4252;
                    border-radius: 5px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QPushButton {
                    background-color: #5E81AC;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #81A1C1;
                }
                QPushButton:pressed {
                    background-color: #4C566A;
                }
                QLineEdit {
                    background-color: #3B4252;
                    border: 2px solid #4C566A;
                    border-radius: 4px;
                    padding: 8px;
                    color: #ECEFF4;
                }
                QLineEdit:focus {
                    border-color: #5E81AC;
                }
                QTextEdit {
                    background-color: #3B4252;
                    border: 2px solid #4C566A;
                    border-radius: 4px;
                    color: #ECEFF4;
                }
                QListWidget {
                    background-color: #3B4252;
                    border: 2px solid #4C566A;
                    border-radius: 4px;
                    color: #ECEFF4;
                }
                QListWidget::item {
                    padding: 5px;
                }
                QListWidget::item:selected {
                    background-color: #5E81AC;
                }
                QTabWidget::pane {
                    border: 2px solid #4C566A;
                    border-radius: 4px;
                }
                QTabBar::tab {
                    background-color: #3B4252;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #5E81AC;
                }
                QProgressBar {
                    border: 2px solid #4C566A;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #5E81AC;
                    border-radius: 2px;
                }
            """)
        else:
            # Light theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #F8F9FA;
                    color: #2E3440;
                }
                QWidget {
                    background-color: #F8F9FA;
                    color: #2E3440;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #D1D5DB;
                    border-radius: 5px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QPushButton {
                    background-color: #3B82F6;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
                QPushButton:pressed {
                    background-color: #1D4ED8;
                }
                QLineEdit {
                    background-color: white;
                    border: 2px solid #D1D5DB;
                    border-radius: 4px;
                    padding: 8px;
                    color: #2E3440;
                }
                QLineEdit:focus {
                    border-color: #3B82F6;
                }
                QTextEdit {
                    background-color: white;
                    border: 2px solid #D1D5DB;
                    border-radius: 4px;
                    color: #2E3440;
                }
                QListWidget {
                    background-color: white;
                    border: 2px solid #D1D5DB;
                    border-radius: 4px;
                    color: #2E3440;
                }
                QListWidget::item {
                    padding: 5px;
                }
                QListWidget::item:selected {
                    background-color: #3B82F6;
                    color: white;
                }
                QTabWidget::pane {
                    border: 2px solid #D1D5DB;
                    border-radius: 4px;
                }
                QTabBar::tab {
                    background-color: white;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #3B82F6;
                    color: white;
                }
                QProgressBar {
                    border: 2px solid #D1D5DB;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #3B82F6;
                    border-radius: 2px;
                }
            """)
    
    def setup_system_tray(self):
        """Setup system tray icon"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
            
            # Create tray menu
            tray_menu = QMenu()
            
            show_action = tray_menu.addAction("Show")
            show_action.triggered.connect(self.show)
            
            quit_action = tray_menu.addAction("Quit")
            quit_action.triggered.connect(self.close)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
    
    def setup_timers(self):
        """Setup update timers with performance optimization"""
        # Apply performance optimizations
        apply_performance_optimizations()
        
        # Get performance configuration
        perf_config = get_performance_config()
        
        # Status update timer (optimized frequency)
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(perf_config['status_update_interval'])
        
        # Learning update timer (optimized frequency)
        self.learning_timer = QTimer()
        self.learning_timer.timeout.connect(self.update_learning_info)
        self.learning_timer.start(perf_config['learning_update_interval'])
        
        # Performance optimization flags
        self._last_status_update = 0
        self._last_learning_update = 0
        self._update_threshold = perf_config['min_update_interval']
        self._max_updates_per_minute = perf_config['max_updates_per_minute']
        self._update_count = 0
        self._minute_start = time.time()
    
    def process_command(self, command: str):
        """Process user command"""
        try:
            # Add to command history
            self.add_to_history(command)
            
            # Show processing status
            self.command_widget.add_activity(f"🔄 Processing: {command}", "info")
            self.status_bar.showMessage("Processing command...")
            
            # If a previous thread is still running, stop and wait briefly
            try:
                if hasattr(self, 'command_thread') and self.command_thread and self.command_thread.isRunning():
                    self.command_thread.requestInterruption()
                    self.command_thread.quit()
                    self.command_thread.wait(1000)
            except Exception:
                pass

            # Process command in a fresh worker thread
            self.command_thread = CommandProcessor(command)
            self.command_thread.command_processed.connect(self.on_command_processed)
            self.command_thread.start()
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            self.command_widget.add_activity(f"❌ Error: {str(e)}", "error")
    
    def on_command_processed(self, result: Dict[str, Any]):
        """Handle command processing result"""
        try:
            response = result.get('response', 'No response')
            action = result.get('action', 'unknown')
            success = result.get('success', False)
            
            # Update activity display
            if success:
                self.command_widget.add_activity(f"✅ {response}", "success")
            else:
                self.command_widget.add_activity(f"❌ {response}", "error")
            
            # Speak response (non-blocking)
            if response:
                try:
                    voice_interface.speak(response, blocking=False)
                except Exception as _e:
                    logger.warning(f"GUI TTS failed: {_e}")

            # Update status bar
            self.status_bar.showMessage(f"Last command: {action}")
            
            # Learn from command
            command_learner.learn_from_command(
                result.get('original_command', ''),
                action,
                success,
                response,
                result.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"Error handling command result: {e}")
            self.command_widget.add_activity(f"❌ Result error: {str(e)}", "error")
    
    def add_to_history(self, command: str):
        """Add command to history list"""
        item = QListWidgetItem(f"[{datetime.now().strftime('%H:%M:%S')}] {command}")
        self.command_history.insertItem(0, item)
        
        # Keep only last 50 commands
        while self.command_history.count() > 50:
            self.command_history.takeItem(self.command_history.count() - 1)
    
    def replay_command(self, item: QListWidgetItem):
        """Replay a command from history"""
        command_text = item.text()
        # Extract command from history item
        if "] " in command_text:
            command = command_text.split("] ", 1)[1]
            self.command_widget.command_input.setText(command)
    
    def on_system_update(self, metrics: Dict[str, Any]):
        """Handle system metrics update"""
        # This is called by the system monitor
        pass
    
    def update_status(self):
        """Update system status display with throttling and rate limiting"""
        try:
            import time
            current_time = time.time()
            
            # Throttle updates to prevent excessive refreshing
            if current_time - self._last_status_update < self._update_threshold:
                return
            
            # Rate limiting: check updates per minute
            if current_time - self._minute_start >= 60:
                self._update_count = 0
                self._minute_start = current_time
            
            if self._update_count >= self._max_updates_per_minute:
                return
            
            self._last_status_update = current_time
            self._update_count += 1
            
            # Get cached summary to avoid heavy computation
            summary = system_monitor.get_system_summary()
            
            # Simplified status text for better performance
            status_text = f"""System Health: {summary.get('status', 'Unknown')} ({summary.get('health_score', 0):.1f}/100)
CPU: {summary.get('metrics', {}).get('cpu', {}).get('usage_percent', 0):.1f}% | Memory: {summary.get('metrics', {}).get('memory', {}).get('usage_percent', 0):.1f}%
Processes: {summary.get('metrics', {}).get('processes', {}).get('total_count', 0)} | Updated: {datetime.now().strftime('%H:%M:%S')}"""
            
            self.status_text.setPlainText(status_text)
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def update_learning_info(self):
        """Update AI learning information with throttling and rate limiting"""
        try:
            import time
            current_time = time.time()
            
            # Throttle updates to prevent excessive refreshing
            if current_time - self._last_learning_update < self._update_threshold:
                return
            
            # Rate limiting: check updates per minute
            if current_time - self._minute_start >= 60:
                self._update_count = 0
                self._minute_start = current_time
            
            if self._update_count >= self._max_updates_per_minute:
                return
            
            self._last_learning_update = current_time
            self._update_count += 1
            
            # Get statistics with error handling
            stats = command_learner.get_command_statistics()
            preferences = command_learner.get_user_preferences()
            
            # Simplified learning info for better performance
            learning_text = f"""AI Learning Statistics:
Commands: {stats.get('total_commands', 0)} | Success: {stats.get('overall_success_rate', 0):.1f}% | Patterns: {stats.get('total_patterns', 0)}

Most Used: {', '.join([cmd[0] for cmd in stats.get('most_used_commands', [])[:3]]) if stats.get('most_used_commands') else 'None'}

Updated: {datetime.now().strftime('%H:%M:%S')}"""
            
            self.learning_text.setPlainText(learning_text)
            
        except Exception as e:
            logger.error(f"Error updating learning info: {e}")
    
    def closeEvent(self, event):
        """Handle application close event"""
        try:
            # Ensure worker thread is stopped before destroying window
            try:
                if hasattr(self, 'command_thread') and self.command_thread and self.command_thread.isRunning():
                    self.command_thread.requestInterruption()
                    self.command_thread.quit()
                    self.command_thread.wait(2000)
            except Exception:
                pass

            # Stop monitoring
            system_monitor.stop_monitoring()
            
            # Cleanup components
            ai_manager.cleanup()
            system_controller.cleanup()
            command_learner.cleanup()
            voice_interface.cleanup()
            
            # Hide to tray if available
            if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
                self.hide()
                event.ignore()
            else:
                event.accept()
                
        except Exception as e:
            logger.error(f"Error during close: {e}")
            event.accept()


class CommandProcessor(QThread):
    """Thread for processing commands"""
    
    command_processed = pyqtSignal(dict)
    
    def __init__(self, command: str):
        super().__init__()
        self.command = command
    
    def run(self):
        """Process command in separate thread"""
        try:
            # Process with AI manager
            result = ai_manager.process_command(self.command)
            result['original_command'] = self.command
            result['success'] = result.get('action') != 'error'
            
            # Execute action if needed
            if result.get('action') == 'open_app' and result.get('target'):
                app_result = system_controller.open_application(result['target'])
                result['success'] = app_result.get('success', False)
                if not result['success']:
                    result['response'] = app_result.get('message', 'Failed to open application')
            
            elif result.get('action') == 'close_app' and result.get('target'):
                app_result = system_controller.close_application(result['target'])
                result['success'] = app_result.get('success', False)
                if not result['success']:
                    result['response'] = app_result.get('message', 'Failed to close application')
            
            elif result.get('action') == 'screenshot':
                screenshot_result = system_controller.take_screenshot()
                result['success'] = screenshot_result.get('success', False)
                result['response'] = screenshot_result.get('message', 'Screenshot failed')
            
            elif result.get('action') == 'system_info':
                info_result = system_controller.get_system_info()
                result['success'] = info_result.get('success', False)
                if result['success']:
                    info = info_result.get('system_info', {})
                    result['response'] = f"System: {info.get('platform', 'Unknown')} | CPU: {info.get('cpu', {}).get('count', 0)} cores | Memory: {info.get('memory', {}).get('total_gb', 0):.1f}GB"
                else:
                    result['response'] = info_result.get('message', 'Failed to get system info')
            
            elif result.get('action') == 'search' and result.get('target'):
                search_result = system_controller.search_application(result['target'])
                if search_result:
                    result['success'] = True
                    result['response'] = f"Found: {search_result['name']} at {search_result['path']}"
                else:
                    result['success'] = False
                    result['response'] = f"No application found matching '{result['target']}'"
            
            # Emit result
            self.command_processed.emit(result)
            
        except Exception as e:
            logger.error(f"Error processing command in thread: {e}")
            self.command_processed.emit({
                'original_command': self.command,
                'response': f"Error processing command: {str(e)}",
                'action': 'error',
                'success': False,
                'error': str(e)
            })
