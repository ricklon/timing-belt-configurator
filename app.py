import streamlit as st
import tempfile
import os
from timing_belt.core import S3MTimingBelt, PRINT_SETTINGS

def initialize_session_state():
    """Initialize session state variables."""
    defaults = {
        "length": 210.0,
        "num_teeth": 70,
        "belt_width": 4.0,
        "scale_factor": 100.5,
        "calculated_belt": None,
        "stl_data": None,
        "step_data": None,
        "files_generated": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def on_length_change():
    """Update number of teeth when length changes."""
    st.session_state.num_teeth = int(round(st.session_state.length / 3))

def on_teeth_change():
    """Update length when number of teeth changes."""
    st.session_state.length = float(st.session_state.num_teeth * 3)

def calculate_belt():
    """Calculate belt parameters and create belt object."""
    try:
        belt = S3MTimingBelt(
            length_mm=st.session_state.length,
            width=st.session_state.belt_width,
            scale_factor=st.session_state.scale_factor / 100.0
        )
        st.session_state.calculated_belt = belt
        
        summary = f"""
### Final Belt Configuration
- **Length:** {belt.length_mm:.2f} mm
- **Number of Teeth:** {belt.num_teeth}
- **Belt Width:** {belt.width:.2f} mm
- **Scale Factor:** {st.session_state.scale_factor:.1f}%
- **Output Filename:** s3m_belt_{belt.length_mm:.1f}mm_{belt.num_teeth}t
"""
        st.markdown(summary)
        return True
    except Exception as e:
        st.error(f"Error in calculation: {str(e)}")
        st.session_state.calculated_belt = None
        return False

def create_input_columns():
    """Create the input interface columns."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Length & Teeth")
        st.latex(f"{st.session_state.length:.1f}\text{{ mm}} = {st.session_state.num_teeth} \\times 3\text{{ mm (pitch)}}")
            
        st.number_input(
            "Belt Length (mm)", 
            min_value=50.0,
            max_value=1000.0,
            value=st.session_state.length,
            step=1.0,
            key="length",
            on_change=on_length_change,
            help="Total length of the belt in millimeters"
        )
        st.number_input(
            "Number of Teeth",
            min_value=10,
            max_value=200,
            value=st.session_state.num_teeth,
            step=1,
            key="num_teeth",
            on_change=on_teeth_change,
            help="Total number of teeth on the belt"
        )

    with col2:
        st.markdown("### Additional Parameters")
        st.number_input(
            "Belt Width (mm)",
            min_value=3.0,
            max_value=30.0,
            value=st.session_state.belt_width,
            step=0.5,
            key="belt_width",
            help="Width of the belt (standard S3M is 9mm)"
        )
        st.slider(
            "Scale Factor (%)",
            min_value=100.0,
            max_value=102.0,
            value=st.session_state.scale_factor,
            step=0.1,
            key="scale_factor",
            help="Compensation for material shrinkage"
        )

    if st.button("Calculate", type="primary"):
        if calculate_belt():
            st.success("Belt calculated successfully!")

def main():
    st.set_page_config(page_title="Timing Belt Generator", layout="wide")
    st.title("S3M Timing Belt Generator")
    
    initialize_session_state()
    create_input_columns()
    
    if st.session_state.calculated_belt and st.button("Generate Belt Files"):
        with st.spinner("Generating timing belt model..."):
            try:
                belt = st.session_state.calculated_belt
                with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as stl_file, \
                     tempfile.NamedTemporaryFile(delete=False, suffix='.step') as step_file:
                    
                    belt.export_stl(stl_file.name)
                    belt.export_step(step_file.name)
                    
                    # Read file contents
                    with open(stl_file.name, 'rb') as f:
                        st.session_state.stl_data = f.read()
                    with open(step_file.name, 'rb') as f:
                        st.session_state.step_data = f.read()
                    
                    os.unlink(stl_file.name)
                    os.unlink(step_file.name)
                    st.session_state.files_generated = True
                    st.success("Belt model generated successfully!")
                    
            except Exception as e:
                st.error(f"Error generating belt files: {str(e)}")
                return

    # Show download buttons if files are generated
    if st.session_state.get('files_generated', False):
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download STL file",
                st.session_state.stl_data,
                f"s3m_belt_{st.session_state.calculated_belt.length_mm:.1f}mm_{st.session_state.calculated_belt.num_teeth}t.stl",
                "application/octet-stream"
            )
        with col2:
            st.download_button(
                "Download STEP file",
                st.session_state.step_data,
                f"s3m_belt_{st.session_state.calculated_belt.length_mm:.1f}mm_{st.session_state.calculated_belt.num_teeth}t.step",
                "application/octet-stream"
            )

    with st.expander("📝 Print Settings"):
        st.markdown("### Print Settings for TPU")
        settings_text = "\n".join([f"- **{k.replace('_', ' ').title()}**: {v}" for k, v in PRINT_SETTINGS.items()])
        st.markdown(settings_text)

if __name__ == "__main__":
    main()