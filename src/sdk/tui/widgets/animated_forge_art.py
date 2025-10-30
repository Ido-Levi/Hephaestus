"""Animated ASCII art for peaceful medieval village."""

from textual.widgets import Static
from rich.text import Text
from rich.align import Align

from .animation_frames import (
    GRASS_FRAMES,
    TREE_LEAVES_FRAMES,
    WIND_FRAMES,
    VILLAGE_SCENE,
)
from .animation_utils import AnimationSequence


class AnimatedForgeArt(Static):
    """Widget displaying an animated medieval village with flowing grass and wind."""

    def __init__(self, status_text: str = "", enable_animations: bool = True, **kwargs):
        """
        Initialize the animated village art.

        Args:
            status_text: Optional status text to display below the art
            enable_animations: Whether animations are enabled
        """
        super().__init__(**kwargs)
        self.status_text = status_text
        self.enable_animations = enable_animations

        # Animation sequences
        self.grass_anim = AnimationSequence(GRASS_FRAMES, loop=True)
        self.tree_leaves_anim = AnimationSequence(TREE_LEAVES_FRAMES, loop=True)
        self.wind_anim = AnimationSequence(WIND_FRAMES, loop=True)

    def on_mount(self) -> None:
        """Set up animation timers when widget is mounted."""
        if self.enable_animations:
            # Different speeds for natural movement
            self.set_interval(0.5, self.animate_grass)       # Slow grass sway
            self.set_interval(0.8, self.animate_tree_leaves) # Gentle leaf rustle
            self.set_interval(1.5, self.animate_wind)        # Slow wind drift

    def animate_grass(self) -> None:
        """Advance grass animation and refresh display."""
        self.grass_anim.advance()
        self.refresh()

    def animate_tree_leaves(self) -> None:
        """Advance tree leaves animation and refresh display."""
        self.tree_leaves_anim.advance()
        self.refresh()

    def animate_wind(self) -> None:
        """Advance wind particle animation and refresh display."""
        self.wind_anim.advance()
        self.refresh()

    def compose_scene(self) -> str:
        """
        Compose the full animated scene by combining all elements.

        Returns:
            Complete ASCII art scene as a string
        """
        # Get current frames
        grass_frame = self.grass_anim.get_current_frame()
        tree_leaves_frame = self.tree_leaves_anim.get_current_frame()
        wind_frame = self.wind_anim.get_current_frame()

        # Build the complete scene
        scene = VILLAGE_SCENE

        # Replace placeholders with animated elements
        scene = scene.replace("{TREE_LEAVES}", tree_leaves_frame.art)
        scene = scene.replace("{GRASS1}", grass_frame.art)
        scene = scene.replace("{GRASS2}", grass_frame.art)
        scene = scene.replace("{WIND1}", wind_frame.art)
        scene = scene.replace("{WIND2}", wind_frame.art)
        scene = scene.replace("{WIND3}", wind_frame.art)

        return scene

    def render(self):
        """Render the animated village art with Rich styling."""
        if self.enable_animations:
            scene_text = self.compose_scene()
        else:
            # Static version without animations
            scene_text = VILLAGE_SCENE.replace("{TREE_LEAVES}", "")
            scene_text = scene_text.replace("{GRASS1}", "")
            scene_text = scene_text.replace("{GRASS2}", "")
            scene_text = scene_text.replace("{WIND1}", "")
            scene_text = scene_text.replace("{WIND2}", "")
            scene_text = scene_text.replace("{WIND3}", "")

        # Create Rich Text with styling
        art = Text(scene_text, style="bold white")

        # Add status text if provided
        if self.status_text:
            art.append("\n\n")
            art.append(self.status_text, style="bold cyan")

        # Center everything
        art.justify = "center"
        return Align.center(art, vertical="middle")

    def update_status(self, status: str):
        """
        Update the status text below the village.

        Args:
            status: New status text to display
        """
        self.status_text = status
        self.refresh()

    def toggle_animations(self):
        """Toggle animations on/off."""
        self.enable_animations = not self.enable_animations
        if self.enable_animations:
            # Resume all animations
            self.grass_anim.resume()
            self.tree_leaves_anim.resume()
            self.wind_anim.resume()
        else:
            # Pause all animations
            self.grass_anim.pause()
            self.tree_leaves_anim.pause()
            self.wind_anim.pause()
        self.refresh()

    def reset_animations(self):
        """Reset all animations to their starting state."""
        self.grass_anim.reset()
        self.tree_leaves_anim.reset()
        self.wind_anim.reset()
        self.refresh()
