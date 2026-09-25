"""Widget definitions for SpinBox — compatible with Textual 8.x."""

from __future__ import annotations

from collections import deque
from rich.text import Text as RichText

from textual import events
from textual.app import ComposeResult, RenderResult
from textual.containers import Horizontal, Vertical
from textual.events import MouseScrollDown, MouseScrollUp
from textual.pad import HorizontalPad
from textual.widget import Widget
from textual.widgets import Button, Input, Static


class CellButton(Button, can_focus=False):
    """A unit-width Button that issues scroll events instead of clicks.
    Part of a SpinBox — no focus of its own."""

    def on_mouse_up(self, event: events.MouseUp) -> None:
        event.stop()
        if self.id == "sb_up":
            self.post_message(MouseScrollUp(self, 0, 0, 0, 0, 1, 0, 0, 0))
        elif self.id == "sb_dn":
            self.post_message(MouseScrollDown(self, 0, 0, 0, 0, 1, 0, 0, 0))

    def on_mouse_down(self, event: events.MouseDown) -> None:
        event.stop()

    def render(self) -> RenderResult:
        label = self.label
        if not isinstance(label, RichText):
            label = RichText(str(label))
        label.stylize_before(self.rich_style)
        return HorizontalPad(
            label,
            0,
            0,
            self.rich_style,
            self._get_justify_method() or "center",
        )


class SpinBox(Widget):
    """A spinbox widget with increment/decrement buttons and keyboard support."""

    DEFAULT_CSS = """
    SpinBox {
        height: 1;
        min-height: 1;
        #sb_box {
            height: 1;
            layout: horizontal;
        }
        #sb_control {
            background: $background-lighten-1;
            height: 1;
            width: 1;
            layout: vertical;
        }
        CellButton {
            color: $primary;
            background: $background-lighten-1;
            min-width: 1;
            width: 1;
            height: 1;
            border-top: none;
            border-bottom: none;
        }
        #sb_input {
            width: 100%;
            height: 1;
        }
        #sb_overflow {
            height: 1;
            width: 1;
            background: $background-lighten-1;
            color: $text-muted;
            text-align: center;
        }
    }
    """

    def __init__(
        self,
        iter_val: range | None = None,
        init_val: object = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.tooltip = "Scroll, Drag or Key Up/Down."
        if iter_val is not None:
            self.iter_ring: deque | None = deque(iter_val)
            if init_val is not None and self.iter_ring:
                try:
                    self.iter_ring.rotate(-1 * self.iter_ring.index(init_val))
                except ValueError:
                    pass
            self.value = str(self.iter_ring[0]) if self.iter_ring else "0"
        else:
            self.iter_ring = None
            self.value = str(init_val) if init_val is not None else "0"

    draging: bool = False

    def on_key(self, event: events.Key) -> None:
        if event.key == "up":
            event.stop()
            self._delta_v(1)
        elif event.key == "down":
            event.stop()
            self._delta_v(-1)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self.draging:
            if event.delta_y < 0:
                self._delta_v(1)
            elif event.delta_y > 0:
                self._delta_v(-1)

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self.draging = False
        self.release_mouse()

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self.draging = True
        self.capture_mouse()

    def on_mouse_scroll_up(self, event: MouseScrollUp) -> None:
        event.stop()
        self._delta_v(1)

    def on_mouse_scroll_down(self, event: MouseScrollDown) -> None:
        event.stop()
        self._delta_v(-1)

    def _delta_v(self, dv: int) -> None:
        sb_input = self.query_one("#sb_input", Input)
        if self.iter_ring is not None:
            self.iter_ring.rotate(-dv)
            self.value = str(self.iter_ring[0])
        else:
            self.value = str(int(sb_input.value or "0") + dv)
        sb_input.value = self.value
        sb_input.action_home()
        overflow = self.query_one("#sb_overflow", Static)
        if len(self.value) > (getattr(sb_input.size, "width", 10) or 10):
            overflow.update("…")
        else:
            overflow.update("¦")
        self.refresh(layout=True)

    def compose(self) -> ComposeResult:
        with Horizontal(id="sb_box"):
            yield Input(self.value, id="sb_input")
            with Vertical(id="sb_control"):
                yield CellButton("▲", id="sb_up")
                yield Static("¦", id="sb_overflow")
                yield CellButton("▼", id="sb_dn")