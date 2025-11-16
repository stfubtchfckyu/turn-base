# app.py
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# ---------- CONFIG ----------
GRID_W = 10
GRID_H = 10
TILE = 60  # pixel ukuran tile
IMG_W = GRID_W * TILE
IMG_H = GRID_H * TILE

# Colors (RGB tuples)
BG_COLOR = (50, 50, 50)
GRID_LINE = (120, 120, 120)
PLAYER_COLOR = (0, 180, 0)
ENEMY_COLOR = (180, 20, 20)
TEXT_COLOR = (255, 255, 255)

# ---------- HELPERS / GAME LOGIC ----------
def init_game():
    """Inisialisasi game state sederhana."""
    state = {
        "player": {"x": 0, "y": 0, "hp": 10},
        "enemy": {"x": GRID_W - 1, "y": GRID_H - 1, "hp": 10},
        "current_turn": "PLAYER",  # or "ENEMY"
        "log": ["Game started. Player turn."]
    }
    return state

def in_bounds(x, y):
    return 0 <= x < GRID_W and 0 <= y < GRID_H

def move_unit(unit, dx, dy):
    nx = unit["x"] + dx
    ny = unit["y"] + dy
    if in_bounds(nx, ny):
        unit["x"], unit["y"] = nx, ny
        return True
    return False

def positions_equal(a, b):
    return a["x"] == b["x"] and a["y"] == b["y"]

def attack(attacker, defender, state):
    dmg = 3
    defender["hp"] -= dmg
    state["log"].append(f"{attacker} menyerang {defender['name']} -{dmg} HP")
    if defender["hp"] <= 0:
        state["log"].append(f"{defender['name']} tewas!")

def enemy_ai_step(state):
    """AI sederhana: bergerak mendekati player. Jika bertemu, menyerang."""
    player = state["player"]
    enemy = state["enemy"]
    # If adjacent -> attack
    dx = player["x"] - enemy["x"]
    dy = player["y"] - enemy["y"]
    step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
    step_y = 0 if dy == 0 else (1 if dy > 0 else -1)

    # Prefer move in x then y
    moved = False
    if abs(dx) > 0:
        moved = move_unit(enemy, step_x, 0)
    if (not moved) and abs(dy) > 0:
        moved = move_unit(enemy, 0, step_y)

    # Attack if same tile
    if positions_equal(player, enemy):
        player["hp"] -= 2
        state["log"].append("Enemy menyerang Player -2 HP")

def end_turn(state):
    if state["current_turn"] == "PLAYER":
        state["current_turn"] = "ENEMY"
        state["log"].append("Giliran musuh.")
        # jalankan AI
        enemy_ai_step(state)
        # switch back if game not finished
        if state["player"]["hp"] > 0 and state["enemy"]["hp"] > 0:
            state["current_turn"] = "PLAYER"
            state["log"].append("Giliran pemain.")
    else:
        state["current_turn"] = "PLAYER"

