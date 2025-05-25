#!/usr/bin/env python3

"""
Settings Dialog for Condor UDP Middleware
Dialog for configuring application settings including unit conversions.

Part of the Condor UDP Middleware project.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import os
from typing import Optional, Dict, Any

from condor_udp_middleware.core.settings import MiddlewareSettings

# Configure logging
logger = logging.getLogger('gui.settings_dialog')


class MiddlewareSettingsDialog:
    """
    Dialog for configuring middleware settings.
    
    Provides a UI for changing all settings in the application,
    organized by category using a notebook.
    """
    
    def __init__(self, parent, settings: MiddlewareSettings):
        """
        Initialize the settings dialog.
        
        Args:
            parent: Parent widget
            settings: Settings instance
        """
        self.parent = parent
        self.settings = settings
        self.result = False  # True if settings were changed and OK was clicked
        
        # Create the dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Middleware Settings")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Set dialog size
        self.dialog.geometry("650x600")
        self.dialog.minsize(600, 500)
        
        # Center on parent
        if parent:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            
            dialog_width = 650
            dialog_height = 600
            
            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2
            
            self.dialog.geometry(f"+{x}+{y}")
        
        # Make dialog modal
        self.dialog.focus_set()
        
        # Create widgets
        self._create_widgets()
        
        # Initialize values from settings
        self._load_settings()
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def _create_widgets(self) -> None:
        """Create the dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook for settings categories
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create settings tabs
        self._create_network_tab()
        self._create_conversions_tab()
        self._create_logging_tab()
        self._create_ui_tab()
        
        # Button frame at the bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # OK and Cancel buttons
        self.ok_button = ttk.Button(button_frame, text="OK", command=self._on_ok)
        self.ok_button.pack(side=tk.RIGHT, padx=5)
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self._on_cancel)
        self.cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # Apply button
        self.apply_button = ttk.Button(button_frame, text="Apply", command=self._on_apply)
        self.apply_button.pack(side=tk.RIGHT, padx=5)
        
        # Test button
        self.test_button = ttk.Button(button_frame, text="Test Configuration", command=self._on_test)
        self.test_button.pack(side=tk.LEFT, padx=5)
    
    def _create_network_tab(self) -> None:
        """Create the Network settings tab."""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="Network")
        
        # Input UDP settings
        input_frame = ttk.LabelFrame(frame, text="Input UDP (from Condor)", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Port:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_port_var = tk.IntVar()
        self.input_port = ttk.Spinbox(
            input_frame,
            from_=1024,
            to=65535,
            textvariable=self.input_port_var,
            width=10
        )
        self.input_port.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(input_frame, text="Default: 55278 (Condor's default UDP port)", 
                  font=("", 8, "italic"), foreground="gray").grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        # Output UDP settings
        output_frame = ttk.LabelFrame(frame, text="Output UDP (to target application)", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.output_host_var = tk.StringVar()
        self.output_host = ttk.Entry(
            output_frame,
            textvariable=self.output_host_var,
            width=20
        )
        self.output_host.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(output_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_port_var = tk.IntVar()
        self.output_port = ttk.Spinbox(
            output_frame,
            from_=1024,
            to=65535,
            textvariable=self.output_port_var,
            width=10
        )
        self.output_port.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(output_frame, text="Default: 127.0.0.1:55300", 
                  font=("", 8, "italic"), foreground="gray").grid(row=2, column=0, columnspan=2, sticky=tk.W)
        
        # Configuration examples
        examples_frame = ttk.LabelFrame(frame, text="Configuration Examples", padding="10")
        examples_frame.pack(fill=tk.X, pady=5)
        
        examples_text = tk.Text(examples_frame, height=6, wrap=tk.WORD, font=("", 8))
        examples_text.pack(fill=tk.X)
        
        example_content = """Example configurations:

1. Same computer: Input=55278, Output=127.0.0.1:55300
   Condor → Middleware → Local application

2. Network setup: Input=55278, Output=192.168.1.100:55278  
   Condor → Middleware → Remote computer

3. Chain setup: Input=55278, Output=127.0.0.1:55279
   Condor → Middleware → Another middleware/application"""
        
        examples_text.insert('1.0', example_content)
        examples_text.config(state=tk.DISABLED)
    
    def _create_conversions_tab(self) -> None:
        """Create the Unit Conversions settings tab."""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="Unit Conversions")
        
        # Master enable/disable
        self.conversions_enabled_var = tk.BooleanVar()
        self.conversions_enabled = ttk.Checkbutton(
            frame,
            text="Enable unit conversions",
            variable=self.conversions_enabled_var,
            command=self._update_conversion_state
        )
        self.conversions_enabled.pack(anchor=tk.W, pady=10)
        
        # Conversion settings frame
        self.conversions_frame = ttk.LabelFrame(frame, text="Unit Preferences", padding="10")
        self.conversions_frame.pack(fill=tk.X, pady=5)
        
        # Altitude conversion
        ttk.Label(self.conversions_frame, text="Altitude:", font=("", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.altitude_unit_var = tk.StringVar()
        self.altitude_unit = ttk.Combobox(
            self.conversions_frame,
            textvariable=self.altitude_unit_var,
            values=["meters", "feet"],
            width=15,
            state="readonly"
        )
        self.altitude_unit.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Label(self.conversions_frame, text="Variables: altitude, height, wheelheight", 
                  font=("", 8), foreground="gray").grid(row=0, column=2, sticky=tk.W, padx=10)
        
        # Speed conversion
        ttk.Label(self.conversions_frame, text="Speed:", font=("", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.speed_unit_var = tk.StringVar()
        self.speed_unit = ttk.Combobox(
            self.conversions_frame,
            textvariable=self.speed_unit_var,
            values=["mps", "kmh", "knots"],
            width=15,
            state="readonly"
        )
        self.speed_unit.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Label(self.conversions_frame, text="Variables: airspeed, vx, vy, vz", 
                  font=("", 8), foreground="gray").grid(row=1, column=2, sticky=tk.W, padx=10)
        
        # Vario conversion
        ttk.Label(self.conversions_frame, text="Vario:", font=("", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.vario_unit_var = tk.StringVar()
        self.vario_unit = ttk.Combobox(
            self.conversions_frame,
            textvariable=self.vario_unit_var,
            values=["mps", "fpm"],
            width=15,
            state="readonly"
        )
        self.vario_unit.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Label(self.conversions_frame, text="Variables: vario, evario, nettovario", 
                  font=("", 8), foreground="gray").grid(row=2, column=2, sticky=tk.W, padx=10)
        
        # Acceleration conversion
        ttk.Label(self.conversions_frame, text="Acceleration:", font=("", 9, "bold")).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.acceleration_unit_var = tk.StringVar()
        self.acceleration_unit = ttk.Combobox(
            self.conversions_frame,
            textvariable=self.acceleration_unit_var,
            values=["mps2", "fps2"],
            width=15,
            state="readonly"
        )
        self.acceleration_unit.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Label(self.conversions_frame, text="Variables: ax, ay, az", 
                  font=("", 8), foreground="gray").grid(row=3, column=2, sticky=tk.W, padx=10)
        
        # Conversion factors info
        factors_frame = ttk.LabelFrame(frame, text="Conversion Factors Reference", padding="10")
        factors_frame.pack(fill=tk.X, pady=5)
        
        factors_text = tk.Text(factors_frame, height=8, wrap=tk.WORD, font=("Consolas", 8))
        factors_text.pack(fill=tk.X)
        
        factors_content = """Conversion factors used:

Altitude:  1 meter = 3.28084 feet
Speed:     1 m/s = 3.6 km/h = 1.94384 knots  
Vario:     1 m/s = 196.85 ft/min
Accel:     1 m/s² = 3.28084 ft/s²

Note: Condor outputs data in metric units by default.
Variables not configured for conversion pass through unchanged."""
        
        factors_text.insert('1.0', factors_content)
        factors_text.config(state=tk.DISABLED)
    
    def _create_logging_tab(self) -> None:
        """Create the Logging settings tab."""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="Logging")
        
        # Log level
        ttk.Label(frame, text="Log Level:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.log_level_var = tk.StringVar()
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self.log_level = ttk.Combobox(
            frame,
            textvariable=self.log_level_var,
            values=log_levels,
            width=10,
            state="readonly"
        )
        self.log_level.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame, text="Note: GUI always shows INFO level and above", 
                  font=("", 8, "italic"), foreground="gray").grid(row=0, column=2, sticky=tk.W, padx=10)
        
        # Log to file checkbox
        self.log_to_file_var = tk.BooleanVar()
        self.log_to_file = ttk.Checkbutton(
            frame,
            text="Log to File",
            variable=self.log_to_file_var,
            command=self._update_log_file_state
        )
        self.log_to_file.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Log file path
        ttk.Label(frame, text="Log File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        log_file_frame = ttk.Frame(frame)
        log_file_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        self.log_file_var = tk.StringVar()
        self.log_file = ttk.Entry(
            log_file_frame,
            textvariable=self.log_file_var,
            width=40
        )
        self.log_file.pack(side=tk.LEFT)
        
        # Browse button for log file
        browse_button = ttk.Button(
            log_file_frame,
            text="Browse",
            command=self._browse_log_file
        )
        browse_button.pack(side=tk.LEFT, padx=5)
        
        # Max log files
        ttk.Label(frame, text="Max Log Files:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        self.max_log_files_var = tk.IntVar()
        self.max_log_files = ttk.Spinbox(
            frame,
            from_=1,
            to=20,
            textvariable=self.max_log_files_var,
            width=5
        )
        self.max_log_files.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Max log size
        ttk.Label(frame, text="Max Log Size (MB):").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.max_log_size_var = tk.IntVar()
        self.max_log_size = ttk.Spinbox(
            frame,
            from_=1,
            to=100,
            textvariable=self.max_log_size_var,
            width=5
        )
        self.max_log_size.grid(row=4, column=1, sticky=tk.W, pady=5)
    
    def _create_ui_tab(self) -> None:
        """Create the UI settings tab."""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="User Interface")
        
        # Theme selection
        ttk.Label(frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.theme_var = tk.StringVar()
        themes = ["system", "light", "dark"]
        self.theme = ttk.Combobox(
            frame,
            textvariable=self.theme_var,
            values=themes,
            width=10,
            state="readonly"
        )
        self.theme.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Auto-start option
        self.auto_start_var = tk.BooleanVar()
        self.auto_start = ttk.Checkbutton(
            frame,
            text="Auto-start middleware on application launch",
            variable=self.auto_start_var
        )
        self.auto_start.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Start minimized option
        self.start_minimized_var = tk.BooleanVar()
        self.start_minimized = ttk.Checkbutton(
            frame,
            text="Start application minimized",
            variable=self.start_minimized_var
        )
        self.start_minimized.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Clear recent configs button
        clear_button = ttk.Button(
            frame,
            text="Clear Recent Configurations",
            command=self._clear_recent_configs
        )
        clear_button.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=20)
    
    def _load_settings(self) -> None:
        """Load settings values into the UI."""
        # Network settings
        network = self.settings.get('network')
        self.input_port_var.set(network.input_port)
        self.output_host_var.set(network.output_host)
        self.output_port_var.set(network.output_port)
        
        # Conversion settings
        conversions = self.settings.get('conversions')
        self.conversions_enabled_var.set(conversions.enabled)
        self.altitude_unit_var.set(conversions.altitude)
        self.speed_unit_var.set(conversions.speed)
        self.vario_unit_var.set(conversions.vario)
        self.acceleration_unit_var.set(conversions.acceleration)
        
        # Update conversion controls state
        self._update_conversion_state()
        
        # Logging settings
        logging_settings = self.settings.get('logging')
        self.log_level_var.set(logging_settings.level)
        self.log_to_file_var.set(logging_settings.log_to_file)
        self.log_file_var.set(logging_settings.log_file_path or "")
        self.max_log_files_var.set(logging_settings.max_log_files)
        self.max_log_size_var.set(logging_settings.max_log_size_mb)
        
        # Update log file controls state
        self._update_log_file_state()
        
        # UI settings
        ui_settings = self.settings.get('ui')
        self.theme_var.set(ui_settings.theme)
        self.auto_start_var.set(ui_settings.auto_start)
        self.start_minimized_var.set(ui_settings.start_minimized)
    
    def _save_settings(self) -> bool:
        """
        Save UI values to settings.
        
        Returns:
            bool: True if settings were saved successfully
        """
        try:
            # Network settings
            self.settings.set('network', 'input_port', self.input_port_var.get())
            self.settings.set('network', 'output_host', self.output_host_var.get())
            self.settings.set('network', 'output_port', self.output_port_var.get())
            
            # Conversion settings
            self.settings.set('conversions', 'enabled', self.conversions_enabled_var.get())
            self.settings.set('conversions', 'altitude', self.altitude_unit_var.get())
            self.settings.set('conversions', 'speed', self.speed_unit_var.get())
            self.settings.set('conversions', 'vario', self.vario_unit_var.get())
            self.settings.set('conversions', 'acceleration', self.acceleration_unit_var.get())
            
            # Logging settings
            self.settings.set('logging', 'level', self.log_level_var.get())
            self.settings.set('logging', 'log_to_file', self.log_to_file_var.get())
            self.settings.set('logging', 'log_file_path', self.log_file_var.get())
            self.settings.set('logging', 'max_log_files', self.max_log_files_var.get())
            self.settings.set('logging', 'max_log_size_mb', self.max_log_size_var.get())
            
            # UI settings
            self.settings.set('ui', 'theme', self.theme_var.get())
            self.settings.set('ui', 'auto_start', self.auto_start_var.get())
            self.settings.set('ui', 'start_minimized', self.start_minimized_var.get())
            
            # Validate settings
            validation_errors = self.settings.validate()
            if validation_errors:
                # Show validation errors
                error_message = "Invalid settings:\n\n"
                for section, errors in validation_errors.items():
                    error_message += f"[{section}]\n"
                    for error in errors:
                        error_message += f"- {error}\n"
                    error_message += "\n"
                
                messagebox.showerror("Validation Error", error_message)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Settings Error", f"Failed to save settings: {e}")
            return False
    
    def _update_conversion_state(self) -> None:
        """Update the state of conversion controls based on enabled state."""
        state = "readonly" if self.conversions_enabled_var.get() else "disabled"
        
        self.altitude_unit.config(state=state)
        self.speed_unit.config(state=state)
        self.vario_unit.config(state=state)
        self.acceleration_unit.config(state=state)
    
    def _update_log_file_state(self) -> None:
        """Update the state of log file controls based on log_to_file state."""
        state = "normal" if self.log_to_file_var.get() else "disabled"
        
        self.log_file.config(state=state)
        self.max_log_files.config(state=state)
        self.max_log_size.config(state=state)
    
    def _browse_log_file(self) -> None:
        """Open file dialog to select log file path."""
        current_path = self.log_file_var.get()
        initial_dir = os.path.dirname(current_path) if current_path else None
        
        path = filedialog.asksaveasfilename(
            title="Select Log File",
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("All Files", "*.*")],
            initialdir=initial_dir
        )
        
        if path:
            self.log_file_var.set(path)
    
    def _clear_recent_configs(self) -> None:
        """Clear the list of recent configurations."""
        if messagebox.askyesno(
            "Clear Recent Configurations",
            "Are you sure you want to clear the list of recent configurations?"
        ):
            self.settings.settings.ui.recent_configs = []
            messagebox.showinfo(
                "Recent Configurations",
                "Recent configurations list has been cleared."
            )
    
    def _on_test(self) -> None:
        """Handle Test Configuration button click."""
        # Save current values temporarily for testing
        temp_settings = self.settings.settings
        
        try:
            # Apply current UI values to temporary settings
            self._save_settings()
            
            # Validate
            errors = self.settings.validate()
            if errors:
                error_msg = "Configuration errors found:\n\n"
                for section, section_errors in errors.items():
                    error_msg += f"[{section}]\n"
                    for error in section_errors:
                        error_msg += f"  - {error}\n"
                messagebox.showerror("Configuration Test Failed", error_msg)
            else:
                # Show configuration summary
                network = self.settings.get('network')
                conversions = self.settings.get('conversions')
                
                summary = f"""Configuration Test Passed!

Network Configuration:
  Input UDP: Port {network.input_port}
  Output UDP: {network.output_host}:{network.output_port}

Unit Conversions: {'Enabled' if conversions.enabled else 'Disabled'}"""
                
                if conversions.enabled:
                    summary += f"""
  Altitude: {conversions.altitude}
  Speed: {conversions.speed}  
  Vario: {conversions.vario}
  Acceleration: {conversions.acceleration}"""
                
                messagebox.showinfo("Configuration Test Passed", summary)
                
        except Exception as e:
            messagebox.showerror("Configuration Test Error", f"Error testing configuration: {e}")
    
    def _on_ok(self) -> None:
        """Handle OK button click."""
        if self._save_settings():
            self.result = True
            self.dialog.destroy()
    
    def _on_apply(self) -> None:
        """Handle Apply button click."""
        if self._save_settings():
            self.result = True
    
    def _on_cancel(self) -> None:
        """Handle Cancel button click."""
        self.result = False
        self.dialog.destroy()


# Example usage:
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Settings Dialog Test")
    root.geometry("300x200")
    
    # Create a button to open the dialog
    def open_settings():
        settings = MiddlewareSettings()
        dialog = MiddlewareSettingsDialog(root, settings)
        if dialog.result:
            print("Settings were changed")
        else:
            print("Settings were not changed")
    
    button = ttk.Button(root, text="Open Settings", command=open_settings)
    button.pack(expand=True)
    
    root.mainloop()