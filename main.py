#!/usr/bin/env python3

"""
Main entry point for Condor UDP Middleware
Parses command line arguments and starts the application
in either GUI or CLI mode.

Middleware UDP para Condor - Especificaciones Finales
"""

import os
import sys
import argparse
import logging
import asyncio
import signal
import tkinter as tk
from typing import Optional

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'condor_udp_middleware')))

# Import our modules
from condor_udp_middleware.core.log_config import configure_logging
from condor_udp_middleware.core.bridge import UDPMiddlewareBridge
from condor_udp_middleware.core.settings import MiddlewareSettings
from condor_udp_middleware.gui.main_window import MiddlewareMainWindow

# Configure initial logging
configure_logging(level=logging.INFO)
logger = logging.getLogger('main')


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Condor UDP Middleware - Converts units in real-time between Condor and external applications"
    )
    
    # Mode selection
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in command-line mode (no GUI)"
    )
    
    # Settings file
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file"
    )
    
    # Auto-start
    parser.add_argument(
        "--start",
        action="store_true",
        help="Automatically start the middleware on launch"
    )
    
    # Auto-minimized
    parser.add_argument(
        "--minimized",
        action="store_true",
        help="Start minimized (GUI mode only)"
    )
    
    # Logging
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Set logging level"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log to specified file"
    )
    
    return parser.parse_args()


async def run_cli(bridge: UDPMiddlewareBridge):
    """
    Run the middleware in command-line mode.
    
    Args:
        bridge: Bridge instance
    """
    logger.info("Starting Condor UDP Middleware in CLI mode")
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    
    def signal_handler():
        logger.info("Shutdown signal received")
        loop.create_task(bridge.stop())
        loop.stop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    # Start bridge
    await bridge.start()
    
    try:
        logger.info("Middleware running, press Ctrl+C to stop")
        
        # Keep running until stopped
        while bridge.running:
            await asyncio.sleep(1)
            
            # Log status periodically
            if int(asyncio.get_event_loop().time()) % 30 == 0:  # Every 30 seconds
                status = bridge.get_status()
                
                logger.info(f"Middleware Status:")
                logger.info(f"- Running for {status['uptime']:.1f} seconds")
                logger.info(f"- Input UDP: {status['input_udp']['bound'] if status['input_udp'] else 'Disabled'}")
                logger.info(f"- Output UDP: {status['output_udp']['active'] if status['output_udp'] else 'Disabled'}")
                logger.info(f"- Messages converted: {status.get('messages_converted', 0)}")
                logger.info(f"- Data active: {status['data_active']}")
    
    except asyncio.CancelledError:
        # Handle cancellation
        pass
    
    finally:
        # Ensure bridge is stopped
        if bridge.running:
            await bridge.stop()
        
        logger.info("Middleware stopped, exiting")


def run_gui(args):
    """
    Run the middleware in GUI mode.
    
    Args:
        args: Command line arguments
    """
    logger.info("Starting Condor UDP Middleware in GUI mode")
    
    # Create root window
    root = tk.Tk()
    
    # Create main window
    app = MiddlewareMainWindow(root)
    
    # Apply command-line overrides
    if args.start:
        # Schedule auto-start after a short delay (to let the UI initialize)
        root.after(1000, app._start_bridge)
    
    if args.minimized:
        # Start minimized
        root.iconify()
    
    # Run the application
    root.mainloop()


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load settings
    settings = MiddlewareSettings(args.config)
    
    # Apply logging settings from command line
    if args.log_level:
        settings.set('logging', 'level', args.log_level)
    
    if args.log_file:
        settings.set('logging', 'log_to_file', True)
        settings.set('logging', 'log_file_path', args.log_file)
    
    settings.apply_logging_settings()
    
    # Run in appropriate mode
    if args.cli:
        # CLI mode
        bridge = UDPMiddlewareBridge(args.config)
        asyncio.run(run_cli(bridge))
    else:
        # GUI mode
        run_gui(args)


if __name__ == "__main__":
    main()
