import pandas as pd
from dash import Dash, html, dcc, Input, Output
import os
import plotly.express as px

def load_data(file_path):
    if not os.path.exists(file_path):
        return pd.DataFrame() 
    df = pd.read_csv(file_path)
    df['year'] = df['year'].astype(int)
    df['population'] = pd.to_numeric(df['population'], errors='coerce')
    return df

def get_country_options(df):
    unique_countries = sorted(df['country'].unique())
    return [{'label': c, 'value': c} for c in unique_countries]

def get_latest_population(df, selected_country):
    country_df = df[df['country'] == selected_country]
    if country_df.empty:
        return "Keine Daten"
    latest_row = country_df.loc[country_df['year'].idxmax()]
    population_value = latest_row['population']
    formatted_value = f"{population_value:,.0f}".replace(",", ".")
    return f"{formatted_value} Einwohner ({int(latest_row['year'])})"

def create_population_chart(df, selected_country):
    filtered_df = df[df['country'] == selected_country].sort_values(by='year')
    fig = px.line(
        filtered_df, x='year', y='population',
        title=f'Bevölkerungsentwicklung: {selected_country}',
        template='plotly_white'
    )
    fig.update_traces(line_color='#007BFF', line_width=3)
    return fig

def create_comparison_chart(df, selected_year):
    """
    Top 10 mit korrekter Mrd./Mio. Schreibweise ohne hängendes Komma.
    """
    year_df = df[df['year'] == selected_year]
    top_10 = year_df.nlargest(10, 'population').copy()
    
    def format_german_units(pop):
        if pop >= 1_000_000_000:
            # Erst runden und Komma setzen, dann Mrd. anhängen
            val = f"{pop / 1_000_000_000:.2f}".replace('.', ',')
            return f"{val} Mrd."
        else:
            val = f"{pop / 1_000_000:.1f}".replace('.', ',')
            return f"{val} Mio."

    top_10['display_text'] = top_10['population'].apply(format_german_units)
    
    fig = px.bar(
        top_10, x='population', y='country', orientation='h',
        title=f'Top 10 bevölkerungsreichste Länder ({selected_year})',
        text='display_text',
        template='plotly_white'
    )
    
    fig.update_traces(
        textposition='auto', 
        textfont_size=14,
        marker_color='#2c3e50',
        cliponaxis=False
    )
    
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        xaxis={'showticklabels': False, 'title': ''},
        margin=dict(l=150, r=120), # Genug Platz für die Texte
        separators=',.' 
    )
    return fig

def create_lowest_population_chart(df, selected_year):
    """
    Erstellt ein Donut-Chart der 10 bevölkerungsärmsten Länder.
    Jetzt mit korrekten Tausenderpunkten (Deutsch).
    """
    year_df = df[df['year'] == selected_year]
    bottom_10 = year_df.nsmallest(10, 'population')
    
    fig = px.pie(
        bottom_10, 
        values='population', 
        names='country', 
        title=f'10 bevölkerungsärmste Länder ({selected_year})',
        hole=0.4,
        template='plotly_white'
    )
    
    # separators=',.' -> Erstes Zeichen ist Tausender-Trenner, zweites Dezimal-Trenner
    # Hier erzwingen wir die deutsche Darstellung: Punkt für Tausender.
    fig.update_traces(
        textinfo='value+label', 
        texttemplate='%{label}<br>%{value:,.0f}',
        textfont_size=13,
        hovertemplate='%{label}: %{value:,.0f} Einwohner'
    )
    
    # Layout-Anpassung für die deutschen Trennzeichen
    fig.update_layout(
        showlegend=False, 
        margin=dict(t=50, b=10, l=10, r=10),
        separators=',.' # WICHTIG: Ersetzt englisches Komma durch deutschen Punkt in der Anzeige
    )
    return fig

def get_growth_rate(df, selected_country):
    country_df = df[df['country'] == selected_country].sort_values('year')
    if len(country_df) < 2:
        return html.Span("Keine Vergleichsdaten", style={'color': 'gray'})
    latest_row = country_df.iloc[-1]
    previous_row = country_df.iloc[-2]
    if latest_row['year'] != previous_row['year'] + 1:
        return html.Span(f"Datenlücke", style={'color': 'gray'})
    rate = ((latest_row['population'] - previous_row['population']) / previous_row['population']) * 100
    if rate > 0.001:
        color, symbol = "#27ae60", "▲"
    elif rate < -0.001:
        color, symbol = "#e74c3c", "▼"
    else:
        color, symbol = "#7f8c8d", "●"
    return html.Span([
        f"{symbol} {rate:+.2f}% ",
        html.Span("vs. Vorjahr", style={'fontSize': '12px', 'color': '#7f8c8d'})
    ], style={'color': color, 'fontWeight': 'bold'})

