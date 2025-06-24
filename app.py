import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# --- Function to process a single Excel file and return processed DataFrame ---
def process_gpr_excel(file):
    # Read Excel (assume first sheet, header in row 1)
    df = pd.read_excel(file, engine="openpyxl")
    
    # Ensure at least 4 columns for layers
    df = df.iloc[:, :4]
    df.columns = ['AC', 'Base', 'SubBase', 'Lower SubBase']
    
    # Add Chainage column (0.25, 0.50, ...)
    df.insert(0, 'Chainage', [(i+1)*0.25 for i in range(len(df))])
    
    # Cumulative boundary calculation with stop-at-empty logic
    boundaries = []
    for _, row in df.iterrows():
        vals = []
        if pd.notnull(row['AC']):
            vals.append(row['AC'])
        else:
            boundaries.append([None, None, None, None])
            continue
        if pd.notnull(row['Base']):
            vals.append(vals[-1] + row['Base'])
        else:
            vals += [None, None, None][:(4-len(vals))]
            boundaries.append(vals)
            continue
        if pd.notnull(row['SubBase']):
            vals.append(vals[-1] + row['SubBase'])
        else:
            vals += [None, None][:(4-len(vals))]
            boundaries.append(vals)
            continue
        if pd.notnull(row['Lower SubBase']):
            vals.append(vals[-1] + row['Lower SubBase'])
        else:
            vals += [None][:(4-len(vals))]
        boundaries.append(vals)
    # Add boundaries to DataFrame
    df['AC_boundary'] = [b[0] for b in boundaries]
    df['Base_boundary'] = [b[1] for b in boundaries]
    df['SubBase_boundary'] = [b[2] for b in boundaries]
    df['LowerSubBase_boundary'] = [b[3] for b in boundaries]
    return df

# --- Function to plot the processed DataFrame as a Plotly chart ---
def plot_gpr_chart(df, file_name):
    colors = {
        'AC': 'black',
        'Base': 'rgb(0,112,192)',
        'SubBase': 'rgb(237,125,49)',
        'Lower SubBase': 'rgb(112,173,71)'
    }
    fig = go.Figure()
    # Add each boundary as a line
    fig.add_trace(go.Scatter(
        x=df['Chainage'], y=df['AC_boundary'],
        mode='lines', name='AC', line=dict(color=colors['AC'], width=3)
    ))
    fig.add_trace(go.Scatter(
        x=df['Chainage'], y=df['Base_boundary'],
        mode='lines', name='Base', line=dict(color=colors['Base'], width=3)
    ))
    fig.add_trace(go.Scatter(
        x=df['Chainage'], y=df['SubBase_boundary'],
        mode='lines', name='SubBase', line=dict(color=colors['SubBase'], width=3)
    ))
    fig.add_trace(go.Scatter(
        x=df['Chainage'], y=df['LowerSubBase_boundary'],
        mode='lines', name='Lower SubBase', line=dict(color=colors['Lower SubBase'], width=3)
    ))
    # Layout settings
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
    # Only horizontal gridlines
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    return fig

# --- Streamlit UI ---
st.set_page_config(page_title="GPR Depth Profile Chart Generator", layout="wide")
st.title("GPR Depth Profile Chart Generator")

st.markdown("""
Upload one or more Excel files with GPR data.<br>
Each file should have columns:<br>
<b>B:</b> AC, <b>C:</b> Base, <b>D:</b> SubBase, <b>E:</b> Lower SubBase (row 1 headers).<br>
The app will generate a chart for each file, with your specified formatting.
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload Excel files", type=["xlsx"], accept_multiple_files=True
)

if uploaded_files:
    for file in uploaded_files:
        file_name = file.name
        # Process data
        df = process_gpr_excel(file)
        # Plot chart
        fig = plot_gpr_chart(df, file_name.split('.')[0])
        st.subheader(f"Chart for: {file_name}")
        st.plotly_chart(fig, use_container_width=True)
        # Download as PNG
        img_bytes = fig.to_image(format="png")
        st.download_button(
            label=f"Download {file_name.split('.')[0]} Chart as PNG",
            data=img_bytes,
            file_name=f"{file_name.split('.')[0]}_chart.png",
            mime="image/png"
        )
