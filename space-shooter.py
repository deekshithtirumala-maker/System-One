import tkinter as tk
import asyncio
import threading
import random
import math

from typesafe_sdk import AsyncTypeSafeClient, Choice


# ============================================================
# SETTINGS
# ============================================================

WIDTH = 600
HEIGHT = 700

GAME_FPS = 30

# TypeSafe call frequency:
# 0.2 seconds = approximately 5 requests/second
AI_INTERVAL = 0.2

PLAYER_SPEED = 8
BULLET_SPEED = 12
ALIEN_SPEED = 2

game_running = True

# AI decisions
ai_move = "stay"
ai_shoot = "no"

state_lock = threading.Lock()


# ============================================================
# GAME STATE
# ============================================================

player_x = WIDTH // 2
player_y = HEIGHT - 50

aliens = []
bullets = []

score = 0
lives = 3


# ============================================================
# TKINTER
# ============================================================

root = tk.Tk()
root.title("TypeSafe Alien Shooter")
root.resizable(False, False)

canvas = tk.Canvas(
    root,
    width=WIDTH,
    height=HEIGHT,
    bg="black"
)
canvas.pack()


# ============================================================
# PLAYER
# ============================================================

player = canvas.create_rectangle(
    player_x - 20,
    player_y - 10,
    player_x + 20,
    player_y + 10,
    fill="blue"
)


# ============================================================
# CREATE ALIEN
# ============================================================

def create_alien():
    x = random.randint(30, WIDTH - 30)
    y = random.randint(50, 150)

    alien = canvas.create_oval(
        x - 20,
        y - 15,
        x + 20,
        y + 15,
        fill="red"
    )

    aliens.append(alien)


for _ in range(5):
    create_alien()


# ============================================================
# POSITION
# ============================================================

def get_position(obj):
    box = canvas.coords(obj)

    if not box:
        return 0, 0

    x = (box[0] + box[2]) / 2
    y = (box[1] + box[3]) / 2

    return x, y


# ============================================================
# PLAYER DESCRIPTION
# ============================================================

def describe_player(px, py):
    left = round(px)
    right = round(WIDTH - px)
    top = round(py)
    bottom = round(HEIGHT - py)

    if px < WIDTH / 3:
        side = "left side of the screen"
    elif px > WIDTH * 2 / 3:
        side = "right side of the screen"
    else:
        side = "center of the screen"

    if py < HEIGHT / 3:
        zone = "upper part of the screen"
    elif py > HEIGHT * 2 / 3:
        zone = "lower part of the screen"
    else:
        zone = "middle part of the screen"

    return {
        "x": round(px),
        "y": round(py),
        "horizontal_position": (
            f"{left} pixels from the left border and "
            f"{right} pixels from the right border"
        ),
        "vertical_position": (
            f"{top} pixels from the top border and "
            f"{bottom} pixels from the bottom border"
        ),
        "side": side,
        "vertical_zone": zone,
        "space_available": {
            "left": left,
            "right": right
        }
    }


# ============================================================
# ALIEN DESCRIPTION
# ============================================================

def describe_alien(x, y, px, py):
    dx = x - px
    dy = y - py

    distance = math.sqrt(dx * dx + dy * dy)

    if abs(dx) <= 30:
        horizontal = "almost directly aligned horizontally with the player"
    elif dx < 0:
        horizontal = f"{abs(round(dx))} pixels to the left of the player"
    else:
        horizontal = f"{round(dx)} pixels to the right of the player"

    if abs(dy) <= 30:
        vertical = "almost at the same vertical level as the player"
    elif dy < 0:
        vertical = f"{abs(round(dy))} pixels above the player"
    else:
        vertical = f"{round(dy)} pixels below the player"

    if dx < -30 and dy < -30:
        direction = "upper-left"
    elif dx > 30 and dy < -30:
        direction = "upper-right"
    elif dx < -30 and dy > 30:
        direction = "lower-left"
    elif dx > 30 and dy > 30:
        direction = "lower-right"
    elif abs(dx) <= 30 and dy < 0:
        direction = "directly above"
    elif abs(dx) <= 30 and dy > 0:
        direction = "directly below"
    elif dx < 0:
        direction = "left"
    elif dx > 0:
        direction = "right"
    else:
        direction = "same position"

    if distance < 100:
        threat = "very close and potentially dangerous"
    elif distance < 200:
        threat = "close to the player"
    elif distance < 350:
        threat = "moderately far from the player"
    else:
        threat = "far from the player"

    return {
        "position": {
            "x": round(x),
            "y": round(y)
        },
        "horizontal_relation": horizontal,
        "vertical_relation": vertical,
        "direction_from_player": direction,
        "distance_from_player": round(distance),
        "threat_description": threat
    }


