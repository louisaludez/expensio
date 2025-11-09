from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, PushMatrix, PopMatrix, Translate
from kivy.graphics.instructions import InstructionGroup
import math

class CircularBudgetWidget(Widget):
    def __init__(self, **kwargs):
        self.progress = kwargs.pop('progress', 0.85)  # 85% progress
        super().__init__(**kwargs)
        self._instruction_group = None
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        # Schedule initial update after widget is fully initialized
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._update_canvas(), 0.1)
    
    def _update_canvas(self, *args):
        if self.width == 0 or self.height == 0:
            return
        
        # Remove old instructions
        if self._instruction_group:
            self.canvas.remove(self._instruction_group)
        
        # Create new instruction group
        self._instruction_group = InstructionGroup()
        
        # Use widget's own coordinate system (0,0 is bottom-left of widget)
        center_x = self.width / 2
        center_y = self.height / 2
        radius = min(self.width, self.height) / 2 - 10
        inner_radius = radius - 20  # Thickness of ring
        
        # Shadow
        self._instruction_group.add(PushMatrix())
        self._instruction_group.add(Translate(center_x, center_y))
        self._instruction_group.add(Color(0, 0, 0, 0.12))
        shadow_size = radius * 2 + 20
        self._instruction_group.add(Ellipse(size=(shadow_size, shadow_size), pos=(-radius - 10 + 3, -radius - 10 - 3)))
        self._instruction_group.add(PopMatrix())
        
        # Thick outer ring (light beige/cream)
        self._instruction_group.add(PushMatrix())
        self._instruction_group.add(Translate(center_x, center_y))
        self._instruction_group.add(Color(0.96, 0.94, 0.90, 1))  # Light beige/cream
        outer_size = radius * 2 + 20
        self._instruction_group.add(Ellipse(size=(outer_size, outer_size), pos=(-radius - 10, -radius - 10)))
        # Inner circle to create ring
        self._instruction_group.add(Color(0.98, 0.98, 0.97, 1))  # Light off-white
        inner_size = inner_radius * 2
        self._instruction_group.add(Ellipse(size=(inner_size, inner_size), pos=(-inner_radius, -inner_radius)))
        self._instruction_group.add(PopMatrix())
        
        # Background wavy graph area (light orange/peach)
        self._instruction_group.add(PushMatrix())
        self._instruction_group.add(Translate(center_x, center_y - 15))
        self._instruction_group.add(Color(1, 0.85, 0.7, 0.25))  # Light orange/peach
        graph_w = inner_radius * 1.7
        graph_h = inner_radius * 0.9
        self._instruction_group.add(Ellipse(size=(graph_w, graph_h), pos=(-inner_radius * 0.85, -inner_radius * 0.45)))
        self._instruction_group.add(PopMatrix())
        
        # Ring borders for definition
        self._instruction_group.add(PushMatrix())
        self._instruction_group.add(Translate(center_x, center_y))
        # Outer edge
        self._instruction_group.add(Color(0.90, 0.88, 0.83, 1))
        self._instruction_group.add(Line(circle=(0, 0, radius + 10, 0, 360), width=1.5))
        # Inner edge
        self._instruction_group.add(Color(0.95, 0.93, 0.88, 1))
        self._instruction_group.add(Line(circle=(0, 0, inner_radius, 0, 360), width=1))
        self._instruction_group.add(PopMatrix())
        
        # Dotted progress line (dark teal)
        # Draw dots along ~85% of the circle
        progress_degrees = 360 * self.progress  # 306 degrees for 85%
        start_angle = -90  # Start from top
        num_dots = int(progress_degrees / 8)  # Approximately one dot every 8 degrees
        dot_radius = 3
        
        self._instruction_group.add(PushMatrix())
        self._instruction_group.add(Translate(center_x, center_y))
        self._instruction_group.add(Color(0.027, 0.204, 0.306, 1))  # Dark teal #07344E
        for i in range(num_dots):
            angle_rad = math.radians(start_angle + (progress_degrees * i / num_dots))
            x = (radius + 10) * math.cos(angle_rad)
            y = (radius + 10) * math.sin(angle_rad)
            self._instruction_group.add(Ellipse(size=(dot_radius * 2, dot_radius * 2), pos=(x - dot_radius, y - dot_radius)))
        self._instruction_group.add(PopMatrix())
        
        # Add instruction group to canvas
        self.canvas.add(self._instruction_group)

