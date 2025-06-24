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
        vals = [None, None, None, None]
        # AC boundary
        if pd.notnull(row['AC']):
            vals[0] = row['AC']
        else:
            boundaries.append(vals)
            continue
        # Base boundary
        if pd.notnull(row['Base']) and pd.notnull(vals[0]):
            vals[1] = vals[0] + row['Base']
        else:
            boundaries.append(vals)
            continue
        # SubBase boundary
        if pd.notnull(row['SubBase']) and pd.notnull(vals[1]):
            vals[2] = vals[1] + row['SubBase']
        else:
            boundaries.append(vals)
            continue
        # Lower SubBase boundary
        if pd.notnull(row['Lower SubBase']) and pd.notnull(vals[2]):
            vals[3] = vals[2] + row['Lower SubBase']
        boundaries.append(vals)
    # Add boundaries to DataFrame
    df['AC_boundary'] = [b[0] for b in boundaries]
    df['Base_boundary'] = [b[1] for b in boundaries]
    df['SubBase_boundary'] = [b[2] for b in boundaries]
    df['LowerSubBase_boundary'] = [b[3] for b in boundaries]
    return df
