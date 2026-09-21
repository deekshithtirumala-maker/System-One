# 🎮 AI Alien Shooter — Jev System 1

A real-time alien shooter game where an AI agent continuously controls the player using **Jev System 1**.

Instead of hard-coding the player's movement and shooting strategy, the AI observes the current game state and makes deterministic decisions about **where to move and when to shoot**.

## 🚀 How It Works

The AI follows a continuous targeting loop:

```text
Find nearest alien
       ↓
Move toward the alien
       ↓
Align with the alien
       ↓
Shoot
       ↓
Kill the alien
       ↓
Find next nearest alien
       ↓
Repeat
```

The goal is simple:

> **Continuously target and kill aliens one by one.**

## 🧠 AI Decisions

The AI makes two decisions:

### Movement

The AI chooses exactly one:

```text
left
right
stay
```

It considers:

* Player position
* Distance from screen borders
* Position of every alien
* Nearest alien
* Horizontal distance to the target
* Vertical distance to the target
* Whether the player is aligned with the target
* Whether moving left or right helps reach the target

### Shooting

The AI chooses exactly one:

```text
yes
no
```

It considers:

* Current target
* Player/alien alignment
* Horizontal distance
* Vertical distance
* Whether firing can help kill the target
* Other available targets

There is no free-form response. The model is constrained to deterministic choices.

## 🛠️ Technologies

* Python
* Tkinter
* Jev System 1
* TypeSafe SDK
* AsyncIO
* Multithreading

## 📂 Project Structure

```text
.
├── typesafe_alien_shooter.py
└── README.md
```

## ▶️ Run the Game

Install the required SDK:

```bash
pip install typesafe-sdk
```

Then run:

```bash
python typesafe_alien_shooter.py
```

Make sure your Jev/TypeSafe environment is configured correctly before starti
