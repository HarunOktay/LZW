import plotly.express as px
import plotly.graph_objects as go

def create_performance_chart(df):
    """
    Create an interactive performance chart using plotly
    """
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add traces for each bit length - Actual Performance
    for bit_length in sorted(df['Code Bit Length'].unique()):
        df_bit = df[df['Code Bit Length'] == bit_length]
        
        # Actual performance (without dictionary)
        fig.add_trace(go.Scatter(
            x=df_bit['Max Dictionary Size'],
            y=df_bit['Compression Performance (%)'],
            mode='lines+markers',
            name=f'{bit_length} bits (Actual)',
            line=dict(dash='solid')
        ))
        
        # Theoretical performance (with dictionary)
        fig.add_trace(go.Scatter(
            x=df_bit['Max Dictionary Size'],
            y=df_bit['Compression Performance with Dict (%)'],
            mode='lines+markers',
            name=f'{bit_length} bits (With Dict)',
            line=dict(dash='dot')
        ))
    
    # Update layout
    fig.update_layout(
        title='Compression Performance by Dictionary Size',
        xaxis_title='Dictionary Size',
        yaxis_title='Compression Performance (%)',
        hovermode='x unified',
        showlegend=True,
        legend_title='Code Bit Length',
        # Add a horizontal line at y=0 to show where compression becomes expansion
        shapes=[
            dict(
                type='line',
                yref='y',
                y0=0,
                y1=0,
                xref='paper',
                x0=0,
                x1=1,
                line=dict(
                    color='red',
                    width=1,
                    dash='dash'
                )
            )
        ]
    )
    
    # Update axes
    fig.update_xaxes(type='log', tickformat=',d')
    
    return fig
