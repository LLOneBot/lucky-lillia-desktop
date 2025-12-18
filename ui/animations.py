"""动画效果模块"""

import flet as ft
from typing import Optional


def create_fade_in_animation(control: ft.Control, duration: int = 300) -> ft.Control:
    control.animate_opacity = duration
    control.opacity = 0
    return control


def create_scale_animation(control: ft.Control, duration: int = 200) -> ft.Control:
    control.animate_scale = duration
    control.scale = 0.95
    return control


def create_slide_animation(control: ft.Control, duration: int = 300) -> ft.Control:
    control.animate_offset = ft.Animation(duration, ft.AnimationCurve.EASE_OUT)
    control.offset = ft.transform.Offset(-0.1, 0)
    return control


def create_rotation_animation(control: ft.Control, duration: int = 1000) -> ft.Control:
    control.animate_rotation = ft.Animation(duration, ft.AnimationCurve.LINEAR)
    return control


def apply_hover_effect(control: ft.Control) -> ft.Control:
    if isinstance(control, ft.Container):
        control.animate = ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
        control.on_hover = lambda e: _on_hover(e, control)
    return control


def _on_hover(e, control: ft.Container):
    if e.data == "true":
        # 鼠标进入
        control.elevation = 8 if hasattr(control, 'elevation') else None
        control.scale = 1.02
    else:
        # 鼠标离开
        control.elevation = 3 if hasattr(control, 'elevation') else None
        control.scale = 1.0
    control.update()


def create_loading_spinner(size: int = 40, color: Optional[str] = None) -> ft.ProgressRing:
    return ft.ProgressRing(
        width=size,
        height=size,
        stroke_width=4,
        color=color or ft.Colors.PRIMARY,
    )


def create_pulse_animation(control: ft.Control, duration: int = 1000) -> ft.Control:
    control.animate_opacity = ft.Animation(duration, ft.AnimationCurve.EASE_IN_OUT)
    return control


class AnimatedCard(ft.Card):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.animate = ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
        self.animate_scale = 200
        self.scale = 1.0
        
    def on_hover_enter(self):
        self.elevation = 6
        self.scale = 1.02
        self.update()
        
    def on_hover_leave(self):
        self.elevation = 3
        self.scale = 1.0
        self.update()
