# ASN-IP Analysis Tool
### Version 2.0
### Author: Dr. Robert Li

A data visualization tool that generates interactive treemaps and bar charts to analyze network traffic patterns across countries and ASNs.

## Features

- Creates treemaps showing total requests by country
- Visualizes unique IP distributions per country
- Generates top 100 ASNs bar chart
- Displays top 50 organizations by request count
- Creates heatmap of ASN vs Country relationships
- Analyzes top 50 IP addresses with detailed information
- Supports country exclusions for focused analysis
- Automatically organizes outputs in timestamped folders
- Handles complex CSV formats with quoted fields and embedded commas
- Provides a comprehensive index page with analysis statistics

## Requirements

- Python 3.6+
- Dependencies listed in requirements.txt

## Installation

1. Clone this repository
2. Create and activate a virtual environment:

```bash
python -m venv venv
```

Then activate using one of the following commands:

- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script:

```bash
python asn-ip.py
```

The tool will prompt for:

- Input CSV file path
- Optional: Countries to exclude (comma-separated)

## Input CSV Format

Your input CSV must contain at least the following columns:

- `ip`
- `asn`
- `country`
- `count`

These are for:

- ip: IP address (string)
- asn: Autonomous System Number (string, prefixed with 'AS')
- country: Two-letter country code (string)
- count: Number of requests (integer)

Additional columns that enhance analysis:

- `org`: Organization name (string)
- `host`: Hostname (string)

The tool can handle complex CSV formats, including:
- Fields with embedded commas (like in ASN names)
- Quoted fields (like organization names)
- Different CSV dialects and delimiters

An example:

```csv
count,ip,country,region,city,asn
9359,34.40.146.25,Australia,New South Wales,Sydney,Google LLC
2913,147.41.128.35,Australia,Tasmania,Hobart,Government of Tasmania
1591,155.190.55.4,Australia,Victoria,Melbourne,CIE
1188,110.145.205.94,Australia,South Australia,Adelaide,Telstra Limited
1127,89.248.165.95,The Netherlands,North Holland,Amsterdam,IP Volume inc
```

### Generating the CSV File

If you haven't already created this CSV file, log into the server where the Apache structured log files are stored and run the following example command:

```bash
site="example.com" && (echo "count,ip,country,asn,org,host" && sudo find /var/log/apache2/ -type f \( -path "*/${site}.access.log*" \) -exec zcat -f {} \; | egrep -v "curl|bot|crawler|spider" | cut -d' ' -f1 | sort | uniq -c | sort -rn | while read count ip; do api_data=$(curl -s "http://ip-api.com/json/${ip}"); country=$(echo "$api_data" | jq -r '.countryCode'); asn=$(echo "$api_data" | jq -r '.as'); org=$(echo "$api_data" | jq -r '.org'); host=$(echo "$api_data" | jq -r '.isp'); echo "$count,$ip,$country,\"$asn\",\"$org\",\"$host\""; done) | tee ${site}_ip_analysis_$(date +%Y%m%d_%H%M%S).csv
```

Modify as you see fit. Replace the `site` variable above (or wildcard it to get all sites) with the site you want to analyze. Replace the find path to reflect where your logs are located. You will want to run this in `sudo` mode.

This should output the required CSV file with a timestamp in the current directory with the headers `count,ip,country,asn,org,host`.

You can then `curl` or `wget` the CSV file to your local machine and run the tool.

Alternatively an implementation that uses the IP-api PRO endpoint can be found in `checkip.sh`. Read the commented documentation within this script. It assumes you already have a pre-filtered output.

## Output

The tool creates a directory named `asn-ip-analysis-{timestamp}[-excl-{countries}]` containing:

- index.html - Main dashboard with links to all visualizations and statistics
- requests_by_country_treemap.html - Interactive treemap of requests by country
- unique_ips_by_country_treemap.html - Treemap showing unique IP distribution
- requests_by_asn_bar.html - Bar chart of top 100 ASNs
- requests_by_org_bar.html - Bar chart of top 50 organizations (if org data available)
- asn_country_heatmap.html - Heatmap showing ASN distribution across countries
- top_ips_analysis.html - Detailed analysis of top 50 IP addresses
- filtered_data.csv - The processed dataset used for analysis

Example output folder:

```bash
asn-ip-analysis-20231025_143022-excl-US-CN/
├── index.html
├── filtered_data.csv
├── requests_by_country_treemap.html
├── unique_ips_by_country_treemap.html
├── requests_by_asn_bar.html
├── requests_by_org_bar.html
├── asn_country_heatmap.html
└── top_ips_analysis.html
```

Example tree map showing a [Mirai botnet](https://en.wikipedia.org/wiki/Mirai_(malware)):

![https://github.com/dr-robert-li/asn-ip-botnet-visualizer/blob/main/example.png?raw=true](https://github.com/dr-robert-li/asn-ip-botnet-visualizer/blob/main/example.png?raw=true)

## License

MIT License

Copyright (c) 2025 Dr. Robert Li

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
