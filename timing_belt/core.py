import cadquery as cq
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

@dataclass
class S3MTimingBelt:
    """
    Class for generating S3M timing belts.
    
    You must specify either:
      - length_mm (total belt length in millimeters) OR 
      - num_teeth (number of teeth on the belt)
    
    The other parameter will be computed assuming an S3M belt
    where the pitch (distance between tooth centers) is 3.0 mm.
    
    Attributes:
        length_mm (Optional[float]): Total belt length in millimeters.
        num_teeth (Optional[int]): Number of teeth on the belt.
        width (float): Width of the belt in millimeters (default is 4.0 mm).
        scale_factor (float): Scale factor for material shrinkage (default 1.0 = 100%).
    """
    length_mm: Optional[float] = None
    num_teeth: Optional[int] = None
    width: float = 4.0
    scale_factor: float = 1.0

    # S3M Standard Parameters (all in mm)
    PITCH: float = 3.0
    BELT_THICKNESS: float = 2.3  # thickness of the belt body
    TOOTH_HEIGHT: float = 1.4    # depth of the tooth void
    TOOTH_TOP_WIDTH: float = 1.5   # width at the void tip (inner-most part)
    TOOTH_BOTTOM_WIDTH: float = 2.2  # width at the belt inner surface

    def __post_init__(self):
        if self.length_mm is None and self.num_teeth is None:
            raise ValueError("You must specify either length_mm or num_teeth.")
        if self.length_mm is not None and self.num_teeth is not None:
            raise ValueError("Specify either length_mm or num_teeth, not both.")
        # Compute the missing parameter so that length_mm == num_teeth * PITCH.
        if self.length_mm is None:
            self.length_mm = self.num_teeth * self.PITCH
        else:
            # Compute ideal number of teeth.
            computed_teeth = self.length_mm / self.PITCH
            # Round to the nearest integer.
            self.num_teeth = round(computed_teeth)
            # Optionally adjust length_mm so that it's exactly consistent:
            self.length_mm = self.num_teeth * self.PITCH

    @property
    def pitch_radius(self) -> float:
        """
        Calculate the belt's pitch radius assuming the belt forms a full circle.
        """
        return self.length_mm / (2 * math.pi)

    @property
    def inner_surface_radius(self) -> float:
        """
        The working (toothed) surface is on the inner side.
        """
        return self.pitch_radius - self.BELT_THICKNESS

    def _generate_tooth_profile(self) -> List[Tuple[float, float]]:
        """
        Generate the points for a single tooth void profile.
        
        The void is defined as a trapezoid starting at the belt's inner surface
        and extending inward (toward the belt center) by TOOTH_HEIGHT.
        """
        base = self.inner_surface_radius  # starting at the belt's inner surface
        return [
            (base, -self.TOOTH_BOTTOM_WIDTH / 2),                        # bottom left
            (base - self.TOOTH_HEIGHT, -self.TOOTH_TOP_WIDTH / 2),         # top left
            (base - self.TOOTH_HEIGHT,  self.TOOTH_TOP_WIDTH / 2),         # top right
            (base,  self.TOOTH_BOTTOM_WIDTH / 2)                           # bottom right
        ]

    def generate_model(self) -> cq.Workplane:
        """
        Generate the complete belt model.
        
        The belt is modeled as an annular ring (a donut) representing the belt body.
        The tooth voids are subtracted from the inner surface of the belt.
        """
        # Define the belt body as an annulus.
        outer_radius = self.pitch_radius
        inner_radius = outer_radius - self.BELT_THICKNESS
        
        belt = (
            cq.Workplane("XY")
            .circle(outer_radius)
            .circle(inner_radius)
            .extrude(self.width)
        )

        # Generate tooth voids.
        tooth_profile = self._generate_tooth_profile()
        tooth_angle = 360.0 / self.num_teeth

        for i in range(self.num_teeth):
            angle = i * tooth_angle
            tooth_void = (
                cq.Workplane("XY")
                .transformed(rotate=(0, 0, angle))
                .polyline(tooth_profile)
                .close()
                .extrude(self.width)
            )
            belt = belt.cut(tooth_void)

        # Apply scaling if needed.
        if self.scale_factor != 1.0:
            scaled_shape = belt.val().scale(self.scale_factor)
            belt = cq.Workplane("XY").add(scaled_shape)

        return belt

    def export_stl(self, filepath: str) -> None:
        """
        Export the belt model to an STL file.
        
        Args:
            filepath (str): Path where the STL file should be saved.
        """
        model = self.generate_model()
        cq.exporters.export(model, filepath)
        
    def export_step(self, filepath: str) -> None:
        """
        Export the belt model to a STEP file.
        
        Args:
            filepath (str): Path where the STEP file should be saved.
        """
        model = self.generate_model()
        cq.exporters.export(model, filepath, 'STEP')

# Example usage:
# If you want to specify by number of teeth:
belt_by_teeth = S3MTimingBelt(num_teeth=70)
print(f"Length from num_teeth: {belt_by_teeth.length_mm} mm")

# If you want to specify by total length:
belt_by_length = S3MTimingBelt(length_mm=210)
print(f"Teeth from length_mm: {belt_by_length.num_teeth}")

# Recommended print settings (for reference)
PRINT_SETTINGS = {
    "material": "TPU 95A",
    "layer_height": 0.1,  # mm
    "infill": 100,        # percent
    "print_speed": 25,    # mm/s
    "temperature": 225,   # °C
    "bed_temperature": 55,  # °C
    "fan_speed": 50,      # percent
    "retraction_enabled": False
}
