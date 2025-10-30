"""Animation utilities for managing frame sequences and timing."""

from typing import List
from .animation_frames import Frame


class AnimationSequence:
    """Manages a sequence of animation frames with timing control."""

    def __init__(self, frames: List[Frame], loop: bool = True):
        """
        Initialize an animation sequence.

        Args:
            frames: List of Frame objects to cycle through
            loop: Whether to loop the animation (True) or stop at last frame
        """
        self.frames = frames
        self.loop = loop
        self.current_index = 0
        self.is_playing = True

    def get_current_frame(self) -> Frame:
        """Get the current frame in the sequence."""
        if not self.frames:
            return Frame(art="", style="")
        return self.frames[self.current_index]

    def advance(self) -> Frame:
        """
        Advance to the next frame and return it.

        Returns:
            The next frame in the sequence
        """
        if not self.is_playing or not self.frames:
            return self.get_current_frame()

        self.current_index += 1

        # Handle looping or stopping at end
        if self.current_index >= len(self.frames):
            if self.loop:
                self.current_index = 0
            else:
                self.current_index = len(self.frames) - 1
                self.is_playing = False

        return self.get_current_frame()

    def reset(self):
        """Reset animation to first frame and resume playing."""
        self.current_index = 0
        self.is_playing = True

    def pause(self):
        """Pause the animation at current frame."""
        self.is_playing = False

    def resume(self):
        """Resume playing the animation."""
        self.is_playing = True

    def set_frame(self, index: int):
        """Jump to a specific frame index."""
        if 0 <= index < len(self.frames):
            self.current_index = index


class SyncedAnimationGroup:
    """Group of animations that can be synchronized together."""

    def __init__(self):
        """Initialize an empty animation group."""
        self.animations = {}

    def add(self, name: str, sequence: AnimationSequence):
        """Add an animation to the group."""
        self.animations[name] = sequence

    def advance_all(self):
        """Advance all animations in the group."""
        for animation in self.animations.values():
            animation.advance()

    def reset_all(self):
        """Reset all animations to first frame."""
        for animation in self.animations.values():
            animation.reset()

    def pause_all(self):
        """Pause all animations."""
        for animation in self.animations.values():
            animation.pause()

    def resume_all(self):
        """Resume all animations."""
        for animation in self.animations.values():
            animation.resume()

    def get(self, name: str) -> AnimationSequence:
        """Get an animation by name."""
        return self.animations.get(name)


def interpolate_position(start: tuple, end: tuple, progress: float) -> tuple:
    """
    Interpolate between two positions.

    Args:
        start: Starting (x, y) position
        end: Ending (x, y) position
        progress: Progress from 0.0 to 1.0

    Returns:
        Interpolated (x, y) position
    """
    x = int(start[0] + (end[0] - start[0]) * progress)
    y = int(start[1] + (end[1] - start[1]) * progress)
    return (x, y)


def overlay_text(base: str, overlay: str, position: tuple) -> str:
    """
    Overlay text onto a base string at specified position.

    Args:
        base: Base text (multi-line string)
        overlay: Text to overlay (multi-line string)
        position: (x, y) position to place overlay

    Returns:
        Combined text with overlay applied
    """
    base_lines = base.split('\n')
    overlay_lines = overlay.split('\n')

    x, y = position

    # Apply overlay line by line
    for i, overlay_line in enumerate(overlay_lines):
        line_index = y + i
        if 0 <= line_index < len(base_lines):
            base_line = base_lines[line_index]
            # Ensure base line is long enough
            if len(base_line) < x:
                base_line += ' ' * (x - len(base_line))

            # Replace characters at position
            left = base_line[:x]
            right = base_line[x + len(overlay_line):]
            base_lines[line_index] = left + overlay_line + right

    return '\n'.join(base_lines)
