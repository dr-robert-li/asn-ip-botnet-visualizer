import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import re
import csv

# Get input file path with validation
while True:
    print("Enter the path to your CSV file:")
    input_file = input().strip()
    if os.path.exists(input_file) and input_file.endswith('.csv'):
        break
    print(f"File {input_file} not found or not a CSV. Please try again.")

# Footer
def add_footer_to_html(html_file_path):
    """Add footer with project link and copyright to an HTML file"""
    footer_html = """
    <div style="margin-top: 30px; padding-top: 10px; border-top: 1px solid #ddd; text-align: center; font-size: 0.8em; font-family: Arial, sans-serif;">
        <p>Powered by <a href="https://github.com/dr-robert-li/asn-ip-botnet-visualizer" target="_blank">ASN-IP Botnet Visualizer</a> | MIT License &copy; 2025 Dr. Robert Li</p>
    </div>
    </body>
    """
    
    # Read the file
    with open(html_file_path, 'r') as f:
        content = f.read()
    
    # Replace the closing body tag with our footer + closing body tag
    modified_content = content.replace('</body>', footer_html)
    
    # Write the modified content back
    with open(html_file_path, 'w') as f:
        f.write(modified_content)

# Create timestamp and base folder name
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
base_folder = f'asn-ip-analysis-{timestamp}'

# Custom CSV parser for this specific format
def parse_custom_csv(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Get header
    header = lines[0].strip().split(',')
    expected_columns = ['count', 'ip', 'country', 'asn', 'org', 'host']
    
    # Verify header matches expected format
    if not all(col in header for col in expected_columns):
        print(f"Warning: Header doesn't match expected format. Found: {header}")
    
    # Parse data rows
    data = []
    for i in range(1, len(lines)):
        line = lines[i].strip()
        if not line:  # Skip empty lines
            continue
        
        # Custom parsing logic for this specific format
        # First, extract quoted fields
        quoted_fields = []
        line_without_quotes = line
        
        # Extract all quoted fields
        quote_pattern = r'"([^"]*)"'
        for match in re.finditer(quote_pattern, line):
            quoted_fields.append(match.group(1))
            # Replace the quoted part with a placeholder
            line_without_quotes = line_without_quotes.replace(match.group(0), "QUOTED_FIELD_PLACEHOLDER")
        
        # Split the remaining line by comma
        parts = line_without_quotes.split(',')
        
        # Replace placeholders with the actual quoted fields
        final_parts = []
        quote_index = 0
        for part in parts:
            if "QUOTED_FIELD_PLACEHOLDER" in part:
                part = part.replace("QUOTED_FIELD_PLACEHOLDER", quoted_fields[quote_index])
                quote_index += 1
            final_parts.append(part)
        
        # Handle the specific format we know about
        if len(final_parts) > 6:
            # We have too many parts, likely due to commas in the ASN field
            # Reconstruct the row with the correct number of fields
            count = final_parts[0]
            ip = final_parts[1]
            country = final_parts[2]
            
            # The ASN field might have been split - combine the parts
            # We know org and host are quoted, so they're already handled correctly
            # Everything between country and org should be part of ASN
            org_index = -2  # Second to last is org
            host_index = -1  # Last is host
            
            asn = ','.join(final_parts[3:org_index])
            org = final_parts[org_index]
            host = final_parts[host_index]
            
            row = [count, ip, country, asn, org, host]
        else:
            # If we have the right number of fields, use them as is
            row = final_parts
        
        # Ensure we have exactly 6 columns
        if len(row) != 6:
            print(f"Warning: Row {i} has {len(row)} fields instead of 6: {row}")
            # Pad with empty strings if needed
            while len(row) < 6:
                row.append("")
            # Or truncate if too many
            row = row[:6]
        
        data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=expected_columns)
    return df

# Try to parse the CSV with our custom parser
try:
    print("Using custom parser for this specific CSV format...")
    df = parse_custom_csv(input_file)
    print(f"Successfully parsed CSV with {len(df)} rows")
    
    # Display the first few rows to verify data
    print("First 5 rows of data:")
    print(df.head())
    
except Exception as e:
    print(f"Custom parser failed: {str(e)}")
    print("Trying alternative method...")
    
    try:
        # Try a more direct approach - read the file and manually fix the format
        with open(input_file, 'r') as f:
            content = f.read()
        
        # Fix the ASN field by replacing commas in the ASN field with a different character
        # This is a bit hacky but should work for this specific format
        fixed_content = re.sub(r'(,HK,AS[^,]*), ([^,"]*)(,")', r'\1@COMMA@\2\3', content)
        
        # Write to a temporary file
        temp_file = input_file + '.fixed.csv'
        with open(temp_file, 'w') as f:
            f.write(fixed_content)
        
        # Read with pandas
        df = pd.read_csv(temp_file)
        
        # Fix the ASN field by replacing the temporary character back to comma
        if 'asn' in df.columns:
            df['asn'] = df['asn'].str.replace('@COMMA@', ',')
        
        # Clean up
        os.remove(temp_file)
        
        print(f"Successfully parsed CSV with alternative method: {len(df)} rows")
        print(df.head())
        
    except Exception as e2:
        print(f"Alternative method failed: {str(e2)}")
        print("Please check your CSV file format and try again.")
        exit(1)

