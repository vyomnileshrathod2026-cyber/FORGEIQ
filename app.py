import streamlit as st
import pandas as pd
import numpy as np
import io

# Optional 3D modeling dependencies with fallback
try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Forge IQ - Manufacturing Process Selector",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Forge IQ")
st.caption("Intelligent Primary, Secondary & Additive Manufacturing Selector with CAD Load Analysis")

# ---------------------------------------------------------
# Materials Database (Primary & Secondary)
# ---------------------------------------------------------
MATERIALS = {
    "Aluminum 6061-T6": {
        "Yield Strength (MPa)": 276,
        "Tensile Strength (MPa)": 310,
        "Elastic Modulus (GPa)": 68.9,
        "Elongation (%)": 12,
        "Machinability Rating (%)": 50,
        "Density (g/cm³)": 2.70,
        "Ductility": "High",
        "Primary Recommendation": {
            "Solid Rod": "Hot Extrusion",
            "Hollow Tube": "Direct Extrusion with Mandrel",
            "Complex 3D Bracket": "High-Pressure Die Casting",
            "Thin Sheet": "Cold Rolling",
            "Structural Beam": "Extrusion"
        },
        "Secondary Recommendation": ["CNC Milling / Turning", "T6 Heat Treatment", "Anodizing Surface Finish"]
    },
    "AISI 1045 Carbon Steel": {
        "Yield Strength (MPa)": 310,
        "Tensile Strength (MPa)": 565,
        "Elastic Modulus (GPa)": 200,
        "Elongation (%)": 16,
        "Machinability Rating (%)": 65,
        "Density (g/cm³)": 7.85,
        "Ductility": "Medium",
        "Primary Recommendation": {
            "Solid Rod": "Hot Rolling",
            "Hollow Tube": "Seamless Tube Piercing & Rolling",
            "Complex 3D Bracket": "Closed-Die Hot Forging",
            "Thin Sheet": "Hot / Cold Strip Rolling",
            "Structural Beam": "Hot Structural Rolling"
        },
        "Secondary Recommendation": ["CNC Turning", "Induction Hardening / Tempering", "Black Oxide Coating"]
    },
    "Titanium Ti-6Al-4V": {
        "Yield Strength (MPa)": 880,
        "Tensile Strength (MPa)": 950,
        "Elastic Modulus (GPa)": 113.8,
        "Elongation (%)": 14,
        "Machinability Rating (%)": 22,
        "Density (g/cm³)": 4.43,
        "Ductility": "Medium-Low",
        "Primary Recommendation": {
            "Solid Rod": "Hot Isostatic Pressing (HIP) / Hot Forging",
            "Hollow Tube": "Extrusion with Glass Lubricant",
            "Complex 3D Bracket": "Investment Casting / Additive Manufacturing (DMLS)",
            "Thin Sheet": "Superplastic Forming / Pack Rolling",
            "Structural Beam": "Hot Extrusion"
        },
        "Secondary Recommendation": ["Low-Speed High-Torque CNC Milling", "Stress Relief Annealing", "Nitriding / PVD Coating"]
    },
    "Brass C360 (Free-Cutting)": {
        "Yield Strength (MPa)": 310,
        "Tensile Strength (MPa)": 395,
        "Elastic Modulus (GPa)": 97,
        "Elongation (%)": 23,
        "Machinability Rating (%)": 100,
        "Density (g/cm³)": 8.50,
        "Ductility": "High",
        "Primary Recommendation": {
            "Solid Rod": "Continuous Casting & Cold Drawing",
            "Hollow Tube": "Extrusion",
            "Complex 3D Bracket": "Brass Die Casting / Sand Casting",
            "Thin Sheet": "Cold Rolling",
            "Structural Beam": "Extrusion"
        },
        "Secondary Recommendation": ["High-Speed CNC Screw Machining", "Polishing / Electroplating", "Stress Relief"]
    },
    "Stainless Steel 316L": {
        "Yield Strength (MPa)": 290,
        "Tensile Strength (MPa)": 580,
        "Elastic Modulus (GPa)": 193,
        "Elongation (%)": 50,
        "Machinability Rating (%)": 36,
        "Density (g/cm³)": 8.00,
        "Ductility": "Very High",
        "Primary Recommendation": {
            "Solid Rod": "Hot Rolling & Solution Annealing",
            "Hollow Tube": "Seamless Tube Piercing or Welded Roll-Forming",
            "Complex 3D Bracket": "Investment Casting (Lost-Wax)",
            "Thin Sheet": "Cold Strip Rolling",
            "Structural Beam": "Hot Rolling"
        },
        "Secondary Recommendation": ["CNC Machining with Carbide Tooling", "Passivation", "Electropolishing"]
    }
}

