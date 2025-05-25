#!/usr/bin/env python3

"""
Status Panel for Condor UDP Middleware
Displays real-time status information for the middleware components.

Part of the Condor UDP Middleware project.
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional
import time

# Configure logging
logger = logging.getLogger('gui.status_panel')


class MiddlewareStatusPanel:
    """
    Panel that displays status information for the middleware components.

    Shows connection status, data rates, and conversion statistics.
    """

    def __init__(self, parent):
        """
        Initialize the status panel.

        Args:
            parent: Parent widget
        """
        self.parent = parent

        # Create the main frame
        self.frame = ttk.Frame(parent, padding="10")

        # Split into sections
        self._create_connection_section()
        self._create_conversion_section()
        self._create_statistics_section()

    def _create_connection_section(self) -> None:
        """Create the connection status section."""
        # Connection status frame
        self.conn_frame = ttk.LabelFrame(self.frame, text="Connection Status", padding="10")
        self.conn_frame.pack(fill=tk.X, pady=5)

        # Create grid layout
        conn_grid = ttk.Frame(self.conn_frame)
        conn_grid.pack(fill=tk.X)

        # Bridge status
        ttk.Label(conn_grid, text="Middleware Status:", font=("", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        self.bridge_status = ttk.Label(conn_grid, text="Stopped", foreground="red")
        self.bridge_status.grid(row=0, column=1, sticky="w", padx=5)

        # Uptime
        ttk.Label(conn_grid, text="Uptime:", font=("", 9, "bold")).grid(row=0, column=2, sticky="w", padx=5)
        self.uptime_value = ttk.Label(conn_grid, text="00:00:00")
        self.uptime_value.grid(row=0, column=3, sticky="w", padx=5)

        # Input UDP status
        ttk.Label(conn_grid, text="Input UDP:", font=("", 9, "bold")).grid(row=1, column=0, sticky="w", padx=5)
        self.input_udp_status = ttk.Label(conn_grid, text="Stopped", foreground="red")
        self.input_udp_status.grid(row=1, column=1, sticky="w", padx=5)

        # Input port
        ttk.Label(conn_grid, text="Port:", font=("", 9)).grid(row=1, column=2, sticky="w", padx=5)
        self.input_port = ttk.Label(conn_grid, text="55278")
        self.input_port.grid(row=1, column=3, sticky="w", padx=5)

        # Output UDP status
        ttk.Label(conn_grid, text="Output UDP:", font=("", 9, "bold")).grid(row=2, column=0, sticky="w", padx=5)
        self.output_udp_status = ttk.Label(conn_grid, text="Stopped", foreground="red")
        self.output_udp_status.grid(row=2, column=1, sticky="w", padx=5)

        # Output target
        ttk.Label(conn_grid, text="Target:", font=("", 9)).grid(row=2, column=2, sticky="w", padx=5)
        self.output_target = ttk.Label(conn_grid, text="127.0.0.1:55300")
        self.output_target.grid(row=2, column=3, sticky="w", padx=5)

    def _create_conversion_section(self) -> None:
        """Create the conversion settings section."""
        self.conversion_frame = ttk.LabelFrame(self.frame, text="Current Conversion Settings", padding="10")
        self.conversion_frame.pack(fill=tk.X, pady=5)

        # Create grid layout
        conv_grid = ttk.Frame(self.conversion_frame)
        conv_grid.pack(fill=tk.X)

        # Conversions enabled status
        ttk.Label(conv_grid, text="Conversions:", font=("", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        self.conversions_enabled = ttk.Label(conv_grid, text="Disabled", foreground="orange")
        self.conversions_enabled.grid(row=0, column=1, sticky="w", padx=5)

        # Current unit settings
        ttk.Label(conv_grid, text="Altitude:", font=("", 9)).grid(row=1, column=0, sticky="w", padx=5)
        self.altitude_unit = ttk.Label(conv_grid, text="meters")
        self.altitude_unit.grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(conv_grid, text="Speed:", font=("", 9)).grid(row=1, column=2, sticky="w", padx=5)
        self.speed_unit = ttk.Label(conv_grid, text="mps")
        self.speed_unit.grid(row=1, column=3, sticky="w", padx=5)

        ttk.Label(conv_grid, text="Vario:", font=("", 9)).grid(row=2, column=0, sticky="w", padx=5)
        self.vario_unit = ttk.Label(conv_grid, text="mps")
        self.vario_unit.grid(row=2, column=1, sticky="w", padx=5)

        ttk.Label(conv_grid, text="Acceleration:", font=("", 9)).grid(row=2, column=2, sticky="w", padx=5)
        self.accel_unit = ttk.Label(conv_grid, text="mps2")
        self.accel_unit.grid(row=2, column=3, sticky="w", padx=5)

    def _create_statistics_section(self) -> None:
        """Create the statistics section."""
        # Statistics frame with two columns
        stats_container = ttk.Frame(self.frame)
        stats_container.pack(fill=tk.BOTH, expand=True, pady=5)

        # Left column - Data Flow Statistics
        self.dataflow_frame = ttk.LabelFrame(stats_container, text="Data Flow Statistics", padding="10")
        self.dataflow_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        dataflow_grid = ttk.Frame(self.dataflow_frame)
        dataflow_grid.pack(fill=tk.X)

        # Messages received
        ttk.Label(dataflow_grid, text="Messages Received:", font=("", 9, "bold")).grid(row=0, column=0, sticky="w",
                                                                                       padx=5)
        self.messages_received = ttk.Label(dataflow_grid, text="0")
        self.messages_received.grid(row=0, column=1, sticky="w", padx=5)

        # Messages processed
        ttk.Label(dataflow_grid, text="Messages Processed:", font=("", 9, "bold")).grid(row=1, column=0, sticky="w",
                                                                                        padx=5)
        self.messages_processed = ttk.Label(dataflow_grid, text="0")
        self.messages_processed.grid(row=1, column=1, sticky="w", padx=5)

        # Messages forwarded
        ttk.Label(dataflow_grid, text="Messages Forwarded:", font=("", 9, "bold")).grid(row=2, column=0, sticky="w",
                                                                                        padx=5)
        self.messages_forwarded = ttk.Label(dataflow_grid, text="0")
        self.messages_forwarded.grid(row=2, column=1, sticky="w", padx=5)

        # Data rates
        ttk.Label(dataflow_grid, text="Input Rate:", font=("", 9)).grid(row=3, column=0, sticky="w", padx=5)
        self.input_rate = ttk.Label(dataflow_grid, text="0.0 msg/sec")
        self.input_rate.grid(row=3, column=1, sticky="w", padx=5)

        ttk.Label(dataflow_grid, text="Output Rate:", font=("", 9)).grid(row=4, column=0, sticky="w", padx=5)
        self.output_rate = ttk.Label(dataflow_grid, text="0.0 msg/sec")
        self.output_rate.grid(row=4, column=1, sticky="w", padx=5)

        # Right column - Conversion Statistics
        self.conversion_stats_frame = ttk.LabelFrame(stats_container, text="Conversion Statistics", padding="10")
        self.conversion_stats_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        conv_stats_grid = ttk.Frame(self.conversion_stats_frame)
        conv_stats_grid.pack(fill=tk.X)

        # Messages with conversions
        ttk.Label(conv_stats_grid, text="Messages Converted:", font=("", 9, "bold")).grid(row=0, column=0, sticky="w",
                                                                                          padx=5)
        self.messages_converted = ttk.Label(conv_stats_grid, text="0")
        self.messages_converted.grid(row=0, column=1, sticky="w", padx=5)

        # Total conversions applied
        ttk.Label(conv_stats_grid, text="Total Conversions:", font=("", 9, "bold")).grid(row=1, column=0, sticky="w",
                                                                                         padx=5)
        self.total_conversions = ttk.Label(conv_stats_grid, text="0")
        self.total_conversions.grid(row=1, column=1, sticky="w", padx=5)

        # Variables converted
        ttk.Label(conv_stats_grid, text="Variables Converted:", font=("", 9)).grid(row=2, column=0, sticky="w", padx=5)
        self.variables_converted = ttk.Label(conv_stats_grid, text="None")
        self.variables_converted.grid(row=2, column=1, sticky="w", padx=5)

        # Conversion percentage
        ttk.Label(conv_stats_grid, text="Conversion Rate:", font=("", 9)).grid(row=3, column=0, sticky="w", padx=5)
        self.conversion_percentage = ttk.Label(conv_stats_grid, text="0%")
        self.conversion_percentage.grid(row=3, column=1, sticky="w", padx=5)

        # Sample conversion display
        sample_frame = ttk.LabelFrame(self.conversion_stats_frame, text="Latest Conversion Example", padding="5")
        sample_frame.pack(fill=tk.X, pady=(10, 0))

        self.sample_conversion = tk.Text(
            sample_frame,
            height=4,
            width=40,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 8)
        )
        self.sample_conversion.pack(fill=tk.X)

    def _is_data_active(self, status_dict: Dict[str, Any]) -> bool:
        """
        Helper function to determine if data is active.

        Args:
            status_dict: Status dictionary from UDP component

        Returns:
            bool: True if data is active (received within 5 seconds)
        """
        if not status_dict.get('running', False):
            return False

        last_received_ago = status_dict.get('last_received_ago')
        if last_received_ago is None:
            return False  # No data received yet

        return last_received_ago < 5.0  # Active if received within 5 seconds

    def _safe_get_numeric(self, data: Dict[str, Any], key: str, default: float = 0.0) -> float:
        """
        Safely get a numeric value from dictionary, handling None values.

        Args:
            data: Dictionary to get value from
            key: Key to look up
            default: Default value if key is missing or None

        Returns:
            float: The value or default
        """
        value = data.get(key, default)
        return value if value is not None else default

    def update_status(self, status: Dict[str, Any]) -> None:
        """
        Update the status display with current middleware status.

        Args:
            status: Bridge status dictionary
        """
        if not status:
            return

        try:
            # Update bridge status
            running = status.get('running', False)
            self.bridge_status.config(
                text="Running" if running else "Stopped",
                foreground="green" if running else "red"
            )

            # Update uptime
            uptime_secs = self._safe_get_numeric(status, 'uptime', 0)
            hours, remainder = divmod(int(uptime_secs), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.uptime_value.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # Update input UDP status
            if 'input_udp' in status and status['input_udp']:
                input_udp = status['input_udp']

                # Port
                self.input_port.config(text=str(input_udp.get('port', 'Unknown')))

                # Status with safe data activity check
                if input_udp.get('running', False):
                    if self._is_data_active(input_udp):
                        self.input_udp_status.config(text="Active", foreground="green")
                    else:
                        self.input_udp_status.config(text="No Data", foreground="orange")
                else:
                    self.input_udp_status.config(text="Stopped", foreground="red")

                # Update data flow statistics
                messages_received = input_udp.get('messages_received', 0)
                self.messages_received.config(text=str(messages_received))

                # Input rate
                input_rate = self._safe_get_numeric(input_udp, 'data_rate_mps', 0)
                self.input_rate.config(text=f"{input_rate:.1f} msg/sec")

            # Update output UDP status
            if 'output_udp' in status and status['output_udp']:
                output_udp = status['output_udp']

                # Target
                host = output_udp.get('target_host', '127.0.0.1')
                port = output_udp.get('target_port', 55300)
                self.output_target.config(text=f"{host}:{port}")

                # Status with safe data activity check
                if output_udp.get('active', False):
                    last_sent_ago = output_udp.get('last_sent_ago')
                    if last_sent_ago is not None and last_sent_ago < 5.0:
                        self.output_udp_status.config(text="Active", foreground="green")
                    else:
                        self.output_udp_status.config(text="No Output", foreground="orange")
                else:
                    self.output_udp_status.config(text="Stopped", foreground="red")

                # Output rate
                output_rate = self._safe_get_numeric(output_udp, 'send_rate_mps', 0)
                self.output_rate.config(text=f"{output_rate:.1f} msg/sec")

            # Update processing statistics
            self.messages_processed.config(text=str(status.get('messages_processed', 0)))
            self.messages_forwarded.config(text=str(status.get('messages_forwarded', 0)))
            self.messages_converted.config(text=str(status.get('messages_converted', 0)))

            # Update conversion settings display
            if 'conversion_settings' in status:
                conv_settings = status['conversion_settings']

                # Conversions enabled
                enabled = conv_settings.get('enabled', False)
                self.conversions_enabled.config(
                    text="Enabled" if enabled else "Disabled",
                    foreground="green" if enabled else "orange"
                )

                # Current units
                self.altitude_unit.config(text=conv_settings.get('altitude', 'meters'))
                self.speed_unit.config(text=conv_settings.get('speed', 'mps'))
                self.vario_unit.config(text=conv_settings.get('vario', 'mps'))
                self.accel_unit.config(text=conv_settings.get('acceleration', 'mps2'))

            # Update conversion statistics
            if 'conversion_stats' in status:
                conv_stats = status['conversion_stats']

                # Total conversions
                total_conv = conv_stats.get('total_conversions_applied', 0)
                self.total_conversions.config(text=str(total_conv))

                # Variables converted
                variables = conv_stats.get('variables_converted', [])
                if variables:
                    var_text = ', '.join(variables) if len(variables) <= 5 else f"{', '.join(variables[:5])}..."
                    self.variables_converted.config(text=var_text)
                else:
                    self.variables_converted.config(text="None")

                # Conversion percentage
                messages_processed = status.get('messages_processed', 0)
                messages_converted = status.get('messages_converted', 0)
                if messages_processed > 0:
                    percentage = (messages_converted / messages_processed) * 100
                    self.conversion_percentage.config(text=f"{percentage:.1f}%")
                else:
                    self.conversion_percentage.config(text="0%")

                # Update sample conversion (if available in detailed stats)
                self._update_sample_conversion(conv_stats)

        except Exception as e:
            # Log the error but don't crash the UI
            logger.error(f"Error updating status panel: {e}")

    def _update_sample_conversion(self, conv_stats: Dict[str, Any]) -> None:
        """Update the sample conversion display."""
        try:
            # This would ideally show a recent conversion example
            # For now, we'll show a summary
            sample_text = "Recent conversions:\n"

            current_settings = conv_stats.get('current_settings', {})
            if current_settings.get('enabled', False):
                sample_text += f"• Altitude → {current_settings.get('altitude', 'meters')}\n"
                sample_text += f"• Speed → {current_settings.get('speed', 'mps')}\n"
                sample_text += f"• Vario → {current_settings.get('vario', 'mps')}\n"
            else:
                sample_text += "Conversions disabled\n"
                sample_text += "Data passed through unchanged"

            # Update text widget
            self.sample_conversion.config(state=tk.NORMAL)
            self.sample_conversion.delete('1.0', tk.END)
            self.sample_conversion.insert('1.0', sample_text)
            self.sample_conversion.config(state=tk.DISABLED)

        except Exception as e:
            logger.error(f"Error updating sample conversion: {e}")

    def reset_status(self) -> None:
        """Reset all status indicators to initial state."""
        try:
            # Reset bridge status
            self.bridge_status.config(text="Stopped", foreground="red")
            self.uptime_value.config(text="00:00:00")

            # Reset UDP status
            self.input_udp_status.config(text="Stopped", foreground="red")
            self.output_udp_status.config(text="Stopped", foreground="red")
            self.input_port.config(text="55278")
            self.output_target.config(text="127.0.0.1:55300")

            # Reset conversion settings
            self.conversions_enabled.config(text="Disabled", foreground="orange")
            self.altitude_unit.config(text="meters")
            self.speed_unit.config(text="mps")
            self.vario_unit.config(text="mps")
            self.accel_unit.config(text="mps2")

            # Reset statistics
            self.messages_received.config(text="0")
            self.messages_processed.config(text="0")
            self.messages_forwarded.config(text="0")
            self.messages_converted.config(text="0")
            self.total_conversions.config(text="0")
            self.variables_converted.config(text="None")
            self.conversion_percentage.config(text="0%")

            # Reset rates
            self.input_rate.config(text="0.0 msg/sec")
            self.output_rate.config(text="0.0 msg/sec")

            # Reset sample conversion
            self.sample_conversion.config(state=tk.NORMAL)
            self.sample_conversion.delete('1.0', tk.END)
            self.sample_conversion.insert('1.0', "No data - middleware stopped")
            self.sample_conversion.config(state=tk.DISABLED)

        except Exception as e:
            logger.error(f"Error resetting status: {e}")


# Example usage:
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Status Panel Test")

    # Create a notebook to simulate the parent
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Create the status panel
    status_panel = MiddlewareStatusPanel(notebook)
    notebook.add(status_panel.frame, text="Status")


    # Simulate status updates
    def update_test():
        # Create a test status dictionary
        import math
        status = {
            "running": True,
            "uptime": time.time() % 3600,  # Cycle through an hour
            "error_count": 0,
            "input_udp": {
                "port": 55278,
                "running": True,
                "messages_received": int(time.time() * 10) % 1000,
                "data_rate_mps": 10.0 + 5.0 * math.sin(time.time() * 0.5),
                "last_received_ago": 1.0,  # Active data
            },
            "output_udp": {
                "target_host": "127.0.0.1",
                "target_port": 55300,
                "active": True,
                "send_rate_mps": 9.8 + 4.0 * math.sin(time.time() * 0.7),
                "last_sent_ago": 0.5,  # Active sending
            },
            "messages_processed": int(time.time() * 9.8) % 1000,
            "messages_converted": int(time.time() * 7.5) % 800,
            "messages_forwarded": int(time.time() * 9.5) % 950,
            "conversion_settings": {
                "enabled": True,
                "altitude": "feet",
                "speed": "knots",
                "vario": "fpm",
                "acceleration": "fps2"
            },
            "conversion_stats": {
                "total_conversions_applied": int(time.time() * 15) % 2000,
                "variables_converted": ["altitude", "airspeed", "vario"],
                "current_settings": {
                    "enabled": True,
                    "altitude": "feet",
                    "speed": "knots",
                    "vario": "fpm"
                }
            }
        }

        # Update the panel
        status_panel.update_status(status)

        # Schedule next update
        root.after(1000, update_test)


    # Start updates
    update_test()

    root.mainloop()