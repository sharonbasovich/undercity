# 404: Drink Not Found
## About
Created at HackClub's undercity, Drink Not Found is a system where you play Tic-Tac-Toe using a drawing machine against AI-buddy Auto ([credit: Paolo](https://www.youtube.com/watch?v=M4BQyCwvZE4)). If you win, you can pick a drink from the vending machine, and randomly get any drink except that one. Also, you contribute to a unique mosaic.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Frontend (blot-board-blitz)](#frontend-blot-board-blitz)
- [Backend (blot-backend)](#backend-blot-backend)
- [Hardware (Blot Plotter)](#hardware-blot-plotter)
- [Development & Testing](#development--testing)
- [Project Structure](#project-structure)
- [License](#license)

---

## Features

- **Tic-Tac-Toe vs. Auto:** Play against a playful AI with pixel-art visuals, chat, speech-to-text, and smooth animations.
- **Collaborative Mosaic:** Help fill a 108x50 square mosaic by filling one of the 180 sections of 30 pixels, building a large mosaic together.
- **Physical Drawing:** All moves and mosaic pieces are drawn in real-time on the Blot plotter.
- **Vending Machine:** Choose your drink on a touchscreen, enter the secret passcode, and smash the confirmation button to get a drink... any drink but the one you chose.
- **Robust UI/UX:** Retro pixel-art theme, animated chat, speech-to-text, matrix rain background, and responsive controls.
- **Testing Mode:** A dummy backend allows full website experience without the hardware.

---

## Blot Architecture

- **Frontend:** React + TypeScript + Vite + Tailwind CSS + shadcn/ui (in `blot-board-blitz/`)
- **Backend:** Python + Flask (in `blot-backend/`), with hardware control via serial and COBS.
- **Hardware:** HackClub's Blot Kit controlled via serial commands.

---

## Frontend (`blot-board-blitz`)
### [The frontend repo](https://github.com/sharonbasovich/blot-board-blitz)
### Setup

```bash
cd blot-board-blitz
npm install
npm run dev
```

- Runs on [localhost:8080](http://localhost:8080)
- Main pages:
  - `/` — Tic-Tac-Toe and mosaic grid
  - `/draw` — Draw the large mosaic boundary rectangle

### Features

- **TicTacToe:** Play against Auto, with animated chat and pixel-art board.
- **PixelGrid:** Submit your own 6x5 pixel pattern to fill the next mosaic subrectangle.
- **Mosaic Preview:** See the full 108x50 mosaic as it fills, live-updating and rotated to match hardware orientation.
- **Toasts & Feedback:** All actions provide clear, non-blocking feedback.

---

## Backend (`blot-backend`)

### Setup

#### When Using The Blot

```bash
cd blot-backend
python ttt_backend_corner5.py
```

- Requires the Blot plotter connected via serial (update `SERIAL_PORT` as needed).
- Exposes Flask API on [localhost:5000](http://localhost:5000).

#### For Testing (Without The Blot)

```bash
cd blot-backend
python ttt_backend_corner5_dummy.py
```

- Simulates all endpoints and drawing logic with print statements and delays.
- Safe for frontend development without hardware.

### Key Endpoints

- `/start` — Start a new Tic-Tac-Toe game
- `/move` — Make a player move
- `/ai-move` — Let Auto make a move
- `/state` — Get current game state
- `/draw-pixel-art-square` — Draw a 6x5 pixel pattern at a mosaic subrectangle
- `/draw-large-area-rectangle` — Draw the full mosaic boundary
- ...and more for advanced control

---

## Hardware (Blot Plotter)

- [Kit created by HackClub](https://blot.hackclub.com/)

---

## Development & Testing

- **Frontend:** Hot-reload with `npm run dev` in `blot-board-blitz/`.
- **Backend:** Run either the real (`ttt_backend_corner5.py`) or dummy (`ttt_backend_corner5_dummy.py`) backend. Note, hot-reloading disabled as it caused serial connection issues.
- **Testing:** Use the dummy backend for full UI/UX testing without hardware risk.
- **Hardware:** Only use the real backend when the Blot plotter is connected and ready.

---

## Project Structure

```
blot-board-blitz/      # Frontend React app
blot-backend/          # Backend Flask app (real and dummy)
```
