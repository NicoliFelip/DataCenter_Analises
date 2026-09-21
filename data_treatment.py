"""
==========================================================================
  DATA TREATMENT SCRIPT - Data Centers & Environmental Impact Analysis
==========================================================================
  Este script carrega, limpa, padroniza e exporta todas as bases de dados
  necessárias para o dashboard de impacto ambiental de data centers.
  
  Foco: indicadores industriais/energéticos (não doméstico/agrícola).
  Saída: arquivos JSON prontos para o HTML dashboard.
==========================================================================
"""

import pandas as pd
import numpy as np
import json
import os
import warnings
warnings.filterwarnings('ignore')

# ===================================================================
# CONFIGURAÇÕES
# ===================================================================
DATA_DIR = r"C:\Users\User\Downloads"
OUTPUT_DIR = r"C:\Users\User\Documents\antigravity\lively-hypatia\data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mapeamento de nomes de países para padronização
COUNTRY_NAME_MAP = {
    # IEA / GHG names -> standard
    'United States': 'United States',
    'USA': 'United States',
    'US': 'United States',
    'United States of America': 'United States',
    'Korea': 'South Korea',
    'Republic of Korea': 'South Korea',
    "Korea, Rep.": 'South Korea',
    "Korea, Republic of": 'South Korea',
    'Czech Republic': 'Czechia',
    'Czechia': 'Czechia',
    'Slovak Republic': 'Slovakia',
    'Viet Nam': 'Vietnam',
    'Russian Federation': 'Russia',
    'Türkiye': 'Turkey',
    'Turkiye': 'Turkey',
    'Türkiye (Turkiye)': 'Turkey',
    'Iran': 'Iran',
    'Iran, Islamic Rep.': 'Iran',
    "Iran (Islamic Republic of)": 'Iran',
    'Venezuela': 'Venezuela',
    'Venezuela, RB': 'Venezuela',
    "Venezuela (Bolivarian Republic of)": 'Venezuela',
    'United Kingdom': 'United Kingdom',
    'UK': 'United Kingdom',
    'Great Britain': 'United Kingdom',
    'People\'s Republic of China': 'China',
    "China, People's Republic of": 'China',
    'Chinese Taipei': 'Taiwan',
    'Hong Kong, China': 'Hong Kong',
    "Hong Kong (China)": 'Hong Kong',
    'Bolivia': 'Bolivia',
    'Bolivia (Plurinational State of)': 'Bolivia',
    'ElSalvador': 'El Salvador',
    'El Salvador': 'El Salvador',
    'Congo': 'Congo',
    'Congo, Dem. Rep.': 'DR Congo',
    'DR Congo': 'DR Congo',
    'Egypt': 'Egypt',
    'Egypt, Arab Rep.': 'Egypt',
    'Brunei': 'Brunei',
    'Brunei Darussalam': 'Brunei',
    'Tanzania': 'Tanzania',
    'Tanzania, United Republic of': 'Tanzania',
    'Syria': 'Syria',
    'Syrian Arab Republic': 'Syria',
    'Lao PDR': 'Laos',
    "Lao People's Democratic Republic": 'Laos',
    'Laos': 'Laos',
    'Moldova': 'Moldova',
    'Moldova, Republic of': 'Moldova',
    'North Macedonia': 'North Macedonia',
    'Republic of North Macedonia': 'North Macedonia',
    'Cote d\'Ivoire': "Côte d'Ivoire",
    "Côte d'Ivoire": "Côte d'Ivoire",
}

def standardize_country(name):
    """Padroniza nome de país."""
    if pd.isna(name):
        return None
    name = str(name).strip()
    return COUNTRY_NAME_MAP.get(name, name)


