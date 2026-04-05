# Screenshot Capture

A full UI screenshot could not be captured automatically in this environment because GTK runtime bindings were unavailable (`gi` import failed).

Use these steps on a desktop Linux session after installing GTK dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev,nlp,secrets]
```

Install GTK runtime packages (Debian/Ubuntu):

```bash
sudo apt-get update
sudo apt-get install -y \
  python3-gi python3-gi-cairo \
  gir1.2-gtk-4.0 gir1.2-adw-1 \
  libgirepository1.0-dev libcairo2-dev pkg-config
```

Run the app:

```bash
privacyguard
```

Capture screenshot (GNOME):

```bash
gnome-screenshot -w -f docs/screenshot.png
```

Alternative (if `gnome-screenshot` is not installed):

```bash
grim -g "$(slurp)" docs/screenshot.png
```