df_materials = pd.DataFrame(MATERIALS).T

# ---------------------------------------------------------
# Additive Manufacturing (3D Printing) Rule Base
# ---------------------------------------------------------
ADDITIVE_MATERIALS = {
    "PLA / PETG (Standard Polymer)": {
        "Process": "FDM (Fused Deposition Modeling)",
        "Max Pressure (MPa)": 10,
        "Max Temp (°C)": 60,
        "Density (g/cm³)": 1.25,
        "Cost per Gram ($)": 0.04,
        "Best For": "Low-stress visual prototypes, jigs, and fixtures."
    },
    "Tough Resin (Photopolymer)": {
        "Process": "SLA (Stereolithography)",
        "Max Pressure (MPa)": 25,
        "Max Temp (°C)": 80,
        "Density (g/cm³)": 1.18,
        "Cost per Gram ($)": 0.15,
        "Best For": "High-precision snap-fits, fluid channels, and detailed enclosures."
    },
    "Nylon PA12": {
        "Process": "SLS (Selective Laser Sintering)",
        "Max Pressure (MPa)": 45,
        "Max Temp (°C)": 120,
        "Density (g/cm³)": 1.01,
        "Cost per Gram ($)": 0.22,
        "Best For": "Complex organic geometries, light structural brackets without supports."
    },
    "Nylon PA12 + Carbon Fiber (CF)": {
        "Process": "FDM / SLS Composite Printing",
        "Max Pressure (MPa)": 85,
        "Max Temp (°C)": 150,
        "Density (g/cm³)": 1.15,
        "Cost per Gram ($)": 0.45,
        "Best For": "High dynamic bending loads, lightweight replacement for aluminum."
    },
    "Titanium Ti-6Al-4V Powder": {
        "Process": "DMLS / SLM (Direct Metal Laser Sintering)",
        "Max Pressure (MPa)": 850,
        "Max Temp (°C)": 400,
        "Density (g/cm³)": 4.43,
        "Cost per Gram ($)": 1.80,
        "Best For": "Aerospace structural brackets, high pressure hydraulic manifolds, biomedical parts."
    },
    "Stainless Steel 316L Powder": {
        "Process": "DMLS / SLM (Direct Metal Laser Sintering)",
        "Max Pressure (MPa)": 500,
        "Max Temp (°C)": 300,
        "Density (g/cm³)": 8.00,
        "Cost per Gram ($)": 0.95,
        "Best For": "Corrosion-resistant pressure vessels, high-stress chemical hardware."
    }
}

# ---------------------------------------------------------
# UI Layout Tabs
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "🎯 Process Recommender", 
    "📊 Material Comparison Matrix", 
    "🚀 Additive & CAD Load Optimizer"
])

