"""
PyQt6 Application Entry Point for AI PC Manager
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from ui_qt.qt_main_window import MainWindow
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main application entry point"""
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("AI PC Manager")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("AI PC Manager")
        
        # Set application icon (if available)
        try:
            icon_path = os.path.join(project_root, "assets", "icon.png")
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            logger.debug(f"Could not set application icon: {e}")
        
        # Enable high DPI scaling (compatible with PyQt6)
        try:
            app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
            app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            # Fallback for newer PyQt6 versions
            try:
                app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
            except AttributeError:
                # If neither attribute exists, continue without them
                pass
        
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        # Center window on screen
        screen = app.primaryScreen().geometry()
        window_geometry = main_window.geometry()
        x = (screen.width() - window_geometry.width()) // 2
        y = (screen.height() - window_geometry.height()) // 2
        main_window.move(x, y)
        
        logger.info("AI PC Manager started successfully")
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        
        # Show error message if possible
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "AI PC Manager Error",
                f"Failed to start AI PC Manager:\n\n{str(e)}\n\nPlease check the logs for more details."
            )
            sys.exit(1)
        except:
            print(f"Error starting AI PC Manager: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
