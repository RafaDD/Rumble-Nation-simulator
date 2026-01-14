"""
Entry point for the UI version of the game simulator.
"""

import sys
import multiprocessing as mp
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
import warnings

warnings.filterwarnings('ignore')

def main():
    """Main entry point for UI application."""
    # Set multiprocessing start method
    mp.set_start_method('spawn', force=True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("天下鸣动 Game Simulator")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