# ============================================================
# LIVE GAME STATE
# ============================================================

def get_game_state():
    px, py = get_position(player)

    player_state = describe_player(px, py)

    alien_state = []

    for alien in aliens:
        x, y = get_position(alien)

        alien_state.append(
            describe_alien(x, y, px, py)
        )

    alien_state.sort(
        key=lambda a: a["distance_from_player"]
    )

    closest_alien = (
        alien_state[0]
        if alien_state
        else None
    )

    bullet_state = []

    for bullet in bullets:
        x, y = get_position(bullet)

        bullet_state.append({
            "position": {
                "x": round(x),
                "y": round(y)
            },
            "horizontal_relation_to_player": (
                f"{round(x - px)} pixels horizontally relative to player"
            ),
            "vertical_relation_to_player": (
                f"{round(y - py)} pixels vertically relative to player"
            )
        })

    return {
        "game": {
            "screen_width": WIDTH,
            "screen_height": HEIGHT,
            "objective": (
                "Survive as long as possible, avoid aliens, "
                "and destroy aliens by shooting them."
            ),
            "score": score,
            "lives_remaining": lives
        },
        "player": player_state,
        "aliens": {
            "count": len(alien_state),
            "closest_alien": closest_alien,
            "all_aliens": alien_state
        },
        "bullets": {
            "count": len(bullet_state),
            "active_bullets": bullet_state
        }
    }


# ============================================================
# TYPESAFE QUESTIONS
# ============================================================

questions = {
    "move": Choice(
    instructions="""You control the player's horizontal movement in a real-time
alien-killing game.

Your CONTINUOUS PRIMARY OBJECTIVE is:

1. Identify the nearest alien.
2. Move toward that nearest alien.
3. Position the player underneath or horizontally aligned with it.
4. Help the player shoot and KILL that alien.
5. After that alien is killed, immediately target the next nearest alien.
6. Continue this process continuously until all aliens are killed.

At every decision, prioritize killing the nearest useful alien.

Analyze the COMPLETE CURRENT GAME STATE, including:
- player's position
- distance from left and right borders
- position of every alien
- nearest alien
- horizontal distance to the nearest alien
- vertical distance to the nearest alien
- whether the player is already aligned with the alien
- whether moving left or right will improve alignment
- positions of other aliens that may become the next target

Choose the horizontal movement that helps the player reach and kill
the current nearest alien.

Return exactly ONE:
- left
- right
- stay

Do not provide explanation or any additional text.
""",
    criteria={
        "left": "Move toward the current nearest alien.",
        "right": "Move toward the current nearest alien.",
        "stay": "Stay horizontally aligned with the current nearest alien."
    }
),

    "shoot": Choice(
    instructions="""You control the player's shooting in a real-time
alien-killing game.

Your objective is to KILL aliens continuously.

At every decision:
1. Identify the current nearest alien.
2. Check whether the player is aligned with that alien.
3. If firing now can help kill the target, choose yes.
4. Continue attacking the current target until it is killed.
5. Once it is killed, immediately target the next nearest alien.

Analyze the complete game state, including:
- player's position
- every alien's position
- nearest alien
- horizontal distance
- vertical distance
- alignment
- whether the target is approaching
- whether firing now helps kill the target

Return exactly ONE:
- yes
- no

Do not provide explanation, probability, percentage, reasoning,
or any additional text.
""",
    criteria={
        "yes": "Fire now to attack and kill the current target.",
        "no": "Do not fire yet because firing now would not effectively attack the target."
    }
)
}


# ============================================================
# TYPESAFE AI LOOP
# ============================================================

async def ai_loop():
    global ai_move
    global ai_shoot

    print("Starting TypeSafe AI...")

    async with AsyncTypeSafeClient(api_key="API_KEY") as client:
        while game_running:
            try:
                state = get_game_state()
                print("Current game state:", state)
                response = await client.system_one(
                    state=state,
                    questions=questions
                )

                move = response.choices["move"].choice
                shoot = response.choices["shoot"].choice

                with state_lock:
                    ai_move = move
                    ai_shoot = shoot

                print(
                    f"AI -> move={move}, shoot={shoot}"
                )

            except Exception as e:
                print("TypeSafe error:", e)

            await asyncio.sleep(AI_INTERVAL)


