import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def process_gpr_excel(file):
    # Read Excel (assume first sheet, header in row 1)
    df = pd.read_excel(file, engine="openpyxl")
    # Use columns 2-5 for AC, Base, SubBase, Lower SubBase
    if df.shape[1] < 5:
        st.error("Excel file must have at least 5 columns: [index/chainage/ID], AC, Base, SubBase, Lower SubBase.")
        return None
    df_layers = df.iloc[:, 1:5].copy()
    df_layers.columns = ['AC', 'Base', 'SubBase', 'Lower SubBase']
    # Add Chainage column (0.25, 0.50, ...)
    df_layers.insert(0, 'Chainage', [(i+1)*0.25 for i in range(len(df_layers))])

    # Prepare boundaries columns
    ac_b, base_b, subbase_b, lowersubbase_b = [], [], [], []

    for _, row in df_layers.iterrows():
        vals = [row['AC'], row['Base'], row['SubBase'], row['Lower SubBase']]
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
        while len(cumsums) < 4:
            cumsums.append(None)
        ac_b.append(cumsums[0])
        base_b.append(cumsums[1])
        subbase_b.append(cumsums[2])
        lowersubbase_b.append(cumsums[3])

    df_layers['AC_boundary'] = ac_b
    df_layers['Base_boundary'] = base_b
    df_layers['SubBase_boundary'] = subbase_b
    df_layers['LowerSubBase_boundary'] = lowersubbase_b
    return df_layers

def plot_gpr_chart(df, file_name):
    colors = {
        'AC': 'black',
        'Base': 'rgb(0,112,192)',
        'SubBase': 'rgb(237,125,49)',
        'Lower SubBase': 'rgb(112,173,71)'
    }
    fig = go.Figure()
    if df['AC_boundary'].notnull().any():
        fig.add_trace(go.Scatter(
            x=df['Chainage'], y=df['AC_boundary'],
            mode='lines', name='AC', line=dict(color=colors['AC'], width=3)
        ))
    if df['Base_boundary'].notnull().any():
        fig.add_trace(go.Scatter(
            x=df['Chainage'], y=df['Base_boundary'],
            mode='lines', name='Base', line=dict(color=colors['Base'], width=3)
        ))
    if df['SubBase_boundary'].notnull().any():
        fig.add_trace(go.Scatter(
            x=df['Chainage'], y=df['SubBase_boundary'],
            mode='lines', name='SubBase', line=dict(color=colors['SubBase'], width=3)
        ))
    if df['LowerSubBase_boundary'].notnull().any():
        fig.add_trace(go.Scatter(
            x=df['Chainage'], y=df['LowerSubBase_boundary'],
            mode='lines', name='Lower SubBase', line=dict(color=colors['Lower SubBase'], width=3)
        ))
    fig.update_layout(
        title=file_name,
        xaxis=dict(
            title='Chainage (m)',
            showline=True, linewidth=3, linecolor='black', mirror=True, ticks='outside'
        ),
        yaxis=dict(
            title='Depth (m)',
            showline=True, linewidth=3, linecolor='black', mirror=True, ticks='outside',
            autorange='reversed', range=[100, 0], dtick=10, gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation='h', yanchor='bottom', y=-0.25, xanchor='center', x=0.5),
        margin=dict(l=60, r=20, t=60, b=60),
        height=600
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    return fig

st.set_page_config(page_title="GPR Depth Profile Chart Generator", layout="wide")
st.title("GPR Depth Profile Chart Generator")

st.markdown("""
Upload one or more Excel files with GPR data.<br>
Each file should have **five columns**:<br>
<b>First column:</b> Index, location, or chainage<br>
<b>Second:</b> AC<br>
<b>Third:</b> Base<br>
<b>Fourth:</b> SubBase<br>
<b>Fifth:</b> Lower SubBase<br>
The app will calculate cumulative boundaries and generate the required chart.
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload Excel files", type=["xlsx"], accept_multiple_files=True
)

if uploaded_files:
    for file in uploaded_files:
        file_name = file.name
        df = process_gpr_excel(file)
        if df is None:
            continue
        st.subheader(f"Preview of processed data for: {file_name}")
        st.write(df.head(20))  # Show the first 20 rows for debugging

        # Check if all boundary columns are empty
        if (
            df['AC_boundary'].notnull().sum() == 0 and
            df['Base_boundary'].notnull().sum() == 0 and
            df['SubBase_boundary'].notnull().sum() == 0 and
            df['LowerSubBase_boundary'].notnull().sum() == 0
        ):
            st.warning("No valid data to plot. Please check your Excel file for correct structure and numeric values.")
        else:
            fig = plot_gpr_chart(df, file_name.split('.')[0])
            st.subheader(f"Chart for: {file_name}")
            st.plotly_chart(fig, use_container_width=True)
            # Download as PNG (Plotly >=5.0 required)
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