# Convert count to numeric
print("Converting 'count' column to numeric...")
df['count'] = pd.to_numeric(df['count'], errors='coerce')

# Check if we have any valid numeric counts
if df['count'].notna().sum() == 0:
    print("ERROR: No valid numeric values in 'count' column.")
    print("This might indicate a parsing issue with your CSV.")
    
    # Try one more approach - direct string to number conversion
    try:
        print("Attempting direct numeric conversion...")
        numeric_counts = []
        for val in df['count'].values:
            try:
                # Try to extract numeric part if it's a string
                if isinstance(val, str):
                    # Extract digits from the beginning of the string
                    match = re.match(r'^(\d+)', val.strip())
                    if match:
                        numeric_counts.append(int(match.group(1)))
                    else:
                        numeric_counts.append(None)
                else:
                    numeric_counts.append(val)
            except:
                numeric_counts.append(None)
        
        df['count'] = numeric_counts
        print(f"Direct conversion resulted in {df['count'].notna().sum()} valid numeric values")
        
        if df['count'].notna().sum() == 0:
            print("Still no valid numeric values. Exiting.")
            exit(1)
    except Exception as e:
        print(f"Direct conversion failed: {str(e)}")
        exit(1)

# Drop rows with NaN counts
nan_count = df['count'].isna().sum()
if nan_count > 0:
    print(f"Dropping {nan_count} rows with non-numeric 'count' values")
    df = df.dropna(subset=['count'])
    print(f"Remaining rows: {len(df)}")

# Verify we still have data
if len(df) == 0:
    print("ERROR: No data remains after cleaning. Check your CSV format.")
    exit(1)

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
    before_exclusion = len(df)
    df = df[~df['country'].isin(excluded_list)]
    after_exclusion = len(df)
    print(f"Excluded {before_exclusion - after_exclusion} rows from countries: {', '.join(excluded_list)}")
    print(f"Remaining rows: {after_exclusion}")

# Save the filtered dataset
filtered_csv_path = os.path.join(output_folder, 'filtered_data.csv')
df.to_csv(filtered_csv_path, index=False)
print(f"Filtered data saved to {filtered_csv_path}")

# Aggregate data by country for the treemap
country_counts = df.groupby('country')['count'].sum().reset_index()
country_counts = country_counts.sort_values('count', ascending=False)
print(f"Found data for {len(country_counts)} countries")

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
unique_ips = unique_ips.sort_values('unique_ips', ascending=False)

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
asn_counts = df.groupby('asn')['count'].sum().reset_index()
asn_counts = asn_counts.sort_values('count', ascending=False).head(100)

fig3 = px.bar(asn_counts,
             x='asn',
             y='count',
             title='Top 100 ASNs by Request Count',
             labels={'asn': 'ASN', 'count': 'Number of Requests'})
fig3.update_layout(
    xaxis={'tickangle': 45},
    clickmode='event+select',
    dragmode='zoom'
)
fig3.write_html(os.path.join(output_folder, 'requests_by_asn_bar.html'))

# Create organization analysis if 'org' column exists
if 'org' in df.columns:
    org_counts = df.groupby('org')['count'].sum().reset_index()
    org_counts = org_counts.sort_values('count', ascending=False).head(50)

    fig4 = px.bar(org_counts,
                 x='org',
                 y='count',
                 title='Top 50 Organizations by Request Count',
                 labels={'org': 'Organization', 'count': 'Number of Requests'})
    fig4.update_layout(
        xaxis={'tickangle': 45},
        clickmode='event+select',
        dragmode='zoom'
    )
    fig4.write_html(os.path.join(output_folder, 'requests_by_org_bar.html'))

# Create heatmap of ASN vs Country
try:
    # Only create if we have enough data
    if len(df['asn'].unique()) > 1 and len(df['country'].unique()) > 1:
        asn_country_pivot = df.pivot_table(
            index='asn', 
            columns='country', 
            values='count', 
            aggfunc='sum',
            fill_value=0
        ).head(30)

        fig5 = px.imshow(asn_country_pivot,
                        labels=dict(x="Country", y="ASN", color="Request Count"),
                        title="Heatmap of Top 30 ASNs by Country")
        fig5.write_html(os.path.join(output_folder, 'asn_country_heatmap.html'))
    else:
        print("Not enough unique ASNs or countries for heatmap")