def save_json(data, filename, orient='records'):
    """Salva dados como JSON."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if isinstance(data, pd.DataFrame):
        # Tratar NaN -> null
        data = data.where(pd.notnull(data), None)
        result = data.to_dict(orient=orient)
    else:
        result = data
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, default=str)
    print(f"  [OK] Salvo: {filename} ({len(result) if isinstance(result, list) else 'dict'} registros)")
    return filepath


print("=" * 70)
print("  INÍCIO DO TRATAMENTO DE DADOS")
print("=" * 70)


# ===================================================================
# 1. DATA CENTERS
# ===================================================================
print("\n[1/11] Carregando: datacenters.xlsx")
df_dc = pd.read_excel(os.path.join(DATA_DIR, "datacenters.xlsx"), sheet_name="Data Centers")
df_dc['Country'] = df_dc['Country'].apply(standardize_country)
df_dc = df_dc.dropna(subset=['Country'])

# Contagem por país
dc_by_country = df_dc.groupby('Country').agg(
    dc_count=('Name', 'count'),
    companies=('Company', 'nunique'),
    cities=('City', 'nunique')
).reset_index()

# Contagem por cidade
dc_by_city = df_dc.groupby(['Country', 'City']).agg(
    dc_count=('Name', 'count'),
    lat=('Latitude', 'mean'),
    lon=('Longitude', 'mean')
).reset_index()

# Detalhes individuais
dc_details = df_dc[['Name', 'Company', 'City', 'State', 'Country', 'Latitude', 'Longitude']].copy()

save_json(dc_by_country, "dc_by_country.json")
save_json(dc_by_city, "dc_by_city.json")
save_json(dc_details, "dc_details.json")

print(f"  Total DCs: {len(df_dc)}, Países: {dc_by_country['Country'].nunique()}")


# ===================================================================
# 2. QUALIDADE DO AR (WHO)
# ===================================================================
print("\n[2/11] Carregando: WHO Air Quality")
df_air = pd.read_excel(
    os.path.join(DATA_DIR, "who_ambient_air_quality_database_version_2024_(v6.1).xlsx"),
    sheet_name="Update 2024 (V6.1)"
)
df_air['country_name'] = df_air['country_name'].apply(standardize_country)
df_air = df_air.dropna(subset=['country_name'])

# Média por país e ano (indicadores de ar: PM10, PM2.5, NO2)
air_by_country_year = df_air.groupby(['country_name', 'year', 'iso3']).agg(
    pm10_mean=('pm10_concentration', 'mean'),
    pm25_mean=('pm25_concentration', 'mean'),
    no2_mean=('no2_concentration', 'mean'),
    n_stations=('city', 'count')
).reset_index()

# Último ano disponível por país
air_latest = air_by_country_year.sort_values('year').groupby('country_name').last().reset_index()

# Dados por cidade com coordenadas (para mapas)
air_by_city = df_air[['country_name', 'iso3', 'city', 'year',
                       'pm10_concentration', 'pm25_concentration', 'no2_concentration',
                       'latitude', 'longitude', 'population', 'type_of_stations']].copy()

save_json(air_by_country_year, "air_by_country_year.json")
save_json(air_latest, "air_latest.json")
save_json(air_by_city, "air_by_city.json")

print(f"  Registros: {len(df_air)}, Países: {df_air['country_name'].nunique()}")


# ===================================================================
# 3. EMISSÕES DE CO₂ (Our World in Data)
# ===================================================================
print("\n[3/11] Carregando: annual-co2-emissions.csv")
df_co2 = pd.read_csv(os.path.join(DATA_DIR, "annual-co2-emissions.csv"))
df_co2.columns = ['entity', 'code', 'year', 'annual_co2_emissions']
df_co2['entity'] = df_co2['entity'].apply(standardize_country)
df_co2 = df_co2.dropna(subset=['entity', 'code'])

# Filtrar apenas países (excluir continentes/regiões - sem código ISO)
df_co2 = df_co2[df_co2['code'].str.len() == 3]

# Converter para milhões de toneladas
df_co2['co2_mt'] = df_co2['annual_co2_emissions'] / 1_000_000

save_json(df_co2[['entity', 'code', 'year', 'co2_mt']], "co2_annual.json")
print(f"  Registros: {len(df_co2)}, Países: {df_co2['entity'].nunique()}")


# ===================================================================
# 4. ESTRESSE HÍDRICO (Aqueduct 4.0 Rankings)
# ===================================================================
print("\n[4/11] Carregando: Aqueduct40 Rankings")

# 4a. Country baseline
df_aq_country_base = pd.read_excel(
    os.path.join(DATA_DIR, "Aqueduct40_rankings_download_Y2023M07D05.xlsx"),
    sheet_name="country_baseline"
)
df_aq_country_base['name_0'] = df_aq_country_base['name_0'].apply(standardize_country)

# Filtrar indicadores industriais e gerais relevantes
water_indicators = [
    'bws', 'bwd', 'iav', 'sev', 'gtd', 'rfr', 'cfr', 'drr', 'ucw', 'cep', 'udw',
    'usa', 'rri', 'smc',  # water stress, depletion, variability, seasonal, groundwater
    'w_awr_bws_tot_cat', 'w_awr_bwd_tot_cat',  # overall water risk
]

# Pivotear: um registro por país com todos indicadores
aq_baseline_pivot = df_aq_country_base.pivot_table(
    index=['gid_0', 'name_0'],
    columns='indicator_name',
    values='score',
    aggfunc='first'
).reset_index()
aq_baseline_pivot.columns.name = None

save_json(df_aq_country_base, "water_stress_country_baseline.json")
save_json(aq_baseline_pivot, "water_stress_country_pivot.json")

# 4b. Country future
df_aq_country_future = pd.read_excel(
    os.path.join(DATA_DIR, "Aqueduct40_rankings_download_Y2023M07D05.xlsx"),
    sheet_name="country_future"
)
df_aq_country_future['name_0'] = df_aq_country_future['name_0'].apply(standardize_country)

save_json(df_aq_country_future, "water_stress_country_future.json")

# 4c. Province baseline (para mapas mais detalhados)
df_aq_prov = pd.read_excel(
    os.path.join(DATA_DIR, "Aqueduct40_rankings_download_Y2023M07D05.xlsx"),
    sheet_name="province_baseline"
)
df_aq_prov['name_0'] = df_aq_prov['name_0'].apply(standardize_country)

# Agregar por país (média das províncias, ponderada pelo score)
# Manter os dados completos para visualização detalhada
save_json(df_aq_prov, "water_stress_province_baseline.json")

print(f"  Country baseline: {len(df_aq_country_base)} registros")
print(f"  Country future: {len(df_aq_country_future)} registros")
print(f"  Province baseline: {len(df_aq_prov)} registros")


# ===================================================================
# 5. PROJEÇÕES DE ESTRESSE HÍDRICO (Aqueduct Country Rankings)
# ===================================================================
print("\n[5/11] Carregando: Aqueduct Water Stress Projections")
ws_file = os.path.join(DATA_DIR, "aqueduct-water-stress-country-rankings-data-set (4).xlsx")

sheets_water_proj = {
    '2020 BAU': (2020, 'BAU'),
    '2020 optimistic': (2020, 'Optimistic'),
    '2020 pessimistic': (2020, 'Pessimistic'),
    '2030 BAU': (2030, 'BAU'),
    '2030 optimistic': (2030, 'Optimistic'),
    '2030 pessimistic': (2030, 'Pessimistic'),
    '2040 BAU': (2040, 'BAU'),
    '2040 optimistic': (2040, 'Optimistic'),
    '2040 pessimistic': (2040, 'Pessimistic'),
}

water_proj_all = []
for sheet_name, (year, scenario) in sheets_water_proj.items():
    try:
        df_ws = pd.read_excel(ws_file, sheet_name=sheet_name)
        # Colunas: Rank, Name, All Sectors, Industrial, Domestic, Agricultural
        df_ws = df_ws.dropna(subset=['Name'])
        df_ws['year'] = year
        df_ws['scenario'] = scenario
        df_ws['Name'] = df_ws['Name'].apply(standardize_country)
        water_proj_all.append(df_ws)
    except Exception as e:
        print(f"  ⚠ Erro ao ler planilha '{sheet_name}': {e}")

df_water_proj = pd.concat(water_proj_all, ignore_index=True)
# Foco industrial: manter todas as colunas para filtro no dashboard
df_water_proj.columns = ['rank', 'country', 'all_sectors', 'industrial', 'domestic', 'agricultural', 'year', 'scenario']

save_json(df_water_proj, "water_stress_projections.json")
print(f"  Total registros: {len(df_water_proj)}")


# ===================================================================
# 6. AQUASTAT - Recursos e uso da água
# ===================================================================
print("\n[6/11] Carregando: AQUASTAT")
df_aquastat = pd.read_excel(
    os.path.join(DATA_DIR, "AQUASTAT Dissemination System.xlsx"),
    sheet_name="Data"
)
df_aquastat['Area'] = df_aquastat['Area'].apply(standardize_country)
df_aquastat = df_aquastat.dropna(subset=['Area', 'Value'])

# Filtrar variáveis industriais/relevantes
industrial_keywords = [
    'industrial', 'industry', 'total water withdrawal',
    'renewable', 'water resources', 'desalination',
    'municipal', 'dam', 'freshwater', 'dependency',
    'water stress', 'water use efficiency',
]

def is_relevant_variable(var):
    if pd.isna(var):
        return False
    var_lower = str(var).lower()
    return any(kw in var_lower for kw in industrial_keywords)

# Manter todas as variáveis mas marcar as industriais
df_aquastat['is_industrial'] = df_aquastat['Variable'].apply(is_relevant_variable)

# Filtrar para variáveis relevantes
df_aquastat_filtered = df_aquastat[df_aquastat['is_industrial']].copy()

# Tabela pivoteada por país/ano/variável
aquastat_summary = df_aquastat_filtered.groupby(['Area', 'Year', 'Variable']).agg(
    value=('Value', 'mean'),
    unit=('Unit', 'first')
).reset_index()

save_json(aquastat_summary, "aquastat_industrial.json")
save_json(df_aquastat[['Area', 'Year', 'VariableGroup', 'Variable', 'Value', 'Unit']], "aquastat_all.json")

# Lista de variáveis disponíveis (para filtros)
var_list = df_aquastat_filtered[['VariableGroup', 'Variable', 'Unit']].drop_duplicates().to_dict('records')
save_json(var_list, "aquastat_variables.json")

print(f"  Total: {len(df_aquastat)}, Industrial: {len(df_aquastat_filtered)}")
print(f"  Variáveis industriais: {df_aquastat_filtered['Variable'].nunique()}")


# ===================================================================
# 7. SUBSÍDIOS A COMBUSTÍVEIS FÓSSEIS (IEA)
# ===================================================================
print("\n[7/11] Carregando: Subsidies 2010-2024")

# 7a. Subsídios por país e produto
df_sub_raw = pd.read_excel(
    os.path.join(DATA_DIR, "Subsidies 2010-2024.xlsx"),
    sheet_name="Subsidies by country",
    header=None,
    skiprows=4
)

# Encontrar onde começa a tabela por país (após os totais globais)
# Os dados por país começam após a linha "Country / Product"
start_idx = None
for i, row in df_sub_raw.iterrows():
    if str(row.iloc[0]).strip() == 'Country':
        start_idx = i + 1
        break

if start_idx:
    years = list(range(2010, 2025))
    df_sub = df_sub_raw.iloc[start_idx:].copy()
    df_sub.columns = ['country', 'product'] + years
    df_sub = df_sub.dropna(subset=['country'])
    df_sub['country'] = df_sub['country'].apply(standardize_country)
    
    # Melt para formato longo
    df_sub_long = df_sub.melt(
        id_vars=['country', 'product'],
        value_vars=years,
        var_name='year',
        value_name='subsidy_musd'
    )
    df_sub_long = df_sub_long.dropna(subset=['subsidy_musd'])
    df_sub_long['year'] = df_sub_long['year'].astype(int)
    
    # Totais globais (primeiras linhas)
    global_totals = df_sub_raw.iloc[1:6].copy()
    global_totals.columns = ['category', 'product'] + years
    global_totals_long = global_totals.melt(
        id_vars=['category', 'product'],
        value_vars=years,
        var_name='year',
        value_name='subsidy_musd'
    )
    
    save_json(df_sub_long, "subsidies_by_country.json")
    save_json(global_totals_long, "subsidies_global_totals.json")
    print(f"  Subsídios por país: {len(df_sub_long)} registros, {df_sub_long['country'].nunique()} países")

# 7b. Indicadores por país
df_sub_ind = pd.read_excel(
    os.path.join(DATA_DIR, "Subsidies 2010-2024.xlsx"),
    sheet_name="Indicators by country",
    header=None,
    skiprows=3
)
df_sub_ind.columns = ['country', 'avg_subsidisation_rate_pct', 'subsidy_per_capita_usd', 'subsidy_share_gdp_pct']
df_sub_ind = df_sub_ind.dropna(subset=['country'])
df_sub_ind['country'] = df_sub_ind['country'].apply(standardize_country)

save_json(df_sub_ind, "subsidies_indicators.json")
print(f"  Indicadores: {len(df_sub_ind)} países")

# 7c. Subsídios de transporte de petróleo
df_transport = pd.read_excel(
    os.path.join(DATA_DIR, "Subsidies 2010-2024.xlsx"),
    sheet_name="Transport Oil Subsidies",
    header=None,
    skiprows=4
)
years_t = list(range(2010, 2025))
df_transport.columns = ['country'] + years_t
df_transport = df_transport.dropna(subset=['country'])
# Remover "World" que é o total
df_transport_countries = df_transport[df_transport['country'] != 'World'].copy()
df_transport_countries['country'] = df_transport_countries['country'].apply(standardize_country)

df_transport_long = df_transport_countries.melt(
    id_vars=['country'],
    value_vars=years_t,
    var_name='year',
    value_name='transport_oil_subsidy_musd'
)
df_transport_long['year'] = df_transport_long['year'].astype(int)

save_json(df_transport_long, "subsidies_transport_oil.json")


# ===================================================================
# 8. IEA ENERGY VALUE ADDED
# ===================================================================
print("\n[8/11] Carregando: IEA Energy Value Added")

# 8a. VA Section Data (estrutura econômica por país, setor ISIC, ano)
df_va = pd.read_excel(
    os.path.join(DATA_DIR, "IEA_Energy_ValueAdded.xlsx"),
    sheet_name="VA section data"
)
df_va['Country'] = df_va['Country'].apply(standardize_country)
df_va = df_va.dropna(subset=['Country', 'Value USD (Million USD)'])

# Manter dados em USD para comparabilidade
va_data = df_va[['Country ISO3', 'Country', 'Year', 'ISIC Section', 'ISIC Division',
                  'ISIC Division Desc', 'Measure', 'Value USD (Million USD)']].copy()
va_data.columns = ['iso3', 'country', 'year', 'isic_section', 'isic_division',
                    'isic_desc', 'measure', 'value_usd_m']

save_json(va_data, "iea_value_added.json")

# 8b. Manufacturing Data
df_manuf = pd.read_excel(
    os.path.join(DATA_DIR, "IEA_Energy_ValueAdded.xlsx"),
    sheet_name="Manufacturing data"
)
df_manuf['Country'] = df_manuf['Country'].apply(standardize_country)
df_manuf = df_manuf.dropna(subset=['Country', 'Value USD (million USD)'])

manuf_data = df_manuf[['Country ISO3', 'Country', 'Year', 'ISIC Division',
                        'ISIC Division Desc', 'Measure', 'Value USD (million USD)']].copy()
manuf_data.columns = ['iso3', 'country', 'year', 'isic_division',
                       'isic_desc', 'measure', 'value_usd_m']

save_json(manuf_data, "iea_manufacturing.json")

# 8c. Indicators Data (intensidade energética por valor adicionado)
df_indicators = pd.read_excel(
    os.path.join(DATA_DIR, "IEA_Energy_ValueAdded.xlsx"),
    sheet_name="Indicators data"
)
df_indicators['Country'] = df_indicators['Country'].apply(standardize_country)
df_indicators = df_indicators.dropna(subset=['Country', 'Value'])

indicators_data = df_indicators[['Country ISO3', 'Country', 'Year',
                                  'ISIC Division', 'ISIC division description',
                                  'Indicator', 'Value', 'Unit']].copy()
indicators_data.columns = ['iso3', 'country', 'year', 'isic_division',
                            'isic_desc', 'indicator', 'value', 'unit']

save_json(indicators_data, "iea_indicators.json")
print(f"  VA: {len(va_data)}, Manufacturing: {len(manuf_data)}, Indicators: {len(indicators_data)}")


# ===================================================================
# 9. DATA ANNEX - ENERGY AND AI (Infraestrutura de Data Centers)
# ===================================================================
print("\n[9/11] Carregando: Data Annex Energy and AI")

# 9a. World Data - estrutura complexa, precisa tratamento especial
df_world_raw = pd.read_excel(
    os.path.join(DATA_DIR, "Data_annex_Energy_and_AI.xlsx"),
    sheet_name="World Data",
    header=None
)

# Extrair cenários das linhas 1-2
scenarios_row = df_world_raw.iloc[1].tolist()
years_row = df_world_raw.iloc[2].tolist()

# Mapear colunas para cenário+ano
col_mapping = {}
current_scenario = 'Historical'
for idx in range(3, len(years_row)):
    if pd.notna(scenarios_row[idx]):
        current_scenario = str(scenarios_row[idx]).strip()
    if pd.notna(years_row[idx]):
        year_val = str(years_row[idx]).replace('*', '').strip()
        col_mapping[idx] = (current_scenario, year_val)

# Extrair dados
world_data_records = []
current_category = None

for i in range(3, len(df_world_raw)):
    indicator = df_world_raw.iloc[i, 2]
    if pd.isna(indicator):
        continue
    indicator = str(indicator).strip()
    
    # Detectar categorias (sem dados numéricos)
    has_data = False
    for col_idx in col_mapping:
        if pd.notna(df_world_raw.iloc[i, col_idx]):
            has_data = True
            break
    
    if not has_data:
        current_category = indicator
        continue
    
    for col_idx, (scenario, year) in col_mapping.items():
        val = df_world_raw.iloc[i, col_idx]
        if pd.notna(val):
            world_data_records.append({
                'category': current_category,
                'indicator': indicator,
                'scenario': scenario,
                'year': year,
                'value': float(val) if not isinstance(val, str) else val
            })

df_world_data = pd.DataFrame(world_data_records)
save_json(df_world_data, "dc_energy_world.json")

# 9b. Regional Data
df_reg_raw = pd.read_excel(
    os.path.join(DATA_DIR, "Data_annex_Energy_and_AI.xlsx"),
    sheet_name="Regional Data",
    header=None
)

# Regional: col 1=região, cols 2-4=2020/2023/2024, col 6=Base Case 2030
reg_records = []
current_category = None
for i in range(4, len(df_reg_raw)):
    region = df_reg_raw.iloc[i, 1]
    if pd.isna(region):
        continue
    region = str(region).strip()
    
    # Detectar categorias
    has_data = any(pd.notna(df_reg_raw.iloc[i, c]) and df_reg_raw.iloc[i, c] != 0 
                   for c in [2, 3, 4, 6])
    
    if not has_data and region not in ['World']:
        current_category = region
        continue
    
    for col_idx, year in [(2, '2020'), (3, '2023'), (4, '2024'), (6, '2030')]:
        val = df_reg_raw.iloc[i, col_idx]
        if pd.notna(val):
            reg_records.append({
                'category': current_category,
                'region': region,
                'year': year,
                'scenario': 'Base Case' if year == '2030' else 'Historical',
                'value': float(val)
            })

df_reg_data = pd.DataFrame(reg_records)
save_json(df_reg_data, "dc_energy_regional.json")

print(f"  World data: {len(df_world_data)} registros")
print(f"  Regional data: {len(df_reg_data)} registros")


# ===================================================================
# 10. RDDPRIVATE - Pesquisa, Desenvolvimento e Demonstração em Energia
# ===================================================================
print("\n[10/11] Carregando: RDDPRIVATE.csv")
df_rdd = pd.read_csv(os.path.join(DATA_DIR, "RDDPRIVATE.csv"))

# Usar colunas mais relevantes
rdd_cols = {
    'COUNTRY': 'country_code',
    'Country/Region': 'country',
    'RDD_SECTOR': 'sector_code',
    'Sector': 'sector',
    'RDD_TYPE': 'type_code',
    'Type': 'type',
    'RDD_TECH': 'tech_code',
    'Technology': 'technology',
    'UNIT': 'unit_code',
    'Unit': 'unit',
    'TIME_PERIOD': 'year',
    'OBS_VALUE': 'value',
}
df_rdd = df_rdd.rename(columns=rdd_cols)
df_rdd = df_rdd[list(rdd_cols.values())]
df_rdd['country'] = df_rdd['country'].apply(standardize_country)
df_rdd = df_rdd.dropna(subset=['country', 'value'])

save_json(df_rdd, "rdd_energy.json")

# Lista de setores e tecnologias (para filtros)
rdd_sectors = df_rdd[['sector_code', 'sector']].drop_duplicates().to_dict('records')
rdd_techs = df_rdd[['tech_code', 'technology']].drop_duplicates().to_dict('records')
save_json({'sectors': rdd_sectors, 'technologies': rdd_techs}, "rdd_filters.json")

print(f"  Registros: {len(df_rdd)}, Países: {df_rdd['country'].nunique()}")


# ===================================================================
# 11. IEA GHG HIGHLIGHTS 2026
# ===================================================================
print("\n[11/11] Carregando: IEA GHG Highlights 2026")

ghg_file = os.path.join(DATA_DIR, "IEA_GHG_highlights_2026.xlsx")

# Definir planilhas com séries temporais (mesma estrutura: região/país, anos 1971-2024)
time_series_sheets = {
    'GHG Energy': {'unit': 'MtCO2eq', 'desc': 'GHG emissions from energy'},
    'GHG FC': {'unit': 'MtCO2eq', 'desc': 'GHG from fuel combustion'},
    'GHG FC - Coal': {'unit': 'MtCO2eq', 'desc': 'GHG from coal combustion'},
    'GHG FC - Oil': {'unit': 'MtCO2eq', 'desc': 'GHG from oil combustion'},
    'GHG FC - Gas': {'unit': 'MtCO2eq', 'desc': 'GHG from gas combustion'},
    'CO2-TES': {'unit': 'tCO2/TJ', 'desc': 'CO2 intensity per energy supply'},
    'CO2-GDP': {'unit': 'kgCO2/USD2020', 'desc': 'CO2 intensity per GDP (exchange rate)'},
    'CO2-GDP PPP': {'unit': 'kgCO2/USD2020 PPP', 'desc': 'CO2 intensity per GDP (PPP)'},
    'CO2-POP': {'unit': 'tCO2/capita', 'desc': 'CO2 per capita'},
}

# Regiões a excluir (pegar apenas países individuais)
REGIONS_TO_EXCLUDE = {
    'World', 'OECD Total', 'Non-OECD Total', 'OECD Americas', 'OECD Asia Oceania',
    'OECD Europe', 'Annex I Parties', 'Non-Annex I Parties', 'Annex B Kyoto Parties',
    'Annex II Parties', 'Annex I EIT', 'North America', 'Europe', 'Asia Oceania',
    'Region/Country/Economy', 'million tonnes of CO2 eq', 'million tonnes of CO2',
    'tonnes CO2 / capita', 'kgCO2 / USD', 'tonnes CO2 / TJ',
    'G7', 'G20', 'OPEC', 'IEA', 'Africa (UN)', 'Americas (UN)', 'Asia (UN)',
    'Europe (UN)', 'Oceania (UN)',
}

all_ghg_ts = []

for sheet_name, meta in time_series_sheets.items():
    try:
        df_sheet = pd.read_excel(ghg_file, sheet_name=sheet_name, header=None, skiprows=3)
        
        # Primeira coluna = país, restante = anos 1971-2024
        years = [int(y) for y in df_sheet.iloc[0, 1:].tolist() if pd.notna(y)]
        
        for i in range(1, len(df_sheet)):
            country = df_sheet.iloc[i, 0]
            if pd.isna(country):
                continue
            country = str(country).strip()
            
            # Excluir regiões/agregados
            if country in REGIONS_TO_EXCLUDE:
                continue
            # Excluir linhas com identação excessiva (regiões)
            if country != country.lstrip():
                # Verificar se é uma sub-região
                clean_name = country.strip()
                if clean_name in REGIONS_TO_EXCLUDE:
                    continue
            
            country_std = standardize_country(country.strip())
            
            for j, year in enumerate(years):
                val = df_sheet.iloc[i, j + 1]
                if pd.notna(val) and str(val).strip() != '..':
                    try:
                        all_ghg_ts.append({
                            'country': country_std,
                            'year': year,
                            'indicator': sheet_name,
                            'unit': meta['unit'],
                            'description': meta['desc'],
                            'value': float(val)
                        })
                    except (ValueError, TypeError):
                        pass
    except Exception as e:
        print(f"  ⚠ Erro ao processar {sheet_name}: {e}")

df_ghg_ts = pd.DataFrame(all_ghg_ts)
save_json(df_ghg_ts, "ghg_timeseries.json")

# SECTOR - dados setoriais (ano 2024)
try:
    df_sector = pd.read_excel(ghg_file, sheet_name='SECTOR', header=None, skiprows=3)
    sector_cols = ['country', 'total_co2', 'electricity_heat', 'other_energy',
                   'manufacturing', 'transport', 'road_transport', 'residential', 'commercial']
    df_sector.columns = sector_cols + [f'extra_{i}' for i in range(len(df_sector.columns) - len(sector_cols))]
    df_sector = df_sector[sector_cols].copy()
    
    # Limpar e filtrar
    sector_data = []
    for _, row in df_sector.iterrows():
        c = row['country']
        if pd.isna(c):
            continue
        c = str(c).strip()
        if c in REGIONS_TO_EXCLUDE or c != c.lstrip():
            clean = c.strip()
            if clean in REGIONS_TO_EXCLUDE:
                continue
        country_std = standardize_country(c.strip())
        row_dict = row.to_dict()
        row_dict['country'] = country_std
        
        # Converter valores
        for col in sector_cols[1:]:
            try:
                row_dict[col] = float(row_dict[col]) if pd.notna(row_dict[col]) and str(row_dict[col]).strip() != '..' else None
            except (ValueError, TypeError):
                row_dict[col] = None
        sector_data.append(row_dict)
    
    df_sector_clean = pd.DataFrame(sector_data)
    df_sector_clean = df_sector_clean.drop_duplicates(subset=['country'], keep='first')
    save_json(df_sector_clean, "ghg_sector_2024.json")
    print(f"  Setorial: {len(df_sector_clean)} países")
except Exception as e:
    print(f"  ⚠ Erro ao processar SECTOR: {e}")

# KAYA decomposition
try:
    df_kaya = pd.read_excel(ghg_file, sheet_name='KAYA', header=None, skiprows=3)
    
    # Kaya: col0 = country (only filled for first indicator), col1 = indicator, cols 2+ = years
    years_kaya = [int(y) for y in df_kaya.iloc[0, 2:].tolist() if pd.notna(y)]
    
    kaya_records = []
    current_country = None
    for i in range(1, len(df_kaya)):
        if pd.notna(df_kaya.iloc[i, 0]):
            candidate = str(df_kaya.iloc[i, 0]).strip()
            if candidate not in REGIONS_TO_EXCLUDE:
                current_country = standardize_country(candidate)
            elif candidate.strip() in REGIONS_TO_EXCLUDE:
                current_country = None
                continue
        
        if current_country is None:
            continue
            
        indicator = df_kaya.iloc[i, 1]
        if pd.isna(indicator):
            continue
        indicator = str(indicator).strip()
        
        for j, year in enumerate(years_kaya):
            val = df_kaya.iloc[i, j + 2]
            if pd.notna(val) and str(val).strip() != '..':
                try:
                    kaya_records.append({
                        'country': current_country,
                        'indicator': indicator,
                        'year': year,
                        'value': float(val)
                    })
                except (ValueError, TypeError):
                    pass
    
    df_kaya_clean = pd.DataFrame(kaya_records)
    save_json(df_kaya_clean, "ghg_kaya.json")
    print(f"  Kaya: {len(df_kaya_clean)} registros")
except Exception as e:
    print(f"  ⚠ Erro ao processar KAYA: {e}")

print(f"  GHG time series: {len(df_ghg_ts)} registros, {df_ghg_ts['country'].nunique()} países")


# ===================================================================
# 12. CRUZAMENTOS PRINCIPAIS (DATASETS COMBINADOS)
# ===================================================================
print("\n" + "=" * 70)
print("  CRIANDO DATASETS COMBINADOS")
print("=" * 70)

# 12a. DC + Air Quality (por país)
print("\n[Cruzamento 1] Data Centers × Qualidade do Ar")
dc_air = dc_by_country.merge(air_latest, left_on='Country', right_on='country_name', how='inner')
dc_air = dc_air.drop(columns=['country_name'], errors='ignore')
save_json(dc_air, "cross_dc_air.json")
print(f"  Matches: {len(dc_air)} países")

# 12b. DC + Water Stress (por país)
print("\n[Cruzamento 2] Data Centers × Estresse Hídrico")
# Pegar água estresse baseline - indicador bws (baseline water stress)
ws_bws = df_aq_country_base[df_aq_country_base['indicator_name'] == 'bws'][
    ['name_0', 'score', 'score_ranked', 'cat', 'label']
].copy()
ws_bws.columns = ['country', 'water_stress_score', 'water_stress_rank', 'water_stress_cat', 'water_stress_label']
ws_bws = ws_bws.drop_duplicates(subset=['country'], keep='first')

dc_water = dc_by_country.merge(ws_bws, left_on='Country', right_on='country', how='inner')
dc_water = dc_water.drop(columns=['country'], errors='ignore')
save_json(dc_water, "cross_dc_water.json")
print(f"  Matches: {len(dc_water)} países")

# 12c. DC + CO2 (por país, último ano disponível)
print("\n[Cruzamento 3] Data Centers × CO₂")
co2_latest = df_co2.sort_values('year').groupby('entity').last().reset_index()
co2_latest = co2_latest.drop_duplicates(subset=['entity'], keep='first')
dc_co2 = dc_by_country.merge(co2_latest[['entity', 'year', 'co2_mt']],
                               left_on='Country', right_on='entity', how='inner')
dc_co2 = dc_co2.drop(columns=['entity'], errors='ignore')
dc_co2 = dc_co2.rename(columns={'year': 'co2_year'})
save_json(dc_co2, "cross_dc_co2.json")
print(f"  Matches: {len(dc_co2)} países")

# 12d. DC + GHG Setorial (indústria vs energia vs transporte)
print("\n[Cruzamento 4] Data Centers × Emissões Setoriais")
if 'df_sector_clean' in dir():
    dc_ghg_sector = dc_by_country.merge(df_sector_clean,
                                         left_on='Country', right_on='country', how='inner')
    dc_ghg_sector = dc_ghg_sector.drop(columns=['country'], errors='ignore')
    save_json(dc_ghg_sector, "cross_dc_ghg_sector.json")
    print(f"  Matches: {len(dc_ghg_sector)} países")

# 12e. DC + Subsídios (por país)
print("\n[Cruzamento 5] Data Centers × Subsídios")
dc_subsidies = dc_by_country.merge(df_sub_ind,
                                    left_on='Country', right_on='country', how='inner')
dc_subsidies = dc_subsidies.drop(columns=['country'], errors='ignore')
save_json(dc_subsidies, "cross_dc_subsidies.json")
print(f"  Matches: {len(dc_subsidies)} países")

# 12f. DC + CO2 per capita + CO2/GDP (últimos dados)
print("\n[Cruzamento 6] Data Centers × CO₂ per capita + CO₂/GDP")
co2_pop_latest = df_ghg_ts[df_ghg_ts['indicator'] == 'CO2-POP'].sort_values('year').groupby('country').last().reset_index()
co2_gdp_latest = df_ghg_ts[df_ghg_ts['indicator'] == 'CO2-GDP'].sort_values('year').groupby('country').last().reset_index()
co2_tes_latest = df_ghg_ts[df_ghg_ts['indicator'] == 'CO2-TES'].sort_values('year').groupby('country').last().reset_index()

dc_intensities = dc_by_country.copy()
dc_intensities = dc_intensities.merge(
    co2_pop_latest[['country', 'value']].rename(columns={'value': 'co2_per_capita'}),
    left_on='Country', right_on='country', how='left'
).drop(columns=['country'], errors='ignore')
dc_intensities = dc_intensities.merge(
    co2_gdp_latest[['country', 'value']].rename(columns={'value': 'co2_per_gdp'}),
    left_on='Country', right_on='country', how='left'
).drop(columns=['country'], errors='ignore')
dc_intensities = dc_intensities.merge(
    co2_tes_latest[['country', 'value']].rename(columns={'value': 'co2_per_tes'}),
    left_on='Country', right_on='country', how='left'
).drop(columns=['country'], errors='ignore')

save_json(dc_intensities, "cross_dc_intensities.json")
print(f"  Total: {len(dc_intensities)} países")

# 12g. DC + GHG por tipo de combustível (carvão, petróleo, gás)
print("\n[Cruzamento 7] Data Centers × Emissões por Combustível")
fuel_latest = {}
for fuel_sheet in ['GHG FC - Coal', 'GHG FC - Oil', 'GHG FC - Gas']:
    fuel_df = df_ghg_ts[df_ghg_ts['indicator'] == fuel_sheet].sort_values('year').groupby('country').last().reset_index()
    fuel_name = fuel_sheet.split(' - ')[1].lower()
    fuel_latest[fuel_name] = fuel_df[['country', 'value']].rename(columns={'value': f'ghg_{fuel_name}_mt'})

dc_fuels = dc_by_country.copy()
for fuel_name, fuel_df in fuel_latest.items():
    dc_fuels = dc_fuels.merge(fuel_df, left_on='Country', right_on='country', how='left')
    dc_fuels = dc_fuels.drop(columns=['country'], errors='ignore')

save_json(dc_fuels, "cross_dc_fuels.json")
print(f"  Total: {len(dc_fuels)} países")

# 12h. MEGA DATASET - tudo junto por país (para análise integrada)
print("\n[Cruzamento 8] Dataset Integrado (mega)")
mega = dc_by_country.copy()

# + Air Quality
mega = mega.merge(air_latest[['country_name', 'pm10_mean', 'pm25_mean', 'no2_mean']],
                   left_on='Country', right_on='country_name', how='left')
mega = mega.drop(columns=['country_name'], errors='ignore')

# + Water Stress
mega = mega.merge(ws_bws, left_on='Country', right_on='country', how='left')
mega = mega.drop(columns=['country'], errors='ignore')

# + CO2
mega = mega.merge(co2_latest[['entity', 'co2_mt']],
                   left_on='Country', right_on='entity', how='left')
mega = mega.drop(columns=['entity'], errors='ignore')

# + CO2 per capita, CO2/GDP, CO2/TES
mega = mega.merge(
    co2_pop_latest[['country', 'value']].rename(columns={'value': 'co2_per_capita'}),
    left_on='Country', right_on='country', how='left'
).drop(columns=['country'], errors='ignore')
mega = mega.merge(
    co2_gdp_latest[['country', 'value']].rename(columns={'value': 'co2_per_gdp'}),
    left_on='Country', right_on='country', how='left'
).drop(columns=['country'], errors='ignore')

# + GHG por combustível
for fuel_name, fuel_df in fuel_latest.items():
    mega = mega.merge(fuel_df, left_on='Country', right_on='country', how='left')
    mega = mega.drop(columns=['country'], errors='ignore')

# + Subsídios
mega = mega.merge(df_sub_ind[['country', 'subsidy_per_capita_usd', 'subsidy_share_gdp_pct']],
                   left_on='Country', right_on='country', how='left')
mega = mega.drop(columns=['country'], errors='ignore')

# + GHG setorial (energia elétrica, manufacturing)
if 'df_sector_clean' in dir():
    mega = mega.merge(
        df_sector_clean[['country', 'total_co2', 'electricity_heat', 'manufacturing', 'transport']],
        left_on='Country', right_on='country', how='left'
    )
    mega = mega.drop(columns=['country'], errors='ignore')

save_json(mega, "mega_dataset.json")
print(f"  Mega dataset: {len(mega)} países, {len(mega.columns)} colunas")


# ===================================================================
# 13. METADADOS PARA O DASHBOARD
# ===================================================================
print("\n" + "=" * 70)
print("  CRIANDO METADADOS")
print("=" * 70)

metadata = {
    'databases': [
        {
            'id': 'datacenters',
            'name': 'Data Centers Database',
            'file': 'datacenters.xlsx',
            'description': 'Localização e informações de 367 data centers globais',
            'records': int(len(df_dc)),
            'countries': int(dc_by_country['Country'].nunique()),
            'outputs': ['dc_by_country.json', 'dc_by_city.json', 'dc_details.json']
        },
        {
            'id': 'who_air',
            'name': 'WHO Ambient Air Quality Database v2024',
            'file': 'who_ambient_air_quality_database_version_2024_(v6.1).xlsx',
            'description': 'Qualidade do ar por cidade e país: PM10, PM2.5, NO₂',
            'records': int(len(df_air)),
            'indicators': ['PM10', 'PM2.5', 'NO₂'],
            'outputs': ['air_by_country_year.json', 'air_latest.json', 'air_by_city.json']
        },
        {
            'id': 'co2_owid',
            'name': 'Annual CO₂ Emissions (Our World in Data)',
            'file': 'annual-co2-emissions.csv',
            'description': 'Emissões anuais de CO₂ por país, série histórica',
            'records': int(len(df_co2)),
            'outputs': ['co2_annual.json']
        },
        {
            'id': 'aqueduct40',
            'name': 'Aqueduct 4.0 Water Risk Rankings',
            'file': 'Aqueduct40_rankings_download_Y2023M07D05.xlsx',
            'description': 'Estresse e riscos hídricos por país e província',
            'outputs': ['water_stress_country_baseline.json', 'water_stress_country_future.json', 'water_stress_province_baseline.json', 'water_stress_country_pivot.json']
        },
        {
            'id': 'aqueduct_proj',
            'name': 'Aqueduct Water Stress Projections',
            'file': 'aqueduct-water-stress-country-rankings-data-set (4).xlsx',
            'description': 'Projeções de estresse hídrico para 2020/2030/2040, cenários BAU/otimista/pessimista',
            'outputs': ['water_stress_projections.json']
        },
        {
            'id': 'aquastat',
            'name': 'AQUASTAT (FAO)',
            'file': 'AQUASTAT Dissemination System.xlsx',
            'description': 'Recursos e uso da água por país e ano (variáveis industriais)',
            'outputs': ['aquastat_industrial.json', 'aquastat_all.json', 'aquastat_variables.json']
        },
        {
            'id': 'subsidies',
            'name': 'IEA Fossil Fuel Subsidies 2010-2024',
            'file': 'Subsidies 2010-2024.xlsx',
            'description': 'Subsídios a combustíveis fósseis por país, produto e ano',
            'outputs': ['subsidies_by_country.json', 'subsidies_indicators.json', 'subsidies_transport_oil.json', 'subsidies_global_totals.json']
        },
        {
            'id': 'iea_va',
            'name': 'IEA Energy & Value Added',
            'file': 'IEA_Energy_ValueAdded.xlsx',
            'description': 'Estrutura econômica, valor adicionado e intensidade energética por setor ISIC',
            'outputs': ['iea_value_added.json', 'iea_manufacturing.json', 'iea_indicators.json']
        },
        {
            'id': 'dc_energy_ai',
            'name': 'IEA Data Annex - Energy and AI',
            'file': 'Data_annex_Energy_and_AI.xlsx',
            'description': 'Infraestrutura energética de data centers: capacidade GW, tipos, projeções',
            'outputs': ['dc_energy_world.json', 'dc_energy_regional.json']
        },
        {
            'id': 'rdd',
            'name': 'IEA Private Energy R&D',
            'file': 'RDDPRIVATE.csv',
            'description': 'Pesquisa e desenvolvimento em energia por país, setor e tecnologia',
            'outputs': ['rdd_energy.json', 'rdd_filters.json']
        },
        {
            'id': 'ghg',
            'name': 'IEA GHG Highlights 2026',
            'file': 'IEA_GHG_highlights_2026.xlsx',
            'description': 'Emissões GHG e CO₂ por país, combustível, setor, per capita e intensidade',
            'outputs': ['ghg_timeseries.json', 'ghg_sector_2024.json', 'ghg_kaya.json']
        },
    ],
    'cross_datasets': [
        {'id': 'dc_air', 'name': 'Data Centers × Qualidade do Ar', 'file': 'cross_dc_air.json'},
        {'id': 'dc_water', 'name': 'Data Centers × Estresse Hídrico', 'file': 'cross_dc_water.json'},
        {'id': 'dc_co2', 'name': 'Data Centers × CO₂', 'file': 'cross_dc_co2.json'},
        {'id': 'dc_ghg_sector', 'name': 'Data Centers × Emissões Setoriais', 'file': 'cross_dc_ghg_sector.json'},
        {'id': 'dc_subsidies', 'name': 'Data Centers × Subsídios Fósseis', 'file': 'cross_dc_subsidies.json'},
        {'id': 'dc_intensities', 'name': 'Data Centers × Intensidades CO₂', 'file': 'cross_dc_intensities.json'},
        {'id': 'dc_fuels', 'name': 'Data Centers × Combustíveis Fósseis', 'file': 'cross_dc_fuels.json'},
        {'id': 'mega', 'name': 'Dataset Integrado Completo', 'file': 'mega_dataset.json'},
    ],
    'all_countries': sorted(dc_by_country['Country'].unique().tolist()),
    'generation_date': pd.Timestamp.now().isoformat(),
}

save_json(metadata, "metadata.json")


# ===================================================================
# 14. RESUMO FINAL
# ===================================================================
print("\n" + "=" * 70)
print("  TRATAMENTO CONCLUÍDO")
print("=" * 70)

# Contar arquivos gerados
json_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.json')]
print(f"\n  Arquivos JSON gerados: {len(json_files)}")
print(f"  Diretório: {OUTPUT_DIR}")
print(f"\n  Bases de dados processadas: {len(metadata['databases'])}")
print(f"  Datasets cruzados: {len(metadata['cross_datasets'])}")
print(f"  Países com data centers: {len(metadata['all_countries'])}")

# Tamanho total
total_size = sum(os.path.getsize(os.path.join(OUTPUT_DIR, f)) for f in json_files)
print(f"  Tamanho total: {total_size / 1024 / 1024:.1f} MB")

print("\n  Arquivos gerados:")
for f in sorted(json_files):
    size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
    print(f"    {f:45s} {size/1024:.0f} KB")

print("\n" + "=" * 70)
print("  Pronto para criar o dashboard HTML!")
print("=" * 70)
