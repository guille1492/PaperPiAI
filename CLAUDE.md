# PaperPiAI — Claude Code project memory

## About this project
AI art picture frame using a Raspberry Pi Zero 2 W and a 7.3" Inky Impression e-ink display.
Generates Stable Diffusion images locally and displays them. Built as a gift.

## Key hardware facts
- Display: Inky Impression 7.3" 2025 Edition (E673/Spectra 6), **800×480 pixels**
- Pi: Raspberry Pi Zero 2 W, 512MB RAM, running Raspberry Pi OS Bullseye 32-bit

## Project structure
- `src/generate_picture.py` — generates images via OnnxStream/Stable Diffusion
- `src/display_picture.py` — sends images to the e-ink display
- `prompts/` — JSON files with prompt fragments (list-of-lists structure, space-joined)
- `scripts/` — install and cron scripts

## Mac development environment
- Project path: `~/Documents/Proyectos/PaperPiAI`
- Fork: `github.com/guille1492/PaperPiAI`
- Remote: `git@github.com:guille1492/PaperPiAI.git`
- Python venv: `.venv/` inside the project folder
- Always activate with `source .venv/bin/activate` before running Python commands
- Mac uses MPS/Metal for image generation (for previewing); Pi uses CPU/ONNX

## Pi environment
- SSH: `ssh admin@raspberrypi.local`
- Always use `venv/bin/python`, never bare `python`, on the Pi
- Known bug fix: `installed_dir` in `generate_picture.py` must be set to `/home/admin/PaperPiAI`

## Prompt file format
Prompts use a list-of-lists JSON structure. Each inner list's items are space-joined into
a phrase, then phrases are combined. Do NOT use dicts or comma-joining. Match the structure
of the existing `prompts/flowers.json` exactly when creating new prompt files.

## Generate and display commands (Pi)
- Generate: `venv/bin/python src/generate_picture.py --width=800 --height=480 images`
- Display: `venv/bin/python src/display_picture.py -r images/output.png`

## My background
I'm a beginner coder. I know some Python but am new to best practices, Git, and Raspberry Pi.
- Explain the *why* behind commands, not just the what
- Keep explanations clear but don't oversimplify
- Prefer doing things through Claude Code rather than manual terminal steps where possible