# ---------------------------------------------------------
# TAB 1: Process Recommender
# ---------------------------------------------------------
with tab1:
    st.subheader("Manufacturing Process Recommendation Engine")
    col1, col2 = st.columns(2)
    
    with col1:
        selected_metal = st.selectbox("Select Input Metal / Alloy:", list(MATERIALS.keys()))
        selected_shape = st.selectbox(
            "Select Target Product Geometry:",
            ["Solid Rod", "Hollow Tube", "Complex 3D Bracket", "Thin Sheet", "Structural Beam"]
        )
        metal_info = MATERIALS[selected_metal]
        primary_proc = metal_info["Primary Recommendation"].get(selected_shape, "Custom Forging/Casting")
        secondary_procs = metal_info["Secondary Recommendation"]
        
    with col2:
        st.info(f"**Selected Material Properties**\n\n"
                f"- **Yield Strength:** {metal_info['Yield Strength (MPa)']} MPa\n"
                f"- **Tensile Strength:** {metal_info['Tensile Strength (MPa)']} MPa\n"
                f"- **Elongation (Ductility):** {metal_info['Elongation (%)']}%\n"
                f"- **Machinability Index:** {metal_info['Machinability Rating (%)']}%")

    st.markdown("---")
    st.subheader("Recommended Workflow")
    res_col1, res_col2 = st.columns(2)
    
    with res_col1:
        st.success("### 1. Primary Manufacturing Process")
        st.write(f"**Recommended Method:** `{primary_proc}`")
        st.markdown(f"""
        **Engineering Rationale:**
        - Chosen based on material ductility ({metal_info['Ductility']}) and target shape constraints ({selected_shape}).
        - Establishes initial bulk geometry while optimizing grain flow and structural integrity.
        """)
        
    with res_col2:
        st.warning("### 2. Secondary Manufacturing Process(es)")
        for idx, proc in enumerate(secondary_procs, 1):
            st.write(f"**Step 2.{idx}:** {proc}")
        st.markdown("""
        **Engineering Rationale:**
        - Achieves dimensional tolerances, surface finish requirements, and target mechanical strength.
        """)

# ---------------------------------------------------------
# TAB 2: Material Comparison Matrix
# ---------------------------------------------------------
with tab2:
    st.subheader("Side-by-Side Property Comparison")
    selected_metals = st.multiselect(
        "Select 2 to 4 metals to compare:",
        options=list(MATERIALS.keys()),
        default=["Aluminum 6061-T6", "AISI 1045 Carbon Steel", "Titanium Ti-6Al-4V"]
    )
    
    if len(selected_metals) > 0:
        comp_df = df_materials.loc[selected_metals, [
            "Yield Strength (MPa)", 
            "Tensile Strength (MPa)", 
            "Elastic Modulus (GPa)", 
            "Elongation (%)", 
            "Machinability Rating (%)",
            "Density (g/cm³)"
        ]]
        st.dataframe(comp_df, use_container_width=True)
        st.subheader("Mechanical Property Visual Comparison")
        st.bar_chart(comp_df[["Yield Strength (MPa)", "Tensile Strength (MPa)"]])
    else:
        st.warning("Please select at least one material to display comparison data.")

