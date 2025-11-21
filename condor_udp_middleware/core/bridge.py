#!/usr/bin/env python3

"""
Main Bridge for Condor UDP Middleware
Orchestrates the flow of data between UDP receiver, converter, and UDP sender.

Part of the Condor UDP Middleware project.
"""

import asyncio
import logging
import time
import socket
import threading
from typing import Dict, Any, Optional

# Import our components (avoiding conflict with Python's io module)
from condor_udp_middleware.core.settings import MiddlewareSettings
from condor_udp_middleware.core.converter import UnitConverter

# Configure logging
logger = logging.getLogger('bridge')

# Network and threading constants
# These values are tuned for optimal performance and stability
UDP_BUFFER_SIZE = 65535  # Maximum UDP packet size (64KB)
SOCKET_TIMEOUT = 0.5  # Socket read timeout in seconds (allows periodic checks)
THREAD_JOIN_TIMEOUT = 2.0  # Maximum time to wait for thread termination in seconds
MAIN_LOOP_INTERVAL = 1.0  # Main monitoring loop check interval in seconds
STATUS_LOG_INTERVAL = 30  # Status logging interval in seconds


class MiddlewareUDPReceiver:
    """Simplified UDP receiver for the middleware."""

    def __init__(self, host: str = '0.0.0.0', port: int = 55278, data_callback=None):
        self.host = host
        self.port = port
        self.data_callback = data_callback
        self.socket = None
        self.running = False
        self.receive_thread = None

        # Statistics
        self.messages_received = 0
        self.bytes_received = 0
        self.start_time = 0
        self.error_count = 0
        self.last_received_time = 0

    def start_receiving(self) -> bool:
        """Start receiving UDP messages."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.settimeout(SOCKET_TIMEOUT)
            self.socket.bind((self.host, self.port))

            self.running = True
            self.start_time = time.time()

            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            logger.info(f"UDP receiver bound to {self.host}:{self.port}")
            return True

        except OSError as e:
            logger.error(f"Error starting UDP receiver: {e}")
            return False

    def _receive_loop(self):
        """Main receive loop."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(UDP_BUFFER_SIZE)
                if data:
                    decoded_message = data.decode('utf-8', errors='ignore')
                    self.messages_received += 1
                    self.bytes_received += len(data)
                    self.last_received_time = time.time()

                    if self.data_callback:
                        try:
                            self.data_callback(decoded_message)
                        except Exception as e:
                            logger.error(f"Error in callback: {e}")
                            self.error_count += 1

            except socket.timeout:
                continue
            except OSError as e:
                if self.running:
                    logger.error(f"UDP receive error: {e}")
                    self.error_count += 1
                break
            except UnicodeDecodeError as e:
                logger.error(f"Error decoding UDP message: {e}")
                self.error_count += 1
            except (ValueError, AttributeError) as e:
                logger.error(f"Error processing received data: {e}")
                self.error_count += 1

    def close(self):
        """Close the UDP receiver."""
        self.running = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=THREAD_JOIN_TIMEOUT)
        if self.socket:
            try:
                self.socket.close()
            except OSError as e:
                logger.warning(f"Error closing receiver socket: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get receiver status."""
        now = time.time()
        uptime = now - self.start_time if self.start_time > 0 else 0

        return {
            "host": self.host,
            "port": self.port,
            "bound": bool(self.socket),
            "running": self.running,
            "messages_received": self.messages_received,
            "bytes_received": self.bytes_received,
            "error_count": self.error_count,
            "uptime_seconds": uptime,
            "data_rate_mps": self.messages_received / uptime if uptime > 0 else 0,
            "last_received_ago": now - self.last_received_time if self.last_received_time > 0 else None
        }


class MiddlewareUDPSender:
    """UDP sender for the middleware."""

    def __init__(self, target_host: str = '127.0.0.1', target_port: int = 55300):
        self.target_host = target_host
        self.target_port = target_port
        self.socket = None
        self.connected = False

        # Statistics
        self.messages_sent = 0
        self.bytes_sent = 0
        self.start_time = 0
        self.error_count = 0
        self.last_sent_time = 0

    def start_sending(self) -> bool:
        """Initialize the UDP sender."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Test connectivity
            try:
                self.socket.connect((self.target_host, self.target_port))
                self.connected = True
                logger.info(f"UDP sender initialized for {self.target_host}:{self.target_port}")
            except OSError as e:
                logger.warning(f"Could not validate target address {self.target_host}:{self.target_port}: {e}")
                self.connected = False

            self.start_time = time.time()
            return True

        except OSError as e:
            logger.error(f"Error creating UDP socket: {e}")
            self.error_count += 1
            return False

    def send_message(self, message: str) -> bool:
        """Send a UDP message."""
        if not self.socket:
            logger.error("UDP socket not initialized")
            return False

        try:
            message_bytes = message.encode('utf-8')
            bytes_sent = self.socket.sendto(message_bytes, (self.target_host, self.target_port))

            self.messages_sent += 1
            self.bytes_sent += bytes_sent
            self.last_sent_time = time.time()

            logger.debug(f"Sent {bytes_sent} bytes to {self.target_host}:{self.target_port}")
            return True

        except OSError as e:
            logger.error(f"Error sending UDP message: {e}")
            self.error_count += 1
            return False
        except (UnicodeEncodeError, TypeError) as e:
            logger.error(f"Error encoding message: {e}")
            self.error_count += 1
            return False

    def close(self):
        """Close the UDP sender."""
        if self.socket:
            try:
                self.socket.close()
                logger.info("UDP sender closed")
            except OSError as e:
                logger.error(f"Error closing UDP socket: {e}")
        self.connected = False

    def get_status(self) -> Dict[str, Any]:
        """Get sender status."""
        now = time.time()
        uptime = now - self.start_time if self.start_time > 0 else 0

        return {
            "target_host": self.target_host,
            "target_port": self.target_port,
            "connected": self.connected,
            "active": bool(self.socket),
            "messages_sent": self.messages_sent,
            "bytes_sent": self.bytes_sent,
            "error_count": self.error_count,
            "uptime_seconds": uptime,
            "send_rate_mps": self.messages_sent / uptime if uptime > 0 else 0,
            "last_sent_ago": now - self.last_sent_time if self.last_sent_time > 0 else None
        }


class UDPMiddlewareBridge:
    """
    Main orchestrator for Condor UDP Middleware.

    Coordinates the flow of data between components:
    - MiddlewareUDPReceiver: Receives UDP data from Condor
    - UnitConverter: Converts units according to user preferences
    - MiddlewareUDPSender: Sends converted data to target application
    """

    def __init__(self, settings_file: Optional[str] = None):
        """
        Initialize the middleware bridge.

        Args:
            settings_file: Path to settings file (optional)
        """
        # Load settings
        self.settings = MiddlewareSettings(settings_file)

        # Apply logging settings
        self.settings.apply_logging_settings()

        # Initialize components
        self._init_components()

        # Flags and state
        self.running = False
        self.startup_time = 0
        self.error_count = 0
        self.main_task = None

        # Statistics
        self.messages_processed = 0
        self.messages_converted = 0
        self.messages_forwarded = 0

    def _init_components(self) -> None:
        """Initialize all components based on settings."""
        # Initialize UDP receiver
        network_settings = self.settings.get('network')
        self.udp_receiver = MiddlewareUDPReceiver(
            host='0.0.0.0',  # Listen on all interfaces
            port=network_settings.input_port,
            data_callback=self._handle_udp_data
        )

        # Initialize unit converter
        conversion_settings = {
            'enabled': self.settings.get('conversions', 'enabled'),
            'altitude': self.settings.get('conversions', 'altitude'),
            'speed': self.settings.get('conversions', 'speed'),
            'vario': self.settings.get('conversions', 'vario'),
            'acceleration': self.settings.get('conversions', 'acceleration')
        }
        self.unit_converter = UnitConverter(conversion_settings)

        # Initialize UDP sender
        self.udp_sender = MiddlewareUDPSender(
            target_host=network_settings.output_host,
            target_port=network_settings.output_port
        )

    def _handle_udp_data(self, data: str) -> None:
        """
        Process incoming UDP data.

        Args:
            data: Raw UDP message from Condor
        """
        try:
            # Update statistics
            self.messages_processed += 1

            # Convert units
            converted_message, conversion_info = self.unit_converter.process_message(data)

            # Check if any conversions were applied
            if conversion_info.get("conversions_applied", 0) > 0:
                self.messages_converted += 1
                logger.debug(f"Applied {conversion_info['conversions_applied']} conversions")

            # Forward converted message
            if self.udp_sender.send_message(converted_message):
                self.messages_forwarded += 1
            else:
                logger.warning("Failed to forward converted message")
                self.error_count += 1

        except (KeyError, TypeError, AttributeError) as e:
            logger.error(f"Error processing UDP data: {e}")
            self.error_count += 1

    async def start(self) -> None:
        """Start the middleware bridge and all components."""
        if self.running:
            logger.warning("Bridge is already running")
            return

        logger.info("Starting Condor UDP Middleware Bridge...")
        self.startup_time = time.time()
        self.running = True
        self.error_count = 0

        # Reset statistics
        self.messages_processed = 0
        self.messages_converted = 0
        self.messages_forwarded = 0

        # Start UDP receiver
        if not self.udp_receiver.start_receiving():
            logger.error("Failed to start UDP receiver")
            self.error_count += 1
            await self.stop()
            return

        # Start UDP sender
        if not self.udp_sender.start_sending():
            logger.error("Failed to start UDP sender")
            self.error_count += 1
            await self.stop()
            return

        # Start main monitoring loop
        self.main_task = asyncio.create_task(self._main_loop())

        logger.info("Bridge started successfully")
        logger.info(f"Listening on port {self.udp_receiver.port}")
        logger.info(f"Forwarding to {self.udp_sender.target_host}:{self.udp_sender.target_port}")

        # Log current conversion settings
        conv_settings = self.settings.get('conversions')
        if conv_settings.enabled:
            logger.info("Unit conversions enabled:")
            logger.info(f"  Altitude: {conv_settings.altitude}")
            logger.info(f"  Speed: {conv_settings.speed}")
            logger.info(f"  Vario: {conv_settings.vario}")
            logger.info(f"  Acceleration: {conv_settings.acceleration}")
        else:
            logger.info("Unit conversions disabled - passing through original data")

    async def stop(self) -> None:
        """Stop the bridge and all components."""
        if not self.running:
            logger.warning("Bridge is not running")
            return

        logger.info("Stopping Condor UDP Middleware Bridge...")
        self.running = False

        # Cancel main task
        if self.main_task:
            self.main_task.cancel()
            try:
                await self.main_task
            except asyncio.CancelledError:
                pass

        # Stop UDP sender
        try:
            self.udp_sender.close()
            logger.info("UDP sender stopped")
        except (OSError, AttributeError) as e:
            logger.error(f"Error stopping UDP sender: {e}")

        # Stop UDP receiver
        try:
            self.udp_receiver.close()
            logger.info("UDP receiver stopped")
        except (OSError, AttributeError) as e:
            logger.error(f"Error stopping UDP receiver: {e}")

        logger.info("Bridge stopped successfully")

    async def _main_loop(self) -> None:
        """Main monitoring loop that checks component status."""
        try:
            last_status_log = 0

            while self.running:
                await self._check_components()
                await asyncio.sleep(MAIN_LOOP_INTERVAL)

                # Log status periodically
                now = time.time()
                if now - last_status_log > STATUS_LOG_INTERVAL:
                    self._log_status()
                    last_status_log = now

        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
            raise
        except (KeyError, AttributeError, TypeError) as e:
            logger.error(f"Error in main loop: {e}")
            self.error_count += 1

    async def _check_components(self) -> None:
        """Check the status of all components and handle issues."""
        # Check UDP receiver
        receiver_status = self.udp_receiver.get_status()
        if not receiver_status["running"]:
            logger.warning("UDP receiver not running")

        # Check UDP sender
        sender_status = self.udp_sender.get_status()
        if not sender_status["active"]:
            logger.warning("UDP sender not active")

        # Check if we're processing data
        if self.messages_processed > 0:
            data_age = time.time() - self.udp_receiver.last_received_time
            if data_age > 10.0:
                logger.warning(f"No data received for {data_age:.1f} seconds")

    def _log_status(self) -> None:
        """Log the status of all components."""
        receiver_status = self.udp_receiver.get_status()
        sender_status = self.udp_sender.get_status()
        converter_stats = self.unit_converter.get_statistics()

        logger.info("Bridge Status:")
        logger.info(f"  Running: {self.running}")
        logger.info(f"  Uptime: {time.time() - self.startup_time:.1f} seconds")
        logger.info(f"  Errors: {self.error_count}")

        logger.info("UDP Receiver:")
        logger.info(f"  Running: {receiver_status['running']}")
        logger.info(f"  Messages: {receiver_status['messages_received']}")
        logger.info(f"  Rate: {receiver_status['data_rate_mps']:.1f} msg/sec")

        logger.info("UDP Sender:")
        logger.info(f"  Active: {sender_status['active']}")
        logger.info(f"  Messages: {sender_status['messages_sent']}")
        logger.info(f"  Rate: {sender_status['send_rate_mps']:.1f} msg/sec")

        logger.info("Conversion:")
        logger.info(f"  Processed: {self.messages_processed}")
        logger.info(f"  Converted: {self.messages_converted}")
        logger.info(f"  Forwarded: {self.messages_forwarded}")
        logger.info(f"  Total conversions: {converter_stats['total_conversions_applied']}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the bridge and all components.

        Returns:
            dict: Status information
        """
        # Get component status
        receiver_status = self.udp_receiver.get_status()
        sender_status = self.udp_sender.get_status()
        converter_stats = self.unit_converter.get_statistics()

        # Build status dictionary
        result = {
            "running": self.running,
            "uptime": time.time() - self.startup_time if self.startup_time > 0 else 0,
            "error_count": self.error_count,
            "data_active": receiver_status['running'] and (
                        receiver_status.get('last_received_ago') or float('inf')) < 5.0,

            # Component status
            "input_udp": receiver_status,
            "output_udp": sender_status,

            # Processing statistics
            "messages_processed": self.messages_processed,
            "messages_converted": self.messages_converted,
            "messages_forwarded": self.messages_forwarded,

            # Conversion statistics
            "conversion_stats": converter_stats,

            # Current settings
            "conversion_settings": self.settings.get('conversions').__dict__,
            "network_settings": self.settings.get('network').__dict__
        }

        return result

    def update_settings(self, new_settings_file: Optional[str] = None) -> bool:
        """
        Update settings and reconfigure components.

        Args:
            new_settings_file: Path to new settings file (optional)

        Returns:
            bool: True if settings were updated successfully
        """
        # Stop if running
        was_running = self.running
        if was_running:
            # Use asyncio to stop properly
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.stop())
            loop.close()

        # Load new settings
        if new_settings_file:
            success = self.settings.load(new_settings_file)
        else:
            success = self.settings.load()

        if not success:
            logger.error("Failed to load new settings")
            return False

        # Apply logging settings
        self.settings.apply_logging_settings()

        # Reinitialize components
        self._init_components()

        # Restart if was running
        if was_running:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start())
            loop.close()

        logger.info("Settings updated successfully")
        return True

    def update_conversion_settings(self, new_conversion_settings: Dict[str, Any]) -> None:
        """
        Update conversion settings without restarting the bridge.

        Args:
            new_conversion_settings: New conversion settings
        """
        # Update settings object
        for key, value in new_conversion_settings.items():
            self.settings.set('conversions', key, value)

        # Update converter
        conversion_dict = {
            'enabled': self.settings.get('conversions', 'enabled'),
            'altitude': self.settings.get('conversions', 'altitude'),
            'speed': self.settings.get('conversions', 'speed'),
            'vario': self.settings.get('conversions', 'vario'),
            'acceleration': self.settings.get('conversions', 'acceleration')
        }
        self.unit_converter.update_settings(conversion_dict)

        logger.info(f"Conversion settings updated: {new_conversion_settings}")

