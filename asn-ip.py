import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Get input file path with validation
while True:
    print("Enter the path to your CSV file:")
    input_file = input().strip()
    if os.path.exists(input_file) and input_file.endswith('.csv'):
        break
    print(f"File {input_file} not found or not a CSV. Please try again.")

# Create timestamp and base folder name
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
base_folder = f'asn-ip-analysis-{timestamp}'

# Read the CSV file with error handling
df = pd.read_csv(input_file, on_bad_lines='skip', engine='python')

# Convert count to numeric, coercing errors to NaN
df['count'] = pd.to_numeric(df['count'], errors='coerce')

# Get user input for countries to exclude
print("Enter countries to exclude (comma-separated) or press Enter to include all:")
excluded_countries = input().strip()
excluded_list = [c.strip() for c in excluded_countries.split(',')] if excluded_countries else []

# Modify folder name if exclusions exist
if excluded_list:
    excluded_suffix = '-excl-' + '-'.join(excluded_list)
    output_folder = base_folder + excluded_suffix
else:
    output_folder = base_folder

# Create output directory
os.makedirs(output_folder, exist_ok=True)

# Filter dataframe based on exclusions
if excluded_list:
    df = df[~df['country'].isin(excluded_list)]

# Aggregate data by country for the treemap
country_counts = df.groupby('country')['count'].sum().reset_index()

# Create treemap of total requests by country with enhanced interactivity
fig1 = px.treemap(country_counts,
                 path=['country'],
                 values='count',
                 title='Total Requests by Country',
                 custom_data=['country', 'count'])
fig1.update_traces(
    hovertemplate='<b>Country:</b> %{customdata[0]}<br><b>Requests:</b> %{customdata[1]:,.0f}<extra></extra>'
)
fig1.update_layout(
    uniformtext=dict(minsize=10, mode='hide'),
    clickmode='event+select'
)
fig1.write_html(os.path.join(output_folder, 'requests_by_country_treemap.html'))

# Create treemap of unique IPs by country
unique_ips = df.groupby('country')['ip'].nunique().reset_index()
unique_ips.columns = ['country', 'unique_ips']

fig2 = px.treemap(unique_ips,
                 path=['country'],
                 values='unique_ips',
                 title='Unique IPs by Country',
                 custom_data=['country', 'unique_ips'])
fig2.update_traces(
    hovertemplate='<b>Country:</b> %{customdata[0]}<br><b>Unique IPs:</b> %{customdata[1]:,.0f}<extra></extra>'
)
fig2.update_layout(
    uniformtext=dict(minsize=10, mode='hide'),
    clickmode='event+select'
)
fig2.write_html(os.path.join(output_folder, 'unique_ips_by_country_treemap.html'))

# Create column graph of requests by ASN
asn_counts = df.groupby('asn')['count'].sum().sort_values(ascending=False).head(20).reset_index()

fig3 = px.bar(asn_counts,
             x='asn',
             y='count',
             title='Top 20 ASNs by Request Count',
             labels={'asn': 'ASN', 'count': 'Number of Requests'})
fig3.update_layout(
    xaxis={'tickangle': 45},
    clickmode='event+select',
    dragmode='zoom'
)
fig3.write_html(os.path.join(output_folder, 'requests_by_asn_bar.html'))