"""Central config for gameplay tuning and rendering constants."""

# Canvas/window size.
WIDTH = 960
HEIGHT = 540
GROUND_Y = 488

# Player hitbox/body base dimensions.
PLAYER_X = 180
PLAYER_W = 78
PLAYER_H = 64

# Vertical physics.
GRAVITY = 2300.0
JUMP_VELOCITY = -1020.0

# Base world scrolling + clamp limits.
BASE_SCROLL_SPEED = 390.0
MIN_SCROLL_SPEED = 220.0
MAX_SCROLL_SPEED = 620.0

# Speed interpolation rates.
SLOW_ACCEL = 780.0
FAST_ACCEL = 860.0
RETURN_ACCEL = 460.0

# Procedural obstacle spacing.
OBSTACLE_MIN_GAP = 760
OBSTACLE_MAX_GAP = 1300

# Trick animation rates (degrees/second).
KICKFLIP_RATE = 360.0
TURN180_RATE = 480.0
BACKFLIP_RATE = 900.0

# Frame pacing target for Tk `after`.
FRAME_DELAY_MS = 8
