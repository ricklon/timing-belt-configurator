import streamlit as st
import tempfile
import os
from typing import Tuple
from timing_belt.core import S3MTimingBelt, PRINT_SETTINGS

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    defaults = {
        "length": 210.0,
        "num_teeth": 70,
        "belt_width": 4.0,
        "scale_factor": 100.5
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def create_input_columns() -> Tuple[st.columns, st.columns]:
    """Create and return the input columns for the UI."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Belt Specifications")
        st.session_state.length = st.number_input(
            "Belt Length (mm)", 
            min_value=50.0,
            max_value=1000.0,
            value=st.session_state.length,
            step=1.0,
            help="Total length of the belt in millimeters"
        )
        
        st.session_state.num_teeth = st.number_input(
            "Number of Teeth",
            min_value=10,
            max_value=200,
            value=st.session_state.num_teeth,
            step=1,
            help="Total number of teeth on the belt"
        )

    with col2:
        st.subheader("Additional Parameters")
        st.session_state.belt_width = st.number_input(
            "Belt Width (mm)",
            min_value=3.0,
            max_value=30.0,
            value=st.session_state.belt_width,
            step=0.5,
            help="Width of the belt (standard S3M is 9mm)"
        )
        
        st.session_state.scale_factor = st.slider(
            "Scale Factor (%)",
            min_value=100.0,
            max_value=102.0,
            value=st.session_state.scale_factor,
            step=0.1,
            help="Compensation for material shrinkage"
        )

    return col1, col2

def show_print_settings():
    """Display the recommended print settings."""
    with st.expander("📝 Recommended Print Settings"):
        st.markdown("### Print Settings for TPU")
        settings_text = "\n".join([
            f"- **{k.replace('_', ' ').title()}**: {v}"
            for k, v in PRINT_SETTINGS.items()
        ])
        st.markdown(settings_text)
        
        st.markdown("""
        ### Tips
        - Ensure your printer is calibrated for flexible materials
        - Consider using direct drive extruder for better TPU handling
        - Clean the build plate thoroughly before printing
        - If available, use an enclosure to maintain consistent temperature
        """)

def generate_belt():
    """Generate the belt model and provide download options."""
    with st.spinner("Generating timing belt model..."):
        try:
            # Create a belt instance
            belt = S3MTimingBelt(
                length_mm=st.session_state.length,
                num_teeth=st.session_state.num_teeth,
                width=st.session_state.belt_width,
                scale_factor=st.session_state.scale_factor / 100.0
            )
            
            # Create temporary files for both formats
            with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as stl_file, \
                 tempfile.NamedTemporaryFile(delete=False, suffix='.step') as step_file:
                
                # Export both formats
                belt.export_stl(stl_file.name)
                belt.export_step(step_file.name)
                
                # Create columns for download buttons
                col1, col2 = st.columns(2)
                
                # STL Download Button
                with col1:
                    with open(stl_file.name, 'rb') as file:
                        st.download_button(
                            label="Download STL file",
                            data=file,
                            file_name=f"s3m_belt_{st.session_state.length}mm_{st.session_state.num_teeth}t.stl",
                            mime="application/octet-stream"
                        )
                
                # STEP Download Button
                with col2:
                    with open(step_file.name, 'rb') as file:
                        st.download_button(
                            label="Download STEP file",
                            data=file,
                            file_name=f"s3m_belt_{st.session_state.length}mm_{st.session_state.num_teeth}t.step",
                            mime="application/octet-stream"
                        )
                
                # Show success message
                st.success("Belt model generated successfully!")
                
                # Cleanup temporary files
                os.unlink(stl_file.name)
                os.unlink(step_file.name)
                
        except Exception as e:
            st.error(f"Error generating belt: {str(e)}")

def main():
    st.set_page_config(page_title="Timing Belt Generator", layout="wide")
    
    st.title("S3M Timing Belt Generator")
    st.markdown("""
    This tool helps you generate custom S3M timing belts for 3D printing. Configure your desired
    specifications and download the resulting STL file.
    """)

    initialize_session_state()
    create_input_columns()
    show_print_settings()

    if st.button("Generate Belt STL", type="primary"):
        generate_belt()

    st.markdown("""---
    ### About S3M Timing Belts
    S3M (Super Torque 3mm) timing belts have a 3mm pitch and curvilinear tooth profile. They're commonly 
    used in 3D printers, CNC machines, and other precision motion applications.
    """)

if __name__ == "__main__":
    main()