# 💡 Svitlo CLI

Terminal TUI app for monitoring power outage schedules in Lviv.

## 📋 Features

- 🎨 Compact minimalistic TUI interface
- 📊 24-hour timeline with colored indicators
- ⏱️ Timer to next change (updates every second)
- ⚡ Current light status
- 📍 Support for all outage groups (1.1-6.2)
- 🔄 Automatic data updates

## 🚀 Installation

### Method 1: Automatic installation (recommended)

```bash
cd svitlo-cli
./install.sh
```

After installation you can run from any directory:
```bash
svitlo-cli
```

### Method 2: Manual installation via pip

```bash
cd svitlo-cli
pip install -e .
```

### Method 3: Local run

```bash
cd svitlo-cli
pip install -r requirements.txt
python3 run.py
```

### Method 4: Homebrew (macOS)

Create your own tap or use ready formula:
```bash
brew install svitlo-cli
```

## 🎮 Usage

After installation:
```bash
svitlo-cli
```

Or for local run:
```bash
python3 run.py
```

## 📦 Uninstallation

```bash
pip uninstall svitlo-cli
```

### Key bindings

- `r` - Show/hide current status and refresh button
- `s` - Enable/disable auto-refresh
- `q` - Exit

### Display

- **Timeline at top**: 24 blocks with colored light status for each hour
- **Bottom blocks** (hidden by default, shown with `R`):
  - Current light status
  - Refresh button
  - Timer to next change
- **Colors**: Orange - light is on, Dark - light is off

## 📦 Dependencies

- `textual` - TUI framework
- `requests` - HTTP client
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast HTML parser

## ⚠️ Important Note

**Currently using test data!**

The official website https://poweron.loe.lviv.ua has no public API and content is generated via JavaScript, so it's impossible to get real data with simple HTTP requests.

## 🎨 Color Scheme

- 🟠 Orange (#FF7C09) - Light is on
- ⬛ Dark (#0d0d0d) - Light is off
- ⬜ Black border (#000) - Current hour
- ⬛ Black background (#000000) - Console design
- ⬜ White (#fff) - Main text
- ⬛ Dark gray (#666) - Text when no light
# svitlo-cli
