import cadquery as cq
import math
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class S3MTimingBelt:
    """
    Class for generating S3M timing belts.
    
    Attributes:
        length_mm (float): Total length of the belt in millimeters
        num_teeth (int): Number of teeth on the belt
        width (float): Width of the belt in millimeters (default is 4.0mm)
        scale_factor (float): Scale factor to compensate for material shrinkage (1.0 = 100%)
    """
    length_mm: float
    num_teeth: int
    width: float = 4.0
    scale_factor: float = 1.0

    # S3M Standard Parameters
    PITCH: float = 3.0
    BELT_THICKNESS: float = 2.3
    TOOTH_HEIGHT: float = 1.4
    TOOTH_TOP_WIDTH: float = 1.5
    TOOTH_BOTTOM_WIDTH: float = 2.2

    @property
    def radius(self) -> float:
        """Calculate belt radius based on length."""
        return self.length_mm / (2 * math.pi)

    def _generate_tooth_profile(self) -> List[Tuple[float, float]]:
        """Generate the points for a single tooth profile."""
        inner_radius = self.radius - self.BELT_THICKNESS
        return [
            (inner_radius + self.TOOTH_HEIGHT, 0),  # Start at tooth base
            (inner_radius, -self.TOOTH_BOTTOM_WIDTH/2),  # Bottom outer
            (inner_radius, self.TOOTH_BOTTOM_WIDTH/2),  # Bottom inner
            (inner_radius + self.TOOTH_HEIGHT, 0),  # Back to start
        ]

    def generate_model(self) -> cq.Workplane:
        """
        Generate the complete belt model.
        """
        # Create base belt ring
        outer_radius = self.radius
        inner_radius = self.radius - self.BELT_THICKNESS
        
        belt = (
            cq.Workplane("XY")
            .circle(outer_radius)
            .circle(inner_radius)  # Create inner circle for belt thickness
            .extrude(self.width)
        )

        # Generate teeth
        tooth_angle = 360.0 / self.num_teeth
        tooth_profile = self._generate_tooth_profile()

        for i in range(self.num_teeth):
            angle = i * tooth_angle
            tooth = (
                cq.Workplane("XY")
                .transformed(rotate=(0, 0, angle))
                .polyline(tooth_profile)
                .close()
                .extrude(self.width)
            )
            belt = belt.cut(tooth)

        # Apply scaling if needed
        if self.scale_factor != 1.0:
            scaled_shape = belt.val().scale(self.scale_factor)
            belt = cq.Workplane("XY").add(scaled_shape)

        return belt

    def export_stl(self, filepath: str) -> None:
        """
        Export the belt model to an STL file.
        
        Args:
            filepath (str): Path where the STL file should be saved
        """
        model = self.generate_model()
        cq.exporters.export(model, filepath)
        
    def export_step(self, filepath: str) -> None:
        """
        Export the belt model to a STEP file.
        
        Args:
            filepath (str): Path where the STEP file should be saved
        """
        model = self.generate_model()
        cq.exporters.export(model, filepath, 'STEP')

# Recommended print settings
PRINT_SETTINGS = {
    "material": "TPU 95A",
    "layer_height": 0.1,  # mm
    "infill": 100,  # percent
    "print_speed": 25,  # mm/s
    "temperature": 225,  # °C
    "bed_temperature": 55,  # °C
    "fan_speed": 50,  # percent
    "retraction_enabled": False
}