except Exception as e:
    print(f"Error creating heatmap: {str(e)}")

# Create IP analysis for top IPs
top_ips = df.groupby('ip')['count'].sum().reset_index()
top_ips = top_ips.sort_values('count', ascending=False).head(50)

# Merge with original data to get country and ASN info
columns_to_merge = ['ip', 'country', 'asn']
if 'org' in df.columns:
    columns_to_merge.append('org')
    
top_ips_details = top_ips.merge(df[columns_to_merge].drop_duplicates(), on='ip')

fig6 = px.bar(top_ips_details,
             x='ip',
             y='count',
             color='country',
             hover_data=['asn'] + (['org'] if 'org' in df.columns else []),
             title='Top 50 IPs by Request Count',
             labels={'ip': 'IP Address', 'count': 'Number of Requests'})
fig6.update_layout(
    xaxis={'tickangle': 45},
    clickmode='event+select',
    dragmode='zoom'
)
fig6.write_html(os.path.join(output_folder, 'top_ips_analysis.html'))

# Create an index.html file that links to all visualizations
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Build list of available visualizations
visualizations = [
    {"file": "requests_by_country_treemap.html", "title": "Requests by Country", "desc": "Treemap visualization of request counts by country"},
    {"file": "unique_ips_by_country_treemap.html", "title": "Unique IPs by Country", "desc": "Treemap visualization of unique IP counts by country"},
    {"file": "requests_by_asn_bar.html", "title": "Top ASNs", "desc": "Bar chart of top 100 ASNs by request count"},
    {"file": "top_ips_analysis.html", "title": "Top IP Addresses", "desc": "Analysis of the top 50 IP addresses by request count"}
]

if 'org' in df.columns:
    visualizations.append({"file": "requests_by_org_bar.html", "title": "Top Organizations", "desc": "Bar chart of top 50 organizations by request count"})

if len(df['asn'].unique()) > 1 and len(df['country'].unique()) > 1:
    visualizations.append({"file": "asn_country_heatmap.html", "title": "ASN-Country Heatmap", "desc": "Heatmap showing relationship between ASNs and countries"})

# Generate HTML for visualization items
viz_items_html = ""
for viz in visualizations:
    viz_items_html += f"""
        <div class="viz-item">
            <h3><a href="{viz['file']}">{viz['title']}</a></h3>
            <p>{viz['desc']}</p>
        </div>
    """

index_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>IP Analysis Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .viz-container {{ display: flex; flex-wrap: wrap; }}
        .viz-item {{ margin: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        a {{ text-decoration: none; color: #0066cc; }}
        a:hover {{ text-decoration: underline; }}
        .stats {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
        footer {{ margin-top: 30px; padding-top: 10px; border-top: 1px solid #ddd; text-align: center; font-size: 0.8em; }}
    </style>
</head>
<body>
    <h1>IP Analysis Results</h1>
    <div class="stats">
        <p><strong>Analysis generated on:</strong> {current_time}</p>
        <p><strong>Total records analyzed:</strong> {len(df)}</p>
        <p><strong>Countries represented:</strong> {len(df['country'].unique())}</p>
        <p><strong>Unique IP addresses:</strong> {len(df['ip'].unique())}</p>
        <p><strong>Unique ASNs:</strong> {len(df['asn'].unique())}</p>
    </div>
    <div class="viz-container">
{viz_items_html}
    </div>
    <p><a href="filtered_data.csv">Download Filtered Dataset</a></p>
    <footer>
        <p>Open Source Project - <a href="https://github.com/dr-robert-li/asn-ip-botnet-visualizer" target="_blank">ASN-IP Botnet Visualizer</a> | MIT License &copy; 2025 Dr. Robert Li</p>
    </footer>
</body>
</html>
"""

with open(os.path.join(output_folder, 'index.html'), 'w') as f:
    f.write(index_html)

# Adding footer to all HTML files
html_files = [
    'requests_by_country_treemap.html',
    'unique_ips_by_country_treemap.html',
    'requests_by_asn_bar.html',
    'top_ips_analysis.html'
]

if 'org' in df.columns:
    html_files.append('requests_by_org_bar.html')

if len(df['asn'].unique()) > 1 and len(df['country'].unique()) > 1:
    html_files.append('asn_country_heatmap.html')

for html_file in html_files:
    file_path = os.path.join(output_folder, html_file)
    if os.path.exists(file_path):
        add_footer_to_html(file_path)

print(f"Analysis complete! Results saved to {output_folder}/")
print(f"Open {output_folder}/index.html to view all visualizations.")
