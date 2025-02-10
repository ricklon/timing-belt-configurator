"""Core functionality for generating timing belts."""
from dataclasses import dataclass
import numpy as np
from typing import List, Tuple
import math
import cadquery as cq

# Print settings for TPU belts
PRINT_SETTINGS = {
    "material": "TPU 95A",
    "layer_height": "0.2mm",
    "infill": "100%",
    "wall_thickness": "1.2mm",
    "print_temperature": "230°C",
    "bed_temperature": "45°C",
    "print_speed": "25mm/s",
    "retraction_speed": "25mm/s",
    "retraction_distance": "1mm",
    "fan_speed": "50%"
}

@dataclass
class ToothProfile:
    """S3M timing belt tooth profile parameters"""
    pitch: float = 3.0  # mm
    tooth_height: float = 1.4  # mm
    tooth_width_at_base: float = 2.0  # mm
    tooth_radius: float = 0.6  # mm
    belt_thickness: float = 2.0  # mm

class S3MTimingBelt:
    """Generator for S3M timing belts"""
    
    def __init__(self, length_mm: float = None, num_teeth: int = None, width: float = 9.0, scale_factor: float = 1.005):
        """Initialize belt parameters"""
        self.profile = ToothProfile()
        
        # Set length and teeth based on input
        if length_mm is not None:
            self.length_mm = length_mm
            self.num_teeth = round(length_mm / self.profile.pitch)
        elif num_teeth is not None:
            self.num_teeth = num_teeth
            self.length_mm = num_teeth * self.profile.pitch
        else:
            raise ValueError("Either length_mm or num_teeth must be provided")
            
        self.width = width
        self.scale_factor = scale_factor
        
        # Calculate pitch radius from length
        self.pitch_radius = self.length_mm / (2 * math.pi)
        
        # Validate inputs
        if self.num_teeth < 10:
            raise ValueError("Number of teeth must be at least 10")
        if width < 3.0:
            raise ValueError("Belt width must be at least 3mm")

    def _create_single_tooth(self, debug=False) -> cq.Workplane:
        """Create a single tooth solid with improved placement"""
        # Calculate positions
        inner_radius = self.pitch_radius - self.profile.belt_thickness
        tooth_width = self.profile.tooth_width_at_base
        tooth_tip_width = tooth_width * 0.8
        
        # Add extra depth to ensure complete cut through inner circle
        extra_depth = 1.0  # Add 1mm extra depth to ensure complete cut
        
        # Points for tooth profile (counter-clockwise from bottom left)
        points = [
            (-tooth_width/2, inner_radius - extra_depth),  # Extended bottom left
            (-tooth_tip_width/2, inner_radius + self.profile.tooth_height),  # Top left
            (tooth_tip_width/2, inner_radius + self.profile.tooth_height),   # Top right
            (tooth_width/2, inner_radius - extra_depth),    # Extended bottom right
            (-tooth_width/2, inner_radius - extra_depth)    # Back to start
        ]
        
        if debug:
            print(f"Inner radius: {inner_radius}")
            print(f"Tooth width at base: {tooth_width}")
            print(f"Tooth points: {points}")
        
        # Create tooth profile and extrude
        tooth = (cq.Workplane("XY")
                .polyline(points)
                .close()
                .extrude(self.width))
        
        return tooth

    def _create_3d_belt(self) -> cq.Workplane:
        """Create the complete 3D belt model"""
        try:
            # Create basic belt body (annulus)
            belt = (cq.Workplane("XY")
                   .circle(self.pitch_radius)
                   .circle(self.pitch_radius - self.profile.belt_thickness)
                   .extrude(self.width))
            
            # Create a single tooth with debug output
            base_tooth = self._create_single_tooth(debug=True)
            
            # Create all teeth by rotating and combining
            angle = 360.0 / self.num_teeth
            
            # Create first tooth
            teeth = base_tooth
            
            # Add remaining teeth
            for i in range(1, self.num_teeth):
                # Create rotated copy of tooth
                rotated = base_tooth.rotate((0,0,0), (0,0,1), i * angle)
                teeth = teeth.union(rotated)
            
            # Cut all teeth from belt body
            result = belt.cut(teeth)
            
            # Apply scaling if needed
            if self.scale_factor != 1.0:
                scaled_solid = result.val().scale(self.scale_factor)
                result = cq.Workplane("XY").add(scaled_solid)
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Failed to create belt geometry: {str(e)}")

    def export_stl(self, filename: str) -> None:
        """Export the belt as STL file"""
        try:
            belt = self._create_3d_belt()
            cq.exporters.export(belt, filename, 'STL')
        except Exception as e:
            raise RuntimeError(f"Failed to export STL: {str(e)}")

    def export_step(self, filename: str) -> None:
        """Export the belt as STEP file"""
        try:
            belt = self._create_3d_belt()
            cq.exporters.export(belt, filename, 'STEP')
        except Exception as e:
            raise RuntimeError(f"Failed to export STEP: {str(e)}")