def create_world_map(df, selected_year):
    """
    Docstring for create_world_map
    
    :param df: Description
    :param selected_year: Description
    #DataFrame auf das aktuelle Jahr filtern
    """
    fig = px.choropleth(
        df[df['year'] == selected_year],
        locations="country",           #Spalte mit den Ländernamen
        locationmode="country names",    #Plotly erkennt die Namen automatisch
        color="population",         #Wonach soll gefärbt werden
        hover_name="country",       #Was steht im Tooltip
        title=f"Globale Bevölkerungsverteilung {selected_year}",
        color_continuous_scale=px.colors.sequential.Plasma,         #Farbskala
        template='plotly_white',
        labels={'population': 'Einwohner'}
    )

    # Karte verbessern
    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=0),
        coloraxis_showscale=True        #Zeigt die Farbskala an
    )

    return fig

def create_layout(df):
    return html.Div([
        # 1. DER HEADER (Ganz oben)
        html.Div([
            html.H1("Population-Dashboard", style={'margin': '0', 'color': 'white'}),
        ], style={'backgroundColor': '#2c3e50', 'padding': '20px', 'textAlign': 'center'}),

        # 2. ZEILE 1: Filter (links) & Weltkarte (rechts)
        html.Div([
            # Linke Spalte (30% Breite)
            html.Div([
                html.Div([
                    html.Label("Land auswählen:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='country-dropdown', 
                        options=get_country_options(df), 
                        value='Germany', 
                        clearable=False
                    )
                ], style={'marginBottom': '20px'}),
                
                # Hier landet die Statistik (Einwohnerzahl + Wachstum)
                html.Div(id='latest-population-info') 
            ], style={'width': '30%'}),

            # Rechte Spalte (68% Breite) für die Weltkarte
            html.Div([
                dcc.Graph(id='world-map')
            ], style={'width': '68%'})
        ], style={
            'display': 'flex', 
            'justifyContent': 'space-between', 
            'width': '98%', 
            'margin': '20px auto'
        }),

        # 3. ZEILE 2: Das Liniendiagramm (Volle Breite unter der Karte)
        html.Div([
            dcc.Graph(id='population-graph')
        ], style={'width': '98%', 'margin': '0 auto 20px auto'}),

        # 4. ZEILE 3: Die zwei Vergleiche (Top 10 & Bottom 10)
        html.Div([
            html.Div([
                dcc.Graph(id='comparison-graph')
            ], style={'width': '49%'}),
            
            html.Div([
                dcc.Graph(id='lowest-population-graph')
            ], style={'width': '49%'})
        ], style={
            'display': 'flex', 
            'justifyContent': 'space-between', 
            'width': '98%', 
            'margin': 'auto'
        })

    ], style={
        'backgroundColor': '#f8f9fa', 
        'minHeight': '100vh', 
        'fontFamily': 'Arial'
    })

# --------- Initialisierung & Callback ------
data = load_data('population_clean.csv')
app = Dash(__name__)
app.layout = create_layout(data)

@app.callback(
    [Output('world-map', 'figure'),           # 1. Karte
     Output('population-graph', 'figure'),    # 2. Liniendiagramm
     Output('latest-population-info', 'children'), # 3. Text
     Output('comparison-graph', 'figure'),    # 4. Balkendiagramm
     Output('lowest-population-graph', 'figure')], # 5. Donut-Diagramm
    Input('country-dropdown', 'value')
)

def update_graph(selected_country):
    latest_year = data['year'].max()
    
    # 1. Funktionen aufrufen
    fig_map = create_world_map(data, latest_year)
    fig_line = create_population_chart(data, selected_country)
    fig_bar = create_comparison_chart(data, latest_year)
    fig_pie = create_lowest_population_chart(data, latest_year)
    
    # 3. Statistiken holen
    pop_text = get_latest_population(data, selected_country)
    growth_info = get_growth_rate(data, selected_country)


    info_display = html.Div([
        html.Div(pop_text, style={'fontSize': '20px', 'fontWeight': 'bold'}), 
        html.Div(growth_info)
    ])
    
    # WICHTIG: Die Reihenfolge im Return muss EXAKT wie oben bei den Outputs sein!
    return fig_map, fig_line, info_display, fig_bar, fig_pie

if __name__ == '__main__':
    app.run(debug=True)