#!/usr/bin/env python3

"""
Centralized logging configuration for Condor UDP Middleware.
Provides functions to consistently configure the logging system
throughout the application, including GUI visualization.

Part of the Condor UDP Middleware project.
"""

import logging
import os
from typing import Optional

# Global variable to track GUI text handler
text_handler = None


def configure_logging(
        level: int = logging.DEBUG,
        log_to_file: bool = False,
        log_file_path: Optional[str] = None,
        max_log_files: int = 5,
        max_log_size_mb: int = 10
) -> None:
    """
    Configure the logging system for the entire application.

    Args:
        level: Logging level for console (default DEBUG)
        log_to_file: Whether to save logs to a file
        log_file_path: Path to log file (optional)
        max_log_files: Maximum number of log files for rotation
        max_log_size_mb: Maximum size of log file in MB
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Save existing text handlers to restore them later
    text_handlers = []
    for handler in root_logger.handlers[:]:
        if hasattr(handler, 'text_widget'):
            text_handlers.append(handler)
            root_logger.removeHandler(handler)
        else:
            # Remove other handlers
            root_logger.removeHandler(handler)

    # Configure root logger level to allow all needed messages
    root_logger.setLevel(min(level, logging.INFO))

    # Create standard formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add console handler with requested level (usually DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if enabled
    if log_to_file and log_file_path:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

            # Create rotating file handler
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=max_log_size_mb * 1024 * 1024,
                backupCount=max_log_files
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            logging.info(f"Logging to file: {log_file_path}")
        except Exception as e:
            logging.error(f"Error setting up file logging: {e}")

    # Restore text handlers with fixed INFO level
    for handler in text_handlers:
        # Ensure level is INFO for GUI
        handler.setLevel(logging.INFO)
        root_logger.addHandler(handler)

    logging.info(f"Logging system initialized: console={logging.getLevelName(level)}, GUI=INFO")


def add_text_handler(text_widget) -> logging.Handler:
    """
    Add a text handler for GUI that shows only INFO, WARNING and ERROR.

    Args:
        text_widget: Tkinter text widget where logs will be displayed

    Returns:
        The created handler
    """
    global text_handler

    class TextHandler(logging.Handler):
        def __init__(self, text_widget):
            logging.Handler.__init__(self)
            self.text_widget = text_widget
            self.setLevel(logging.INFO)  # Fixed level at INFO
            self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.max_lines = 1000  # Limit to avoid memory overload

        def emit(self, record):
            msg = self.format(record)

            def append():
                if not self.text_widget.winfo_exists():
                    return

                try:
                    self.text_widget.configure(state='normal')

                    # Color based on level
                    if record.levelno >= logging.ERROR:
                        self.text_widget.insert('end', msg + '\n', 'error')
                    elif record.levelno >= logging.WARNING:
                        self.text_widget.insert('end', msg + '\n', 'warning')
                    else:
                        self.text_widget.insert('end', msg + '\n', 'info')

                    # Limit number of lines
                    line_count = int(self.text_widget.index('end-1c').split('.')[0])
                    if line_count > self.max_lines:
                        to_delete = line_count - self.max_lines
                        self.text_widget.delete('1.0', f'{to_delete + 1}.0')

                    self.text_widget.configure(state='disabled')
                    self.text_widget.see('end')
                except Exception as e:
                    print(f"Error updating log widget: {e}")

            # Add to main thread
            if self.text_widget.winfo_exists():
                self.text_widget.after(0, append)

    try:
        # Configure tags for coloring messages
        text_widget.tag_configure('info', foreground='black')
        text_widget.tag_configure('warning', foreground='orange')
        text_widget.tag_configure('error', foreground='red')
    except Exception as e:
        print(f"Error configuring text tags: {e}")

    # Create and configure handler
    handler = TextHandler(text_widget)

    # Add to root logger
    root_logger = logging.getLogger()

    # Remove existing text handlers
    for h in list(root_logger.handlers):
        if hasattr(h, 'text_widget'):
            root_logger.removeHandler(h)

    root_logger.addHandler(handler)
    text_handler = handler

    # Startup message
    logging.info("Log view initialized with fixed INFO level")

    return handler


def remove_text_handler() -> None:
    """Remove text handler from root logger."""
    global text_handler

    root_logger = logging.getLogger()

    # Remove handler if it exists
    if text_handler:
        root_logger.removeHandler(text_handler)
        text_handler = None

    # Search and remove other text handlers
    for handler in root_logger.handlers[:]:
        if hasattr(handler, 'text_widget'):
            root_logger.removeHandler(handler)