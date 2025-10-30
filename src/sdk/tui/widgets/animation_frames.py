"""Animation frames for peaceful medieval village scene."""

from dataclasses import dataclass
from typing import List


@dataclass
class Frame:
    """Single animation frame with ASCII art and styling."""
    art: str
    style: str = "bold yellow"


# ============================================================================
# GRASS ANIMATION FRAMES (4 frames for swaying grass)
# ============================================================================

GRASS_FRAMES = [
    Frame(art="| | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |", style="bold green"),
    Frame(art="/ / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / / /", style="bold green"),
    Frame(art="| | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |", style="bold green"),
    Frame(art="\\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\", style="bold green"),
]


# ============================================================================
# TREE LEAVES ANIMATION (4 frames for rustling leaves)
# ============================================================================

TREE_LEAVES_FRAMES = [
    Frame(art="""        @@@@@@@
       @@@@@@@@@
      @@@@@@@@@@@
       @@@@@@@@@
        @@@@@@@""", style="bold green"),

    Frame(art="""       @@@@@@@
      @@@@@@@@@
     @@@@@@@@@@@
      @@@@@@@@@
       @@@@@@@""", style="bold green"),

    Frame(art="""        @@@@@@@
       @@@@@@@@@
      @@@@@@@@@@@
       @@@@@@@@@
        @@@@@@@""", style="bold green"),

    Frame(art="""         @@@@@@@
        @@@@@@@@@
       @@@@@@@@@@@
        @@@@@@@@@
         @@@@@@@""", style="bold green"),
]


# ============================================================================
# WIND/AIR PARTICLES (3 frames for floating particles)
# ============================================================================

WIND_FRAMES = [
    Frame(art="  .    .      .       .     .        .    .       .      .", style="dim cyan"),
    Frame(art="     .    .      .       .     .        .    .       .", style="dim cyan"),
    Frame(art=" .       .      .       .     .        .    .       .     .", style="dim cyan"),
]


# ============================================================================
# MEDIEVAL VILLAGE SCENE (Static background with placeholders)
# ============================================================================

VILLAGE_SCENE = """


{WIND1}


                         {TREE_LEAVES}
                             |||
                             |||
                            |||||
                           |||||||


{WIND2}


                    ___________________
                   /                   \\
                  /                     \\
                 /   __           __     \\
                /   |  |         |  |     \\
               /    |  |         |  |      \\
              /     |__|         |__|       \\
             /          _______             \\
            /          |       |             \\
           /           |       |              \\
          /____________|_______|_______________\\
          |            |       |               |
          |            |       |               |
          |            |       |               |
          |____________|_______|_______________|


{WIND3}


═══════════════════════════════════════════════════════════
{GRASS1}
{GRASS2}
"""
