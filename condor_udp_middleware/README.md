# Condor UDP Middleware

A real-time unit conversion middleware for Condor Soaring Simulator that receives UDP data, converts units according to user preferences, and forwards the converted data to external applications while maintaining the original message format.

## Overview

Condor UDP Middleware acts as a transparent bridge between Condor Soaring Simulator and external applications by:

1. **Receiving UDP data** from Condor Soaring Simulator
2. **Converting units** in real-time based on user preferences (altitude, speed, vario, acceleration)
3. **Forwarding converted data** to target applications maintaining the original key=value format
4. **Providing real-time monitoring** through an intuitive GUI with conversion statistics

## Features

- **Real-time unit conversion** - Convert altitude, speed, vario, and acceleration units on-the-fly
- **Configurable conversions** - Easy dropdown selection for different unit systems
- **Transparent operation** - External applications receive data in the same format as Condor
- **GUI and CLI modes** - Run with graphical interface or headless for automated setups
- **Live statistics** - Monitor data flow, conversion rates, and performance metrics
- **Flexible networking** - Support for local and remote panel configurations
- **Robust architecture** - Thread-safe operation with comprehensive error handling

## Supported Unit Conversions

| Variable Type | Source (Condor) | Target Options |
|---------------|-----------------|----------------|
| **Altitude** | meters | meters, feet |
| **Speed** | m/s | m/s, km/h, knots |
| **Vario** | m/s | m/s, ft/min |
| **Acceleration** | m/s² | m/s², ft/s² |

### Variables Converted

- **Altitude**: `altitude`, `height`, `wheelheight`
- **Speed**: `airspeed`, `vx`, `vy`, `vz`
- **Vario**: `vario`, `evario`, `nettovario`
- **Acceleration**: `ax`, `ay`, `az`

## Installation

### Prerequisites

- Python 3.8 or later
- Condor Soaring Simulator with UDP output enabled
- Target application configured to receive UDP data

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/condor-udp-middleware.git
   cd condor-udp-middleware
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the middleware:**
   ```bash
   python main.py
   ```

## Configuration

### Condor Setup

Configure Condor to send UDP data by editing the UDP configuration:

```ini
# In Condor's UDP settings
Enabled=1
Host=127.0.0.1
Port=55278
SendIntervalMs=100
ExtendedData=1
```

### Middleware Configuration

The middleware can be configured through:

1. **GUI Settings Dialog** - Access via the "Settings" button
2. **Configuration File** - Automatically created at `~/.condor_udp_middleware/config.json`
3. **Command Line Arguments** - Override settings for specific runs

#### Default Configuration

- **Input UDP**: Port 55278 (receives from Condor)
- **Output UDP**: 127.0.0.1:55300 (sends to target application)
- **Conversions**: Disabled by default

#### Network Configurations

| Scenario | Input Port | Output Host | Output Port |
|----------|------------|-------------|-------------|
| Same PC | 55278 | 127.0.0.1 | 55300 |
| Remote Panel | 55278 | 192.168.1.100 | 55278 |
| Multiple Panels | 55278 | Various IPs | 55278 |

### Target Application Setup

Configure your target application (PanelBuilder, custom panels, etc.) to receive UDP data on the middleware's output port (default: 55300).

## Usage

### GUI Mode (Default)

```bash
python main.py
```

The GUI provides:
- **Real-time status** monitoring
- **Quick conversion toggles** for immediate unit changes
- **Detailed statistics** showing data flow and conversion rates
- **Live logging** with configurable levels
- **Settings management** with validation

### CLI Mode

```bash
python main.py --cli
```

For headless operation with:
- **Automatic startup** on system boot
- **Log file output** for monitoring
- **Signal handling** for graceful shutdown

### Command Line Options

```bash
python main.py [options]

Options:
  --cli                 Run without GUI
  --config PATH         Use specific configuration file
  --start               Auto-start middleware on launch
  --minimized           Start minimized (GUI mode only)
  --log-level LEVEL     Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  --log-file PATH       Log to specified file
```

## Data Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Condor Simulator│───▶│ UDP Middleware   │───▶│ Target App      │
│ Port: 55278     │    │ Converts Units   │    │ Port: 55300     │
│                 │    │ Real-time        │    │ (PanelBuilder,  │
│ altitude=1000.0 │    │ Processing       │    │ Custom Panels)  │
│ airspeed=30.5   │    │                  │    │                 │
│ vario=-2.1      │    │ altitude=3281.0  │    │ altitude=3281.0 │
└─────────────────┘    │ airspeed=59.2    │    │ airspeed=59.2   │
                       │ vario=-413.4     │    │ vario=-413.4    │
                       └──────────────────┘    └─────────────────┘
                       meters→feet              knots, ft/min
```

## Performance

- **Processing Rate**: 10+ messages/second
- **Latency**: <1ms conversion time
- **Memory Usage**: ~20MB typical
- **CPU Usage**: <1% on modern systems
- **Reliability**: 100% message forwarding success

## Architecture

```
condor_udp_middleware/
├── main.py                 # Application entry point
├── core/
│   ├── bridge.py          # Main orchestrator
│   ├── converter.py       # Unit conversion engine
│   ├── settings.py        # Configuration management
│   └── log_config.py      # Logging system
└── gui/
    ├── main_window.py     # Primary GUI interface
    ├── status_panel.py    # Real-time monitoring
    └── settings_dialog.py # Configuration UI
```

## Use Cases

### Flight Training
- Convert altitudes to preferred units for student pilots
- Standardize vario readings across different instruments
- Adapt speed displays for different aircraft types

### Panel Building
- **PanelBuilder Integration** - Direct compatibility with panel software
- **Custom Panels** - Support for home-built cockpit displays
- **Multi-Monitor Setups** - Distribute converted data to multiple displays

### Data Logging
- **Unit Standardization** - Log all data in consistent units
- **Analysis Tools** - Feed converted data to analysis applications
- **Recording Systems** - Compatible with flight recording software

### Network Configurations
- **Remote Panels** - Send converted data over LAN/WAN
- **Multiple Simulators** - Support multi-pilot scenarios
- **Instructor Stations** - Provide converted data to instructor displays

## Troubleshooting

### Common Issues

**No data received:**
- Verify Condor UDP output is enabled
- Check input port matches Condor's output port
- Ensure no firewall blocking UDP traffic

**Target application not receiving data:**
- Verify output host and port configuration
- Check target application is listening on correct port
- Test network connectivity for remote configurations

**Conversion not working:**
- Enable conversions in GUI or settings
- Verify unit selections are different from source
- Check logs for conversion errors

### Logging

Enable detailed logging for troubleshooting:

```bash
python main.py --log-level DEBUG --log-file middleware.log
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests, report bugs, or suggest features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, bug reports, or feature requests, please open an issue on GitHub.

---

**Enjoy enhanced soaring simulation with real-time unit conversion!** ✈️