# ---------------------------------------------------------
# TAB 3: Additive Manufacturing & CAD Load Optimizer (NEW)
# ---------------------------------------------------------
with tab3:
    st.subheader("3D Printing Material & Process Selection Engine")
    st.caption("Upload a SolidWorks STL CAD file and specify pressure/load constraints to evaluate additive manufacturing feasibility.")
    
    cad_col1, cad_col2 = st.columns([1, 1])
    
    mesh_obj = None
    volume_cm3 = 45.2  # Default sample volume if no file uploaded
    surface_area_cm2 = 110.5
    bounds_mm = [50.0, 40.0, 30.0]
    
    with cad_col1:
        st.markdown("#### 1. CAD Model & Structural Requirements")
        uploaded_file = st.file_uploader("Upload SolidWorks STL File (.stl):", type=["stl"])
        use_demo = st.button("📦 Load Sample CAD Geometry (Bracket)")
        
        if uploaded_file is not None and TRIMESH_AVAILABLE:
            try:
                mesh_obj = trimesh.load(io.BytesIO(uploaded_file.read()), file_type="stl")
                volume_cm3 = max(abs(mesh_obj.volume) / 1000.0, 0.1) # mm³ to cm³
                surface_area_cm2 = abs(mesh_obj.area) / 100.0        # mm² to cm²
                bounds_mm = mesh_obj.extents                       # mm
                st.success(f"Successfully loaded CAD Model: **{uploaded_file.name}**")
            except Exception as e:
                st.error(f"Error parsing STL file: {e}")
        elif use_demo:
            st.info("Loaded demo CAD bracket model properties.")
        
        st.markdown("---")
        st.markdown("#### 2. Operating Environment & Pressure Distribution")
        
        operating_pressure = st.slider(
            "Max Operating Pressure / Stress (MPa):",
            min_value=1, max_value=600, value=35, step=5,
            help="Specify the hydrostatic pressure or yield stress expected on the part."
        )
        
        operating_temp = st.slider(
            "Max Working Temperature (°C):",
            min_value=20, max_value=350, value=50, step=5
        )
        
        load_type = st.radio(
            "Primary Load Type:",
            ["Static Tension / Compression", "Dynamic Bending & Fatigue", "High Impact & Thermal Stress"],
            horizontal=True
        )

    with cad_col2:
        st.markdown("#### 3. Interactive CAD Model Visualizer")
        
        if PLOTLY_AVAILABLE and mesh_obj is not None:
            # Render actual uploaded STL using Plotly Mesh3d
            vertices = mesh_obj.vertices
            faces = mesh_obj.faces
            fig = go.Figure(data=[
                go.Mesh3d(
                    x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
                    i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
                    color='crimson', opacity=0.8, name='CAD Mesh'
                )
            ])
            fig.update_layout(
                scene=dict(xaxis_title='X (mm)', yaxis_title='Y (mm)', zaxis_title='Z (mm)'),
                margin=dict(l=0, r=0, b=0, t=30),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Demo 3D visual box representation
            st.info("3D Visualizer Active (Upload an `.stl` file to see real-time mesh rendering).")
            st.metric("Part Volume", f"{volume_cm3:.2f} cm³")
            st.metric("Surface Area", f"{surface_area_cm2:.2f} cm²")
            st.write(f"**Bounding Box Dimensions:** {bounds_mm[0]:.1f} × {bounds_mm[1]:.1f} × {bounds_mm[2]:.1f} mm")

    st.markdown("---")
    st.subheader("Additive Manufacturing Recommendation Output")
    
    # Selection Logic based on Pressure, Temp, and Load Type
    recommended_material_name = None
    
    if operating_pressure <= 10 and operating_temp <= 60:
        recommended_material_name = "PLA / PETG (Standard Polymer)"
    elif operating_pressure <= 25 and operating_temp <= 80 and load_type == "Static Tension / Compression":
        recommended_material_name = "Tough Resin (Photopolymer)"
    elif operating_pressure <= 45 and operating_temp <= 120:
        recommended_material_name = "Nylon PA12"
    elif operating_pressure <= 85 and operating_temp <= 150:
        recommended_material_name = "Nylon PA12 + Carbon Fiber (CF)"
    elif operating_pressure > 85 or operating_temp > 150:
        if "Thermal" in load_type or operating_temp > 250:
            recommended_material_name = "Titanium Ti-6Al-4V Powder"
        else:
            recommended_material_name = "Stainless Steel 316L Powder"
            
    rec_mat_data = ADDITIVE_MATERIALS[recommended_material_name]
    
    # Calculate mass and cost
    part_mass_g = volume_cm3 * rec_mat_data["Density (g/cm³)"]
    est_cost_usd = part_mass_g * rec_mat_data["Cost per Gram ($)"]
    est_print_time_hrs = max(volume_cm3 * 0.15, 0.5)
    
    rec_col1, rec_col2, rec_col3 = st.columns(3)
    
    with rec_col1:
        st.success(f"### Recommended 3D Printing Tech\n**{rec_mat_data['Process']}**")
        st.write(f"**Selected Material:** `{recommended_material_name}`")
        st.write(f"**Application Suitability:** {rec_mat_data['Best For']}")
        
    with rec_col2:
        st.info("### Part Mass & Cost Estimate")
        st.metric("Estimated Part Mass", f"{part_mass_g:.1f} grams")
        st.metric("Estimated Material Cost", f"${est_cost_usd:.2f} USD")
        
    with rec_col3:
        st.warning("### Production Metrics")
        st.metric("Est. Print Time", f"{est_print_time_hrs:.1f} hours")
        st.metric("Pressure Safety Factor", f"{(rec_mat_data['Max Pressure (MPa)'] / operating_pressure):.2f}x")