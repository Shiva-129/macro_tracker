import plotly.graph_objects as go
import config

def plot_event_impact(event_row, impact_data):
    """
    Generates a Plotly chart showing the impact of the event on various assets.
    """
    event_name = event_row['event']
    event_time = event_row['date']
    actual = event_row.get('actual', 'N/A')
    estimate = event_row.get('estimate', 'N/A')
    
    fig = go.Figure()
    
    # Calculate volatility for each asset to determine line style
    # Assets with bigger moves get thicker, brighter lines
    max_moves = {}
    for asset_name, df in impact_data.items():
        max_moves[asset_name] = df['pct_change'].abs().max()
    
    # Sort assets by volatility to draw important ones on top
    sorted_assets = sorted(max_moves.items(), key=lambda x: x[1])
    
    # Define groups for buttons
    core_assets = ["Equities", "FX", "Rates", "Volatility"]
    sector_assets = ["Tech", "Financials", "Healthcare", "Cons. Disc", "Cons. Staples", 
                     "Energy", "Utilities", "Industrials", "Materials", "Real Estate", "Comm. Svcs"]
    
    for asset_name, _ in sorted_assets:
        df = impact_data[asset_name]
        move_size = max_moves[asset_name]
        
        # Determine style based on move size
        if move_size > 0.5: # Big move (>0.5%)
            width = 3
            opacity = 1.0
        elif move_size > 0.2: # Medium move
            width = 2
            opacity = 0.8
        else: # Small move (noise)
            width = 1
            opacity = 0.4
            
        # Determine group for visibility toggling
        # We use 'legendgroup' to group them, but for buttons we need to know indices
        # For simplicity, we'll just add them all and use the button logic to show/hide
        
        fig.add_trace(go.Scatter(
            x=df['minutes_relative'],
            y=df['pct_change'],
            mode='lines',
            name=asset_name,
            line=dict(width=width),
            opacity=opacity,
            hovertemplate='%{y:.2f}%'
        ))
        
    # Add vertical line at t=0 (Event Time)
    fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="white", annotation_text="Release")
    
    # Create Buttons for Views
    # We need to know which traces belong to which group.
    # Since we added them in sorted order, it's tricky to know indices.
    # A simpler way for buttons is to rely on trace names.
    
    # Actually, Plotly buttons use 'visible' array (True/False/LegendOnly)
    # We need to construct these arrays.
    
    # Let's rebuild the trace adding loop to be simpler for button logic
    # We will add Core first, then Sectors, to make indices predictable? 
    # No, sorting by volatility is better for visuals.
    
    # Alternative: Use 'legendgroup' and just let user click legend? 
    # User asked for buttons.
    
    # Let's stick to the sorted addition for visual layering, but we'll calculate visibility masks dynamically.
    
    total_traces = len(fig.data) # Includes the vertical line? No, vline is a shape/annotation usually, but add_vline adds a shape.
    # fig.data only contains the Scatters we added.
    
    # Helper to create visibility mask
    def create_mask(target_group):
        mask = []
        for trace in fig.data:
            name = trace.name
            # Check if name matches any in the target group
            # We need to match partial names because config has "Equities (SPY)" etc.
            is_core = any(c in name for c in ["SPY", "EURUSD", "TNX", "VIX"])
            is_sector = any(s in name for s in ["XLK", "XLF", "XLV", "XLY", "XLP", "XLE", "XLU", "XLI", "XLB", "XLRE", "XLC"])
            
            if target_group == "all":
                mask.append(True)
            elif target_group == "core":
                mask.append(True if is_core else False)
            elif target_group == "sectors":
                mask.append(True if is_sector else False)
        return mask

    fig.update_layout(
        title=title_text,
        xaxis_title="Minutes Relative to Release",
        yaxis_title="Change (%)",
        template="plotly_dark",
        hovermode="x unified",
        dragmode='pan',
        
        # Add Buttons
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0,
                y=1.15,
                showactive=True,
                buttons=list([
                    dict(label="All",
                         method="update",
                         args=[{"visible": create_mask("all")}]),
                    dict(label="Core Assets",
                         method="update",
                         args=[{"visible": create_mask("core")}]),
                    dict(label="Sectors",
                         method="update",
                         args=[{"visible": create_mask("sectors")}])
                ]),
            )
        ]
    )
    
    # Enable scroll zoom for easier navigation
    config_options = {
        'scrollZoom': True,
        'displayModeBar': True,
        'displaylogo': False,
    }
    
    return fig, config_options