# ============================================================
# START AI THREAD
# ============================================================

def start_ai():
    asyncio.run(ai_loop())


ai_thread = threading.Thread(
    target=start_ai,
    daemon=True
)

ai_thread.start()


# ============================================================
# SHOOT
# ============================================================

def shoot():
    px, py = get_position(player)

    bullet = canvas.create_rectangle(
        px - 3,
        py - 15,
        px + 3,
        py,
        fill="yellow"
    )

    bullets.append(bullet)


# ============================================================
# MOVE PLAYER
# ============================================================

def move_player():
    global player_x

    with state_lock:
        move = ai_move

    if move == "left":
        player_x -= PLAYER_SPEED

    elif move == "right":
        player_x += PLAYER_SPEED

    if player_x < 20:
        player_x = 20

    if player_x > WIDTH - 20:
        player_x = WIDTH - 20

    px, py = get_position(player)

    dx = player_x - px

    canvas.move(
        player,
        dx,
        0
    )


# ============================================================
# BULLETS
# ============================================================

def update_bullets():
    for bullet in bullets[:]:
        canvas.move(
            bullet,
            0,
            -BULLET_SPEED
        )

        x, y = get_position(bullet)

        if y < 0:
            canvas.delete(bullet)
            bullets.remove(bullet)


# ============================================================
# ALIENS
# ============================================================

def update_aliens():
    global lives

    for alien in aliens[:]:
        canvas.move(
            alien,
            0,
            ALIEN_SPEED
        )

        x, y = get_position(alien)

        if y > HEIGHT - 30:
            canvas.delete(alien)
            aliens.remove(alien)

            lives -= 1

            create_alien()


# ============================================================
# COLLISION
# ============================================================

def collision(a, b):
    ax1, ay1, ax2, ay2 = canvas.coords(a)
    bx1, by1, bx2, by2 = canvas.coords(b)

    return not (
        ax2 < bx1 or
        ax1 > bx2 or
        ay2 < by1 or
        ay1 > by2
    )


# ============================================================
# BULLET / ALIEN COLLISION
# ============================================================

def check_collisions():
    global score

    for bullet in bullets[:]:
        for alien in aliens[:]:

            if collision(bullet, alien):

                canvas.delete(bullet)
                canvas.delete(alien)

                if bullet in bullets:
                    bullets.remove(bullet)

                if alien in aliens:
                    aliens.remove(alien)

                score += 10

                create_alien()

                break


# ============================================================
# UI
# ============================================================

def update_ui():
    canvas.delete("ui")

    canvas.create_text(
        70,
        20,
        text=f"Score: {score}",
        fill="white",
        font=("Arial", 14),
        tags="ui"
    )

    canvas.create_text(
        520,
        20,
        text=f"Lives: {lives}",
        fill="white",
        font=("Arial", 14),
        tags="ui"
    )

    with state_lock:
        move = ai_move
        shoot_decision = ai_shoot

    canvas.create_text(
        WIDTH // 2,
        20,
        text=f"AI: {move} | Shoot: {shoot_decision}",
        fill="white",
        font=("Arial", 11),
        tags="ui"
    )


# ============================================================
# GAME OVER
# ============================================================

def game_over():
    global game_running

    game_running = False

    canvas.create_text(
        WIDTH // 2,
        HEIGHT // 2,
        text="GAME OVER",
        fill="white",
        font=("Arial", 32)
    )


# ============================================================
# GAME LOOP
# ============================================================

def game_loop():

    if not game_running:
        return

    # Apply TypeSafe movement decision
    move_player()

    # Update game objects
    update_bullets()
    update_aliens()

    # Detect collisions
    check_collisions()

    # Apply TypeSafe shooting decision
    with state_lock:
        shoot_decision = ai_shoot

    if shoot_decision == "yes":
        shoot()

    # Update display
    update_ui()

    # Check game over
    if lives <= 0:
        game_over()
        return

    # Continue at approximately 30 FPS
    root.after(
        int(1000 / GAME_FPS),
        game_loop
    )


# ============================================================
# START GAME
# ============================================================

game_loop()

root.mainloop()
