#!/usr/bin/env python3
"""
Patch inky 2.x to work with the Inky Impression 7.3" 2025 Edition (E673/Spectra 6)
on Raspberry Pi OS Bullseye.

Problem: inky 2.x uses gpiod to claim and manually toggle CE0 (GPIO 8) as a
chip-select pin. But the kernel's spi-bcm2835 driver permanently owns CE0 —
gpiod cannot claim a pin held by a kernel driver, so display init fails with
OSError: [Errno 16] Device or resource busy.

Fix: remove CE0 from gpiod management in inky_e673.py. The hardware SPI
controller already toggles CE0 automatically during every spidev transfer,
making the manual gpiod calls redundant.

Also patches gpiodevice to suppress the "Woah there, pins in use" warning
for SPI-owned pins (cosmetic — doesn't affect function).

Run from the PaperPiAI directory on the Pi after any `pip install inky --upgrade`:
    venv/bin/python scripts/patch_inky_e673.py
"""

import sys
import site
from pathlib import Path

# Find the venv site-packages
venv_site = Path(sys.executable).parent.parent / "lib"
candidates = list(venv_site.glob("python*/site-packages"))
if not candidates:
    print("ERROR: Could not find site-packages in venv")
    sys.exit(1)
site_packages = candidates[0]

# ── Patch 1: inky_e673.py ────────────────────────────────────────────────────

inky_path = site_packages / "inky" / "inky_e673.py"
if not inky_path.exists():
    print(f"ERROR: {inky_path} not found — is inky installed?")
    sys.exit(1)

src = inky_path.read_text()

if "# PATCHED: cs_pin removed" in src:
    print("inky_e673.py: already patched, skipping.")
else:
    patches = [
        # Mark the file as patched
        (
            'def setup(self):',
            'def setup(self):  # PATCHED: cs_pin removed from gpiod — hardware SPI handles CE0'
        ),
        # Remove cs_pin from check_pins_available
        (
            '"Chip Select": self.cs_pin,\n                        "Data/Command": self.dc_pin,',
            '"Data/Command": self.dc_pin,'
        ),
        # Remove cs_pin line_offset resolution
        (
            "                    self.cs_pin = gpiochip.line_offset_from_id(self.cs_pin)\n                    self.dc_pin",
            "                    self.dc_pin"
        ),
        # Remove cs_pin from request_lines config
        (
            "                        self.cs_pin: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE, bias=Bias.DISABLED),\n                        self.dc_pin",
            "                        self.dc_pin"
        ),
        # Remove cs_pin assert in _spi_write
        (
            "        self._gpio.set_value(self.cs_pin, Value.INACTIVE)\n        self._gpio.set_value(self.dc_pin, Value.ACTIVE if dc else Value.INACTIVE)",
            "        self._gpio.set_value(self.dc_pin, Value.ACTIVE if dc else Value.INACTIVE)"
        ),
        # Remove cs_pin deassert in _spi_write
        (
            "        self._gpio.set_value(self.cs_pin, Value.ACTIVE)\n\n    def _send_command",
            "\n    def _send_command"
        ),
        # Remove cs_pin assert in _send_command
        (
            "        self._gpio.set_value(self.cs_pin, Value.INACTIVE)\n        self._gpio.set_value(self.dc_pin, Value.INACTIVE)\n        time.sleep(0.3)",
            "        self._gpio.set_value(self.dc_pin, Value.INACTIVE)\n        time.sleep(0.3)"
        ),
        # Remove cs_pin deassert in _send_command
        (
            "        self._gpio.set_value(self.cs_pin, Value.ACTIVE)\n        self._gpio.set_value(self.dc_pin, Value.INACTIVE)",
            "        self._gpio.set_value(self.dc_pin, Value.INACTIVE)"
        ),
    ]

    failed = [old[:60] for old, _ in patches if old not in src]
    if failed:
        print("ERROR: inky_e673.py — these patterns were not found (wrong inky version?):")
        for f in failed:
            print("  >>>", f)
        sys.exit(1)

    for old, new in patches:
        src = src.replace(old, new, 1)
    inky_path.write_text(src)
    print("inky_e673.py: patched OK")

# ── Patch 2: gpiodevice/__init__.py ──────────────────────────────────────────

gpio_path = site_packages / "gpiodevice" / "__init__.py"
if not gpio_path.exists():
    print(f"WARNING: {gpio_path} not found — skipping gpiodevice patch")
else:
    src = gpio_path.read_text()
    if "startswith(\"spi\")" in src:
        print("gpiodevice/__init__.py: already patched, skipping.")
    else:
        old = (
            "        if line_info.used:\n"
            "            used += 1\n"
            "            yield errors.GPIOError"
        )
        new = (
            "        if line_info.used:\n"
            "            # Skip pins claimed by the SPI kernel driver - inky manages CS via spidev.\n"
            "            if line_info.consumer.startswith(\"spi\"):\n"
            "                continue\n"
            "            used += 1\n"
            "            yield errors.GPIOError"
        )
        if old not in src:
            print("WARNING: gpiodevice pattern not found — skipping (wrong version?)")
        else:
            gpio_path.write_text(src.replace(old, new, 1))
            print("gpiodevice/__init__.py: patched OK")

print("\nDone. No reboot needed — patches take effect immediately.")
