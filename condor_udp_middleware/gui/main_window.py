#!/usr/bin/env python3

"""
Main Window for Condor UDP Middleware
The primary GUI window that contains all panels and controls
for managing the middleware.

Part of the Condor UDP Middleware project.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import asyncio
import logging
from typing import Optional, Dict, Any
import webbrowser

# Import our modules
from condor_udp_middleware.core.bridge import UDPMiddlewareBridge
from condor_udp_middleware.core.settings import MiddlewareSettings
from condor_udp_middleware.gui.status_panel import MiddlewareStatusPanel
from condor_udp_middleware.gui.settings_dialog import MiddlewareSettingsDialog

# Configure logging
logger = logging.getLogger('gui.main_window')


class MiddlewareMainWindow:
    """
    Main application window for Condor UDP Middleware.
    
    This window contains:
    - Menu bar with file, tools, and help options
    - Control panel with start/stop and conversion settings
    - Status panel showing data flow and conversion statistics
    - Log panel for real-time monitoring
    """
    
    def __init__(self, master: tk.Tk):
        """
        Initialize the main window.
        
        Args:
            master: Tkinter root window
        """
        self.master = master
        self.bridge: Optional[UDPMiddlewareBridge] = None
        self.settings = MiddlewareSettings()
        
        # Asyncio event loop for the bridge
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.bridge_thread: Optional[threading.Thread] = None
        
        # Setup UI
        self._setup_window()
        self._create_menu()
        self._create_widgets()
        
        # Update status periodically
        self._update_status()
        
        # Initialize Bridge (but don't start it yet)
        self._init_bridge()
        
        # Handle window close
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Show "first run" message if applicable
        if self.settings.settings.first_run:
            self._show_first_run_message()
    
    def _setup_window(self) -> None:
        """Configure the main window."""
        self.master.title("Condor UDP Middleware - Unit Converter")
        self.master.geometry("1200x800")
        self.master.minsize(800, 600)
        
        # Set icon if available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '../assets/icon.ico')
            if os.path.exists(icon_path):
                self.master.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")

        # Configure grid layout
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=1)  # Status panel gets all extra space

        # Apply theme from settings
        self._apply_theme()
    
    def _apply_theme(self) -> None:
        """Apply the selected theme from settings."""
        theme = self.settings.get('ui', 'theme')
        
        style = ttk.Style()
        if theme == 'system':
            # Use system theme (default)
            if sys.platform == 'win32':
                style.theme_use('vista')
            elif sys.platform == 'darwin':
                style.theme_use('aqua')
            else:
                style.theme_use('clam')
        elif theme == 'light':
            # Light theme
            style.theme_use('clam')
            style.configure('.', background='#f0f0f0')
        elif theme == 'dark':
            # Dark theme
            style.theme_use('clam')
            style.configure('.', background='#303030', foreground='white')
    
    def _create_menu(self) -> None:
        """Create the menu bar."""
        self.menu_bar = tk.Menu(self.master)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open Configuration...", command=self._open_config)
        self.file_menu.add_command(label="Save Configuration", command=self._save_config)
        self.file_menu.add_command(label="Save Configuration As...", command=self._save_config_as)
        self.file_menu.add_separator()
        
        # Recent configs submenu
        self.recent_menu = tk.Menu(self.file_menu, tearoff=0)
        self._update_recent_menu()
        self.file_menu.add_cascade(label="Recent Configurations", menu=self.recent_menu)
        
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self._on_close)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # Tools menu
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.tools_menu.add_command(label="Settings...", command=self._open_settings)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="Reset Conversion Statistics", command=self._reset_stats)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="Test Configuration", command=self._test_config)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="View Log File", command=self._view_log_file, state=tk.DISABLED)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        
        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Documentation", command=self._open_documentation)
        self.help_menu.add_command(label="About", command=self._show_about)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        # Set menu bar
        self.master.config(menu=self.menu_bar)
    
    def _update_recent_menu(self) -> None:
        """Update the recent configurations menu."""
        # Clear existing items
        self.recent_menu.delete(0, tk.END)
        
        # Add recent configs
        recent_configs = self.settings.settings.ui.recent_configs
        if recent_configs:
            for path in recent_configs:
                self.recent_menu.add_command(
                    label=os.path.basename(path),
                    command=lambda p=path: self._open_config(p)
                )
        else:
            self.recent_menu.add_command(label="No recent configurations", state=tk.DISABLED)
    
    def _setup_log_handler(self, add_text_handler=None) -> None:
        """Set up a custom log handler to show logs in the UI."""
        from condor_udp_middleware.core.log_config import add_text_handler
        add_text_handler(self.log_text)

    def _create_widgets(self) -> None:
        """Create the main window widgets."""
        # Control panel at the top
        self.control_frame = ttk.Frame(self.master, padding="10")
        self.control_frame.grid(row=0, column=0, sticky="ew")
        
        # Left side - main controls
        self.controls_left = ttk.Frame(self.control_frame)
        self.controls_left.pack(side="left", fill="x", expand=True)
        
        # Start/Stop button
        self.start_stop_button = ttk.Button(
            self.controls_left,
            text="Start Middleware",
            command=self._toggle_bridge,
            style="Accent.TButton"
        )
        self.start_stop_button.pack(side="left", padx=5)

        # Settings button
        self.settings_button = ttk.Button(
            self.controls_left,
            text="Settings",
            command=self._open_settings
        )
        self.settings_button.pack(side="left", padx=5)
        
        # Quick conversion toggles
        self.conversion_frame = ttk.LabelFrame(self.controls_left, text="Quick Conversions", padding="5")
        self.conversion_frame.pack(side="left", padx=10, fill="y")
        
        # Conversion enable/disable
        self.conversions_enabled_var = tk.BooleanVar()
        self.conversions_enabled_var.set(self.settings.get('conversions', 'enabled'))
        self.conversions_enabled_check = ttk.Checkbutton(
            self.conversion_frame,
            text="Enable Conversions",
            variable=self.conversions_enabled_var,
            command=self._on_conversions_toggle
        )
        self.conversions_enabled_check.pack(anchor="w")
        
        # Unit dropdowns in a sub-frame
        self.units_frame = ttk.Frame(self.conversion_frame)
        self.units_frame.pack(fill="x", pady=5)
        
        # Altitude unit
        ttk.Label(self.units_frame, text="Altitude:").grid(row=0, column=0, sticky="w", padx=2)
        self.altitude_unit_var = tk.StringVar()
        self.altitude_unit_var.set(self.settings.get('conversions', 'altitude'))
        self.altitude_combo = ttk.Combobox(
            self.units_frame, 
            textvariable=self.altitude_unit_var,
            values=["meters", "feet"],
            width=8,
            state="readonly"
        )
        self.altitude_combo.grid(row=0, column=1, padx=2)
        self.altitude_combo.bind("<<ComboboxSelected>>", self._on_unit_change)
        
        # Speed unit
        ttk.Label(self.units_frame, text="Speed:").grid(row=0, column=2, sticky="w", padx=2)
        self.speed_unit_var = tk.StringVar()
        self.speed_unit_var.set(self.settings.get('conversions', 'speed'))
        self.speed_combo = ttk.Combobox(
            self.units_frame,
            textvariable=self.speed_unit_var,
            values=["mps", "kmh", "knots"],
            width=8,
            state="readonly"
        )
        self.speed_combo.grid(row=0, column=3, padx=2)
        self.speed_combo.bind("<<ComboboxSelected>>", self._on_unit_change)
        
        # Vario unit
        ttk.Label(self.units_frame, text="Vario:").grid(row=1, column=0, sticky="w", padx=2)
        self.vario_unit_var = tk.StringVar()
        self.vario_unit_var.set(self.settings.get('conversions', 'vario'))
        self.vario_combo = ttk.Combobox(
            self.units_frame,
            textvariable=self.vario_unit_var,
            values=["mps", "fpm"],
            width=8,
            state="readonly"
        )
        self.vario_combo.grid(row=1, column=1, padx=2)
        self.vario_combo.bind("<<ComboboxSelected>>", self._on_unit_change)
        
        # Right side - status indicators
        self.indicators_frame = ttk.Frame(self.control_frame)
        self.indicators_frame.pack(side="right", padx=5)
        
        # Input UDP indicator
        self.input_frame = ttk.Frame(self.indicators_frame)
        self.input_frame.pack(side="left", padx=5)
        
        ttk.Label(self.input_frame, text="Input UDP:").pack(side="left")
        self.input_status = ttk.Label(
            self.input_frame,
            text="Stopped",
            foreground="red"
        )
        self.input_status.pack(side="left")
        
        # Output UDP indicator
        self.output_frame = ttk.Frame(self.indicators_frame)
        self.output_frame.pack(side="left", padx=5)
        
        ttk.Label(self.output_frame, text="Output UDP:").pack(side="left")
        self.output_status = ttk.Label(
            self.output_frame,
            text="Stopped",
            foreground="red"
        )
        self.output_status.pack(side="left")
        
        # Status panel with notebook for different views
        self.status_frame = ttk.Frame(self.master, padding="10")
        self.status_frame.grid(row=1, column=0, sticky="nsew")
        
        self.status_notebook = ttk.Notebook(self.status_frame)
        self.status_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Add status panel
        self.status_panel = MiddlewareStatusPanel(self.status_notebook)
        self.status_notebook.add(self.status_panel.frame, text="Status & Data Flow")
        
        # Log panel
        self.log_frame = ttk.Frame(self.status_notebook)
        self.status_notebook.add(self.log_frame, text="Log")
        
        # Log controls
        self.log_controls = ttk.Frame(self.log_frame)
        self.log_controls.pack(fill="x", pady=5)
        
        ttk.Label(self.log_controls, text="Log Level: INFO (fixed for GUI)").pack(side="left")
        
        # Clear log button
        self.clear_log_button = ttk.Button(
            self.log_controls,
            text="Clear Log",
            command=self._clear_log
        )
        self.clear_log_button.pack(side="right", padx=5)
        
        # Log text widget
        log_container = ttk.Frame(self.log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_container,
            wrap=tk.WORD,
            height=10,
            width=80,
            state=tk.DISABLED
        )
        self.log_scrollbar = ttk.Scrollbar(
            log_container,
            orient=tk.VERTICAL,
            command=self.log_text.yview
        )
        self.log_text['yscrollcommand'] = self.log_scrollbar.set
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure custom log handler to show logs in the UI
        self._setup_log_handler()
        
        # Status bar at the bottom
        self.status_bar = ttk.Label(
            self.master,
            text="Ready - Configure ports and start middleware",
            anchor=tk.W,
            padding="5 2"
        )
        self.status_bar.grid(row=2, column=0, sticky="ew")
        
        # Update conversion controls state
        self._update_conversion_controls()
    
    def _clear_log(self) -> None:
        """Clear the log text widget."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _init_bridge(self) -> None:
        """Initialize the bridge instance."""
        try:
            self.bridge = UDPMiddlewareBridge()
            logger.info("Bridge initialized")
            self.status_bar.config(text="Bridge initialized - Ready to start")
        except Exception as e:
            logger.error(f"Error initializing bridge: {e}")
            messagebox.showerror(
                "Initialization Error",
                f"Failed to initialize bridge: {e}"
            )
            self.status_bar.config(text="Bridge initialization failed")
    
    def _toggle_bridge(self) -> None:
        """Start or stop the bridge."""
        if not self.bridge:
            messagebox.showerror(
                "Bridge Error",
                "Bridge not initialized. Please restart the application."
            )
            return
            
        if self.bridge_thread and self.bridge_thread.is_alive():
            # Bridge is running, stop it
            self._stop_bridge()
        else:
            # Bridge is not running, start it
            self._start_bridge()
    
    def _start_bridge(self) -> None:
        """Start the bridge in a separate thread."""
        # Disable the button while starting
        self.start_stop_button.config(state=tk.DISABLED)
        self.status_bar.config(text="Starting middleware...")
        
        # Function to run the bridge in a background thread
        def run_bridge():
            try:
                # Create a new event loop for this thread
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                
                # Start the bridge
                self.loop.run_until_complete(self.bridge.start())
                
                # Update UI in main thread
                self.master.after(0, lambda: self._on_bridge_started())
                
                # Run the event loop
                self.loop.run_forever()
                
            except Exception as e:
                logger.error(f"Error in bridge thread: {e}")
                # Update UI in main thread
                self.master.after(0, lambda: self._on_bridge_error(str(e)))
                
            finally:
                # Clean up
                if self.loop and self.loop.is_running():
                    self.loop.close()
                
                # Update UI in main thread
                self.master.after(0, lambda: self._on_bridge_stopped())
        
        # Start the bridge in a background thread
        self.bridge_thread = threading.Thread(target=run_bridge, daemon=True)
        self.bridge_thread.start()
    
    def _on_bridge_started(self) -> None:
        """Called when the bridge has started."""
        self.start_stop_button.config(text="Stop Middleware", state=tk.NORMAL)
        
        # Get current settings for status
        network = self.settings.get('network')
        self.status_bar.config(
            text=f"Middleware running - Listening on :{network.input_port}, forwarding to {network.output_host}:{network.output_port}"
        )
        
        # Save settings for next time
        self.settings.save()
    
    def _on_bridge_error(self, error_msg: str) -> None:
        """Called when there's an error starting the bridge."""
        self.start_stop_button.config(text="Start Middleware", state=tk.NORMAL)
        self.status_bar.config(text=f"Bridge error: {error_msg}")
        
        messagebox.showerror(
            "Bridge Error",
            f"Failed to start middleware: {error_msg}"
        )
    
    def _stop_bridge(self) -> None:
        """Stop the bridge."""
        if not self.bridge or not self.loop:
            return

        # Disable the button while stopping
        self.start_stop_button.config(state=tk.DISABLED)
        self.status_bar.config(text="Stopping middleware...")

        # Stop the bridge asynchronously
        def stop_async():
            try:
                asyncio.run_coroutine_threadsafe(self.bridge.stop(), self.loop)
            except Exception as e:
                logger.error(f"Error stopping bridge: {e}")
                self.master.after(0, self._on_bridge_stopped)

        # Run in a thread to avoid blocking the GUI
        thread = threading.Thread(target=stop_async, daemon=True)
        thread.start()

        # Start polling to check if the bridge has stopped
        self._poll_bridge_stopped()
    
    def _poll_bridge_stopped(self) -> None:
        """Poll to check if the bridge has stopped."""
        if self.bridge and not self.bridge.running:
            self._on_bridge_stopped()
        elif self.bridge_thread and not self.bridge_thread.is_alive():
            self._on_bridge_stopped()
        else:
            # Continue polling every 100ms
            self.master.after(100, self._poll_bridge_stopped)
    
    def _on_bridge_stopped(self) -> None:
        """Called when the bridge has stopped."""
        self.start_stop_button.config(text="Start Middleware", state=tk.NORMAL)
        self.status_bar.config(text="Middleware stopped")
    
    def _update_status(self) -> None:
        """Update status displays periodically."""
        if self.bridge and self.bridge.running:
            try:
                # Get bridge status
                status = self.bridge.get_status()

                # Validate status before updating UI
                if status and isinstance(status, dict):
                    # Update status panel
                    self.status_panel.update_status(status)

                    # Update connection indicators
                    self._update_connection_indicators(status)
                else:
                    logger.warning("Invalid status received from bridge")
                    self._update_connection_indicators(None)
                    self.status_panel.reset_status()

            except Exception as e:
                logger.error(f"Error updating status: {e}")
                # On error, show disconnected status
                self._update_connection_indicators(None)
                self.status_panel.reset_status()
        else:
            # Bridge not running, show disconnected status
            self._update_connection_indicators(None)
            self.status_panel.reset_status()
        
        # Schedule next update
        self.master.after(1000, self._update_status)
    
    def _update_connection_indicators(self, status: Optional[Dict[str, Any]]) -> None:
        """Update the connection status indicators."""
        if not status:
            # Not running, all disconnected
            self.input_status.config(text="Stopped", foreground="red")
            self.output_status.config(text="Stopped", foreground="red")
            return
        
        # Input UDP status
        if 'input_udp' in status and status['input_udp']:
            input_udp = status['input_udp']
            if input_udp['running']:
                self.input_status.config(text="Active", foreground="green")
            else:
                self.input_status.config(text="Error", foreground="orange")
        else:
            self.input_status.config(text="Stopped", foreground="red")
        
        # Output UDP status
        if 'output_udp' in status and status['output_udp']:
            output_udp = status['output_udp']
            if output_udp['active']:
                self.output_status.config(text="Active", foreground="green")
            else:
                self.output_status.config(text="Error", foreground="orange")
        else:
            self.output_status.config(text="Stopped", foreground="red")
    
    def _on_conversions_toggle(self) -> None:
        """Handle conversion enable/disable toggle."""
        enabled = self.conversions_enabled_var.get()
        
        # Update settings
        self.settings.set('conversions', 'enabled', enabled)
        
        # Update bridge if running
        if self.bridge:
            self.bridge.update_conversion_settings({'enabled': enabled})
        
        # Update UI
        self._update_conversion_controls()
        
        logger.info(f"Conversions {'enabled' if enabled else 'disabled'}")
    
    def _on_unit_change(self, event=None) -> None:
        """Handle unit dropdown changes."""
        # Update settings
        self.settings.set('conversions', 'altitude', self.altitude_unit_var.get())
        self.settings.set('conversions', 'speed', self.speed_unit_var.get())
        self.settings.set('conversions', 'vario', self.vario_unit_var.get())
        
        # Update bridge if running
        if self.bridge:
            conversion_settings = {
                'altitude': self.altitude_unit_var.get(),
                'speed': self.speed_unit_var.get(),
                'vario': self.vario_unit_var.get()
            }
            self.bridge.update_conversion_settings(conversion_settings)
        
        logger.info(f"Unit settings updated: altitude={self.altitude_unit_var.get()}, "
                   f"speed={self.speed_unit_var.get()}, vario={self.vario_unit_var.get()}")
    
    def _update_conversion_controls(self) -> None:
        """Update the state of conversion controls."""
        enabled = self.conversions_enabled_var.get()
        state = "normal" if enabled else "disabled"
        
        self.altitude_combo.config(state="readonly" if enabled else "disabled")
        self.speed_combo.config(state="readonly" if enabled else "disabled")
        self.vario_combo.config(state="readonly" if enabled else "disabled")
    
    def _open_config(self, path: Optional[str] = None) -> None:
        """Open a configuration file."""
        if not path:
            path = filedialog.askopenfilename(
                title="Open Configuration",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            
        if path:
            if self.bridge.update_settings(path):
                self.settings = self.bridge.settings
                self._refresh_ui_from_settings()
                self.settings.add_recent_config(path)
                self._update_recent_menu()
                self.status_bar.config(text=f"Loaded configuration from {path}")
            else:
                messagebox.showerror(
                    "Configuration Error",
                    f"Failed to load configuration from {path}"
                )
    
    def _save_config(self) -> None:
        """Save the current configuration."""
        if self.settings.save():
            self.status_bar.config(text=f"Configuration saved to {self.settings.config_file}")
        else:
            messagebox.showerror("Configuration Error", "Failed to save configuration")
    
    def _save_config_as(self) -> None:
        """Save the configuration to a new file."""
        path = filedialog.asksaveasfilename(
            title="Save Configuration As",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if path:
            if self.settings.save(path):
                self.settings.add_recent_config(path)
                self._update_recent_menu()
                self.status_bar.config(text=f"Configuration saved to {path}")
            else:
                messagebox.showerror("Configuration Error", f"Failed to save configuration to {path}")
    
    def _open_settings(self) -> None:
        """Open the settings dialog."""
        dialog = MiddlewareSettingsDialog(self.master, self.settings)
        
        if dialog.result:
            self._apply_settings_changes()
    
    def _apply_settings_changes(self) -> None:
        """Apply changes to settings."""
        # Apply theme
        self._apply_theme()
        
        # Apply logging settings
        self.settings.apply_logging_settings()
        
        # Refresh UI from settings
        self._refresh_ui_from_settings()
        
        # If bridge is running, ask to restart
        if self.bridge and self.bridge.running:
            if messagebox.askyesno(
                "Restart Required",
                "Settings have changed. Restart the middleware to apply them?"
            ):
                self._stop_bridge()
                self.master.after(1000, self._start_bridge)
            else:
                self.settings.save()
        else:
            self.settings.save()
    
    def _refresh_ui_from_settings(self) -> None:
        """Refresh UI controls from current settings."""
        # Update conversion controls
        self.conversions_enabled_var.set(self.settings.get('conversions', 'enabled'))
        self.altitude_unit_var.set(self.settings.get('conversions', 'altitude'))
        self.speed_unit_var.set(self.settings.get('conversions', 'speed'))
        self.vario_unit_var.set(self.settings.get('conversions', 'vario'))
        
        self._update_conversion_controls()
    
    def _reset_stats(self) -> None:
        """Reset conversion statistics."""
        if self.bridge and hasattr(self.bridge, 'unit_converter'):
            self.bridge.unit_converter.reset_statistics()
            messagebox.showinfo("Statistics Reset", "Conversion statistics have been reset.")
        else:
            messagebox.showwarning("No Statistics", "No statistics to reset (middleware not running).")
    
    def _test_config(self) -> None:
        """Test current configuration."""
        errors = self.settings.validate()
        if errors:
            error_msg = "Configuration errors found:\n\n"
            for section, section_errors in errors.items():
                error_msg += f"[{section}]\n"
                for error in section_errors:
                    error_msg += f"  - {error}\n"
            messagebox.showerror("Configuration Test Failed", error_msg)
        else:
            messagebox.showinfo("Configuration Test Passed", "Configuration is valid!")
    
    def _view_log_file(self) -> None:
        """Open the log file in the default text editor."""
        log_file = self.settings.get('logging', 'log_file_path')
        if log_file and os.path.exists(log_file):
            if sys.platform == 'win32':
                os.startfile(log_file)
            elif sys.platform == 'darwin':
                os.system(f'open "{log_file}"')
            else:
                os.system(f'xdg-open "{log_file}"')
        else:
            messagebox.showerror("Log File Error", "Log file not found or logging to file is disabled")
    
    def _open_documentation(self) -> None:
        """Open the documentation."""
        messagebox.showinfo("Documentation", "Documentation for Condor UDP Middleware\n\nThis middleware converts units in real-time between Condor and external applications.")
    
    def _show_about(self) -> None:
        """Show the about dialog."""
        messagebox.showinfo(
            "About Condor UDP Middleware",
            "Condor UDP Middleware\n\n"
            "Version: 1.0.0\n\n"
            "A unit conversion middleware for Condor Soaring Simulator.\n"
            "Converts altitude, speed, vario and acceleration units in real-time.\n\n"
            "Built with Python and inspired by Condor-Shirley-Bridge architecture."
        )
    
    def _show_first_run_message(self) -> None:
        """Show a welcome message for first-time users."""
        messagebox.showinfo(
            "Welcome to Condor UDP Middleware",
            "Welcome to Condor UDP Middleware!\n\n"
            "This appears to be your first time running the application.\n\n"
            "Please configure your network ports and unit conversion preferences "
            "in Settings before starting the middleware.\n\n"
            "The middleware will listen for UDP data from Condor, convert units "
            "according to your preferences, and forward the data to another application."
        )
    
    def _on_close(self) -> None:
        """Handle window close event."""
        if self.bridge and self.bridge.running:
            if not messagebox.askyesno(
                    "Quit",
                    "The middleware is still running. Are you sure you want to quit?"
            ):
                return

            # Stop the bridge
            self._stop_bridge()

            # Wait a moment to let it stop cleanly
            self.master.after(200)

        # Remove the text handler before closing
        from condor_udp_middleware.core.log_config import remove_text_handler
        remove_text_handler()

        # Save settings
        self.settings.save()

        # Destroy the window
        self.master.destroy()


# Run the application if this script is executed directly
if __name__ == "__main__":
    root = tk.Tk()
    app = MiddlewareMainWindow(root)
    root.mainloop()