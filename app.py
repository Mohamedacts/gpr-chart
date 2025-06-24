import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- Password protection ---
def password_protect():
    st.title("GPR Depth Profile Chart Generator")
    password = st.text_input("Enter password to access the app:", type="password")
    if password != "MohamedAli":
        st.warning("Please enter the correct password.")
        st.stop()

password_protect()

def process_gpr_excel(file):
    df = pd.read_excel(file, engine="openpyxl")
    df.columns = [str(col).strip().lower() for col in df.columns]
    layer_cols = [col for col in df.columns if "layer" in col]
    if len(layer_cols) < 3:
        st.error("Excel file must have at least columns: layer 1, layer 2, layer 3.")
        return None
    layer_cols = layer_cols[:4]
    df_layers = df[layer_cols].copy()
    std_names = ["Layer 1", "Layer 2", "Layer 3", "Layer 4"]
    df_layers.columns = std_names[:len(layer_cols)]
    df_layers.insert(0, 'Chainage', [(i+1)*0.25 for i in range(len(df_layers))])
    boundaries = []
    for _, row in df_layers.iterrows():
        vals = [row.get(name) for name in std_names[:len(layer_cols)]]
        cumsums = []
        running_sum = 0
        for v in vals:
            if v is None or (isinstance(v, float) and np.isnan(v)):
                break
            try:
                running_sum += float(v)
            except Exception:
                break
            cumsums.append(running_sum)
        while len(cumsums) < len(layer_cols):
            cumsums.append(None)
        boundaries.append(cumsums)
    for idx, name in enumerate(std_names[:len(layer_cols)]):
        df_layers[f"{name}_boundary"] = [b[idx] for b in boundaries]
    return df_layers

def plot_gpr_chart(df, graph_title):
    color_map = {
        "Layer 1": "black",
        "Layer 2": "rgb(0,112,192)",
        "Layer 3": "rgb(237,125,49)",
        "Layer 4": "rgb(112,173,71)"
    }
    fig = go.Figure()
    for layer in [col for col in df.columns if col.endswith("_boundary")]:
        base_name = layer.replace("_boundary", "")
        if df[layer].notnull().any():
            fig.add_trace(go.Scatter(
                x=df['Chainage'], y=df[layer],
                mode='lines', name=base_name, line=dict(color=color_map.get(base_name, "gray"), width=3)
            ))
    fig.update_layout(
        title=dict(
            text=graph_title,
            font=dict(color='black')
        ),
        font=dict(color='black'),
        xaxis=dict(
            title=dict(text='Chainage (m)', font=dict(color='black')),
            showline=True, linewidth=3, linecolor='black', mirror=True, ticks='outside',
            tickfont=dict(color='black'),
            dtick=1,        # Ticks every 1.0 on x-axis
            tick0=0,        # Start ticks at 0
            range=[0, 100]  # Fix axis from 0 to 100 (adjust as needed)
        ),
        yaxis=dict(
            title=dict(text='Depth (m)', font=dict(color='black')),
            showline=True, linewidth=3, linecolor='black', mirror=True, ticks='outside',
            autorange='reversed', range=[100, 0], dtick=10, gridcolor='lightgray',
            tickfont=dict(color='black')
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h', yanchor='bottom', y=-0.25, xanchor='center', x=0.5,
            font=dict(color='black')
        ),
        margin=dict(l=60, r=20, t=60, b=60),
        height=600
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    return fig

st.header("Welcome to the GPR Depth Profile Chart Generator", divider="rainbow")

st.markdown("""
Upload one or more Excel files with GPR data.<br>
Your file must have columns:<br>
<b>file name</b> (or similar), <b>layer 1</b>, <b>layer 2</b>, <b>layer 3</b>, and optionally <b>layer 4</b>.<br>
The app will calculate cumulative boundaries and generate the chart.
""", unsafe_allow_html=True)

# --- File uploader with clear-on-submit form and graph title input ---
with st.form("upload_form", clear_on_submit=True):
    uploaded_files = st.file_uploader(
        "Upload Excel files", type=["xlsx"], accept_multiple_files=True, key="uploader"
    )
    graph_title = st.text_input("Enter graph title (will appear on chart):", value="GPR Depth Profile")
    submitted = st.form_submit_button("Process / Clear All Files")

if uploaded_files and submitted:
    for file in uploaded_files:
        file_name = file.name
        df = process_gpr_excel(file)
        if df is None:
            continue
        st.subheader(f"Preview of processed data for: {file_name}")
        st.write(df.head(20))  # Show the first 20 rows for debugging

        boundary_cols = [col for col in df.columns if col.endswith("_boundary")]
        if all(df[col].notnull().sum() == 0 for col in boundary_cols):
            st.warning("No valid data to plot. Please check your Excel file for correct structure and numeric values.")
        else:
            fig = plot_gpr_chart(df, graph_title)
            st.subheader(f"Chart for: {file_name}")
            st.plotly_chart(fig, use_container_width=True)
            try:
                img_bytes = fig.to_image(format="png")
                st.download_button(
                    label=f"Download {file_name.split('.')[0]} Chart as PNG",
                    data=img_bytes,
                    file_name=f"{file_name.split('.')[0]}_chart.png",
                    mime="image/png"
                )
            except Exception as e:
                st.info("PNG download not available. (Plotly version may be <5.0 or kaleido not installed)")

# --- Credit at the bottom ---
st.markdown("""
---
**Mohamed Ali**  
Pavement Engineer  
📞 +966581764292
""")
