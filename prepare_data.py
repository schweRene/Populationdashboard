import pandas as pd
import pycountry_convert as pc

def get_continent_name(iso3_code):
    manual_fixes = {
        "GRL": "Europe", "TLS": "Asia", "ARE": "Asia",
        "YEM": "Asia", "SGP": "Asia", "KOS": "Europe", 
        "ESH": "Africa", "GUF": "Amerika",
        "PAK": "Asia", "BTN": "Asia"
    }
    code = str(iso3_code).upper().strip() if pd.notna(iso3_code) else ""
    if code in manual_fixes: return manual_fixes[code]
    try:
        iso2 = pc.country_alpha3_to_country_alpha2(code)
        cont_code = pc.country_alpha2_to_continent_code(iso2)
        mapping = {'AF': 'Africa', 'AS': 'Asia', 'EU': 'Europe', 'NA': 'Amerika', 'SA': 'Amerika', 'OC': 'Oceania'}
        return mapping.get(cont_code, None)
    except:
        return None

# Original laden
df = pd.read_csv("population.csv")
df["continent"] = df["iso3"].apply(get_continent_name)
df_clean = df.dropna(subset=["continent"]).copy()

# Korrektur für Pakistan/Indien/Bhutan Lücken (Kaschmir & Co.)
years = df_clean["year"].unique()
# Wir fügen die ISO-Codes hinzu, die Plotly für die 'weißen Flecken' erwartet
missing_codes = [
    {"iso3": "ESH", "country": "Western Sahara", "continent": "Africa"},
    {"iso3": "GUF", "country": "French Guiana", "continent": "Amerika"},
    {"iso3": "KAS", "country": "Kashmir", "continent": "Asia"}
]

new_rows = []
for m in missing_codes:
    for y in years:
        new_rows.append({"iso3": m["iso3"], "country": m["country"], "year": y, "population": 0, "continent": m["continent"]})

df_final = pd.concat([df_clean, pd.DataFrame(new_rows)], ignore_index=True)
df_final.to_csv("population_continent.csv", index=False)
print("Datenvorbereitung abgeschlossen. Lücken-ISO-Codes hinzugefügt.")