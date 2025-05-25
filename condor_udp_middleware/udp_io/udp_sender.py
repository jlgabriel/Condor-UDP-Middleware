#!/usr/bin/env python3

"""
UDP Sender for Condor UDP Middleware
Sends converted UDP messages to target applications.

Part of the Condor UDP Middleware project.
"""

import socket
import time
import threading
import logging
from typing import Optional, Dict, Any
import queue

# Configure logging
logger = logging.getLogger('udp_sender')


class UDPSender:
    """
    Sends UDP messages to a target host and port.
    Used to forward converted Condor data to external applications.
    """
    
    def __init__(self, 
                 target_host: str = '127.0.0.1',
                 target_port: int = 55300,
                 buffer_size: int = 65535):
        """
        Initialize the UDP sender.
        
        Args:
            target_host: Target host to send messages to
            target_port: Target port to send messages to
            buffer_size: UDP buffer size
        """
        self.target_host = target_host
        self.target_port = target_port
        self.buffer_size = buffer_size
        
        # UDP socket
        self.socket: Optional[socket.socket] = None
        
        # Message queue for async sending
        self.message_queue = queue.Queue()
        self.send_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Statistics
        self.messages_sent = 0
        self.bytes_sent = 0
        self.start_time = 0
        self.error_count = 0
        self.last_sent_time = 0
        
        # Connection status
        self.connected = False
    
    def open(self) -> bool:
        """
        Open the UDP socket.
        
        Returns:
            bool: True if socket opened successfully, False otherwise
        """
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Set socket options for better performance
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Test connectivity by trying to connect (UDP doesn't really connect, but this validates the address)
            try:
                # This doesn't actually send data, just validates the address
                self.socket.connect((self.target_host, self.target_port))
                self.connected = True
                logger.info(f"UDP sender initialized for {self.target_host}:{self.target_port}")
            except OSError as e:
                logger.warning(f"Could not validate target address {self.target_host}:{self.target_port}: {e}")
                # We'll still try to send, as UDP doesn't require a connection
                self.connected = False
            
            self.start_time = time.time()
            return True
                
        except OSError as e:
            logger.error(f"Error creating UDP socket: {e}")
            self.error_count += 1
            return False
    
    def close(self) -> None:
        """Close the UDP socket and stop the send thread."""
        self.running = False
        
        # Wait for send thread to finish
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join(timeout=2.0)
        
        # Close UDP socket
        if self.socket:
            try:
                self.socket.close()
                logger.info("UDP sender closed")
            except OSError as e:
                logger.error(f"Error closing UDP socket: {e}")
        
        self.connected = False
    
    def start_sending(self) -> bool:
        """
        Start the async sending thread.
        
        Returns:
            bool: True if sending started successfully, False otherwise
        """
        if not self.socket:
            if not self.open():
                return False
        
        self.running = True
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.send_thread.start()
        logger.info(f"Started UDP sender to {self.target_host}:{self.target_port}")
        return True
    
    def send_message(self, message: str) -> bool:
        """
        Send a UDP message immediately (synchronous).
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.socket:
            logger.error("UDP socket not initialized")
            return False
        
        try:
            # Encode message to bytes
            message_bytes = message.encode('utf-8')
            
            # Send message
            bytes_sent = self.socket.sendto(message_bytes, (self.target_host, self.target_port))
            
            # Update statistics
            self.messages_sent += 1
            self.bytes_sent += bytes_sent
            self.last_sent_time = time.time()
            
            logger.debug(f"Sent {bytes_sent} bytes to {self.target_host}:{self.target_port}")
            return True
            
        except OSError as e:
            logger.error(f"Error sending UDP message: {e}")
            self.error_count += 1
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            self.error_count += 1
            return False
    
    def send_message_async(self, message: str) -> bool:
        """
        Queue a message for asynchronous sending.
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if message was queued successfully, False otherwise
        """
        if not self.running:
            logger.warning("Async sending not started")
            return False
        
        try:
            self.message_queue.put(message, block=False)
            return True
        except queue.Full:
            logger.warning("Message queue full, dropping message")
            self.error_count += 1
            return False
    
    def _send_loop(self) -> None:
        """
        Main loop for asynchronous message sending.
        Runs in a separate thread.
        """
        if not self.socket:
            logger.error("UDP socket not initialized for send loop")
            return
        
        logger.info("UDP sender loop started")
        
        while self.running:
            try:
                # Get message from queue with timeout
                try:
                    message = self.message_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Send the message
                if not self.send_message(message):
                    logger.warning("Failed to send queued message")
                
                # Mark task as done
                self.message_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in send loop: {e}")
                self.error_count += 1
        
        logger.info("UDP sender loop stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the UDP sender.
        
        Returns:
            dict: Status information
        """
        now = time.time()
        uptime = now - self.start_time if self.start_time > 0 else 0
        
        return {
            "target_host": self.target_host,
            "target_port": self.target_port,
            "connected": self.connected,
            "active": bool(self.socket),
            "running": self.running and bool(self.send_thread and self.send_thread.is_alive()),
            "messages_sent": self.messages_sent,
            "bytes_sent": self.bytes_sent,
            "error_count": self.error_count,
            "uptime_seconds": uptime,
            "send_rate_mps": self.messages_sent / uptime if uptime > 0 else 0,
            "send_rate_bps": self.bytes_sent / uptime if uptime > 0 else 0,
            "last_sent_ago": now - self.last_sent_time if self.last_sent_time > 0 else None,
            "queue_size": self.message_queue.qsize() if self.running else 0
        }
    
    def is_sending_data(self) -> bool:
        """
        Check if we're actively sending data (sent something in the last 5 seconds).
        
        Returns:
            bool: True if sending data, False otherwise
        """
        if not self.last_sent_time:
            return False
        
        return (time.time() - self.last_sent_time) < 5.0
    
    def set_target(self, host: str, port: int) -> bool:
        """
        Change the target host and port. Will reopen the socket if already open.
        
        Args:
            host: New target host
            port: New target port
            
        Returns:
            bool: True if successful, False otherwise
        """
        was_running = self.running
        
        # Stop current sending if running
        if was_running:
            self.close()
        
        # Set new target
        self.target_host = host
        self.target_port = port
        
        # Restart if it was running
        if was_running:
            return self.start_sending()
        
        return True
    
    def flush_queue(self) -> int:
        """
        Flush all pending messages in the queue.
        
        Returns:
            int: Number of messages flushed
        """
        flushed = 0
        try:
            while True:
                self.message_queue.get_nowait()
                self.message_queue.task_done()
                flushed += 1
        except queue.Empty:
            pass
        
        if flushed > 0:
            logger.info(f"Flushed {flushed} messages from queue")
        
        return flushed
    
    def wait_for_queue_empty(self, timeout: float = 5.0) -> bool:
        """
        Wait for the message queue to be empty.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if queue became empty, False if timeout
        """
        try:
            # Join with timeout
            start_time = time.time()
            while not self.message_queue.empty():
                if time.time() - start_time > timeout:
                    return False
                time.sleep(0.1)
            
            return True
        except Exception as e:
            logger.error(f"Error waiting for queue: {e}")
            return False


# Example usage and testing:
if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.DEBUG)
    
    # Create UDP sender
    sender = UDPSender(target_host='127.0.0.1', target_port=55300)
    
    try:
        # Start sending
        if sender.start_sending():
            print(f"Started UDP sender to {sender.target_host}:{sender.target_port}")
            
            # Send some test messages
            test_messages = [
                "time=1.0\naltitude=1000.0\nairspeed=50.0",
                "time=2.0\naltitude=1100.0\nairspeed=55.0",
                "time=3.0\naltitude=1200.0\nairspeed=60.0"
            ]
            
            for i, message in enumerate(test_messages):
                print(f"Sending message {i+1}: {len(message)} bytes")
                
                # Test both sync and async sending
                if i % 2 == 0:
                    # Synchronous send
                    success = sender.send_message(message)
                    print(f"Sync send result: {success}")
                else:
                    # Asynchronous send
                    success = sender.send_message_async(message)
                    print(f"Async send queued: {success}")
                
                time.sleep(1)
            
            # Wait for async messages to be sent
            print("Waiting for async messages to be sent...")
            sender.wait_for_queue_empty(timeout=5.0)
            
            # Show final status
            status = sender.get_status()
            print("\nFinal Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
        
        else:
            print("Failed to start UDP sender")
    
    except KeyboardInterrupt:
        print("\nSending stopped by user")
    
    finally:
        # Always close the sender
        sender.close()
        print("UDP sender closed")