# ---------- RENDER ----------
def render_image(state):
    """Return PIL.Image of the grid + units."""
    img = Image.new("RGB", (IMG_W, IMG_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # grid lines
    for x in range(GRID_W + 1):
        draw.line([(x * TILE, 0), (x * TILE, IMG_H)], fill=GRID_LINE)
    for y in range(GRID_H + 1):
        draw.line([(0, y * TILE), (IMG_W, y * TILE)], fill=GRID_LINE)

    # draw units as rectangles with a little padding
    pad = 6
    pl = state["player"]
    en = state["enemy"]

    # player
    px0 = pl["x"] * TILE + pad
    py0 = pl["y"] * TILE + pad
    px1 = (pl["x"] + 1) * TILE - pad
    py1 = (pl["y"] + 1) * TILE - pad
    draw.rectangle([px0, py0, px1, py1], fill=PLAYER_COLOR)

    # enemy
    ex0 = en["x"] * TILE + pad
    ey0 = en["y"] * TILE + pad
    ex1 = (en["x"] + 1) * TILE - pad
    ey1 = (en["y"] + 1) * TILE - pad
    draw.rectangle([ex0, ey0, ex1, ey1], fill=ENEMY_COLOR)

    # small HP text
    try:
        font = ImageFont.load_default()
    except:
        font = None

    draw.text((5, 5), f"Player HP: {pl['hp']}", fill=TEXT_COLOR, font=font)
    draw.text((5, 20), f"Enemy HP: {en['hp']}", fill=TEXT_COLOR, font=font)
    draw.text((5, 35), f"Turn: {state['current_turn']}", fill=TEXT_COLOR, font=font)

    return img

# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="Turn-Based RTS (Streamlit)", layout="wide")
st.title("Turn-Based RTS — Streamlit demo")

# Init session state
if "state" not in st.session_state:
    s = init_game()
    # add name fields for log messages
    s["player"]["name"] = "Player"
    s["enemy"]["name"] = "Enemy"
    st.session_state.state = s

state = st.session_state.state

# Left column: game view
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Board")
    img = render_image(state)
    st.image(img, use_column_width=True)

    # Movement buttons (only enabled on player's turn and if player alive)
    st.markdown("**Controls**")
    col_up, col_mid, col_down = st.columns([1, 2, 1])
    with col_up:
        if st.button("Up") and state["current_turn"] == "PLAYER" and state["player"]["hp"] > 0:
            moved = move_unit(state["player"], 0, -1)
            state["log"].append(f"Player moved up.") if moved else state["log"].append("Can't move up.")
            end_turn(state)
    with col_mid:
        left_col, spacer, right_col = st.columns([1, 1, 1])
        with left_col:
            if st.button("Left") and state["current_turn"] == "PLAYER" and state["player"]["hp"] > 0:
                moved = move_unit(state["player"], -1, 0)
                state["log"].append(f"Player moved left.") if moved else state["log"].append("Can't move left.")
                end_turn(state)
        with right_col:
            if st.button("Right") and state["current_turn"] == "PLAYER" and state["player"]["hp"] > 0:
                moved = move_unit(state["player"], 1, 0)
                state["log"].append(f"Player moved right.") if moved else state["log"].append("Can't move right.")
                end_turn(state)
    with col_down:
        if st.button("Down") and state["current_turn"] == "PLAYER" and state["player"]["hp"] > 0:
            moved = move_unit(state["player"], 0, 1)
            state["log"].append(f"Player moved down.") if moved else state["log"].append("Can't move down.")
            end_turn(state)

    # Attack button (attack if on same tile)
    if st.button("Attack") and state["current_turn"] == "PLAYER" and state["player"]["hp"] > 0:
        if positions_equal(state["player"], state["enemy"]):
            state["enemy"]["hp"] -= 4
            state["log"].append("Player menyerang Enemy -4 HP")
            # check kill
            if state["enemy"]["hp"] <= 0:
                state["log"].append("Enemy tewas! Player menang.")
        else:
            state["log"].append("Tidak ada musuh di tile ini.")
        end_turn(state)

    # Reset button
    if st.button("Reset Game"):
        st.session_state.state = init_game()
        st.experimental_rerun()

with col2:
    st.subheader("Status & Log")
    st.markdown(f"**Turn:** {state['current_turn']}")
    st.markdown(f"**Player HP:** {state['player']['hp']}")
    st.markdown(f"**Enemy HP:** {state['enemy']['hp']}")

    st.markdown("---")
    st.markdown("**Event Log (latest 10):**")
    for line in state["log"][-10:][::-1]:
        st.write("- " + line)

# Check for endgame
if state["player"]["hp"] <= 0:
    st.error("Kamu kalah. Player HP = 0")
if state["enemy"]["hp"] <= 0:
    st.success("Kamu menang! Enemy HP = 0")
