"""
ui/theme.py
-----------
Layout constants, color palettes, and styling tokens for the Stardew Valley aesthetic UI.
"""

from simulation.environment import GRID_COLS, GRID_ROWS

# ==============================================================
# 1080p Layout Constants
# ==============================================================
CELL = 64
MAP_W = GRID_COLS * CELL          # 20 * 64 = 1280
MAP_H = GRID_ROWS * CELL          # 15 * 64 = 960

GRID_X = 24                       # Spacing from left of screen
GRID_Y = 16                       # Spacing from top of screen
GRID_RADIUS = 6                   # Rounded outer corners fitting timber frame

WINDOW_W = 1920
WINDOW_H = 1080

PANEL_X = GRID_X + MAP_W + 20     # 24 + 1280 + 20 = 1324
PANEL_W = WINDOW_W - PANEL_X - 24   # 1920 - 1324 - 24 = 572

DEFAULT_SPEED = 3.0

# ==============================================================
# Stardew Valley Aesthetic Palette & Styling Tokens
# ==============================================================

# Timber / Wood Frame
SV_WOOD_DARK = (54, 26, 12)          # Outer frame outline / deep timber
SV_WOOD_MAIN = (194, 118, 48)        # Warm golden timber base
SV_WOOD_HI = (238, 172, 88)          # Top/left golden oak highlight
SV_WOOD_SH = (122, 58, 20)           # Bottom/right rich chestnut shadow
SV_WOOD_RIVET = (255, 215, 115)      # Brass / gold corner rivets
SV_WOOD_HEADER = (80, 42, 18)        # Dark walnut banner / table header
SV_WOOD_INNER_BORDER = (74, 38, 16)  # Frame separator border

# Parchment Canvas
SV_PARCHMENT = (251, 238, 198)       # Creamy warm parchment fill
SV_PARCHMENT_LIGHT = (254, 246, 222) # Bright cream ledger row
SV_PARCHMENT_DARK = (235, 212, 164)  # Inner parchment shadow
SV_PARCHMENT_INSET = (228, 202, 152) # Recessed item slot fill
SV_INSET_SHADOW = (186, 154, 108)    # 3D shadow for recessed slots
SV_INSET_HI = (255, 246, 226)        # 3D highlight for recessed slots

# Ink & Typography
SV_TEXT_DARK = (64, 30, 12)          # Deep chocolate ink (main text)
SV_TEXT_MUTED = (128, 82, 45)        # Sepia / warm muted brown
SV_TEXT_TITLE = (145, 68, 14)        # Warm carved wood header title
SV_TEXT_LIGHT = (255, 248, 235)      # Cream text on wood/buttons
SV_TEXT_SHADOW = (50, 24, 10)        # Drop shadow for cream text
SV_TEXT_HI_SHADOW = (255, 245, 220)  # Highlight shadow for dark text on parchment

# Harvest & Vitals Accents
SV_ENERGY_MAIN = (92, 186, 44)       # Vibrant Stardew grass green
SV_ENERGY_HI = (165, 235, 95)        # Glossy top highlight
SV_ENERGY_SH = (48, 125, 20)         # Bottom shade

SV_NECTAR_MAIN = (245, 168, 28)      # Golden honey / starfruit amber
SV_NECTAR_HI = (255, 228, 110)       # Glossy top highlight
SV_NECTAR_SH = (185, 112, 14)        # Bottom shade

SV_GOLD_STAR = (255, 210, 50)        # Stardew Gold Star highlight
SV_GOLD_WINNER = (245, 195, 75)      # Winner row highlight in benchmark
SV_GOLD_BORDER = (195, 130, 25)

# Button Colors
SV_BTN_NORMAL_FILL = (208, 128, 48)
SV_BTN_NORMAL_HI = (244, 178, 92)
SV_BTN_NORMAL_SH = (132, 64, 20)

SV_BTN_HOVER_FILL = (235, 155, 62)
SV_BTN_HOVER_HI = (255, 208, 120)
SV_BTN_HOVER_SH = (156, 82, 26)

SV_BTN_ACTIVE_FILL = (68, 148, 54)   # Harvest green when running
SV_BTN_ACTIVE_HI = (112, 196, 92)
SV_BTN_ACTIVE_SH = (38, 94, 28)

SV_BTN_PAUSE_FILL = (214, 140, 42)   # Amber wood for pause
SV_BTN_PAUSE_HI = (248, 188, 88)
SV_BTN_PAUSE_SH = (138, 72, 18)

SV_BTN_DANGER_FILL = (185, 45, 38)   # Crimson red wood
SV_BTN_DANGER_HI = (228, 82, 75)
SV_BTN_DANGER_SH = (118, 25, 20)

SV_BTN_BENCH_FILL = (120, 60, 160)   # Royal starfruit purple / violet wood
SV_BTN_BENCH_HI = (160, 95, 210)
SV_BTN_BENCH_SH = (75, 35, 105)

# Hive & Meadow accents
SV_HIVE_FILL = (232, 148, 38)
SV_HIVE_ROOF = (156, 78, 22)
SV_PATH_LINE = (245, 185, 40)        # Golden pollen trail
SV_PATH_STEP = (255, 228, 110)

BG = (22, 34, 24)
OBSTACLE = (100, 116, 139)
OBSTACLE_BORDER = (71, 85, 105)
