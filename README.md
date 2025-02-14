# ASN-IP Analysis Tool

A data visualization tool that generates interactive treemaps and bar charts to analyze network traffic patterns across countries and ASNs.

## Features

- Creates treemaps showing total requests by country
- Visualizes unique IP distributions per country
- Generates top 100 ASNs bar chart
- Supports country exclusions for focused analysis
- Automatically organizes outputs in timestamped folders

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

Your input CSV must contain at least the following columns

- `ip`
- `asn`
- `country`
- `count`

These are for:

- ip: IP address (string)
- asn: Autonomous System Number (string, prefixed with 'AS')
- country: Two-letter country code (string)
- count: Number of requests (integer)

It can contain extra columns, but the above columns are required.

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

If you haven't already created this CSV file, log into the server where the Apache structured log files are stored and run the following command:

```bash
site="example.com" && (echo "count,ip,country,asn,org" && find /var/log/ -type f \( -path "*/phpfpm/${site}.access.log*" -o -path "*/apache2/${site}.access.log*" \) -exec zcat -f {} \; | egrep -v "curl|bot|crawler" | cut -d' ' -f1 | sort | uniq -c | sort -rn | while read count ip; do whois_data=$(whois $ip); country=$(echo "$whois_data" | grep -i "^country:" | head -1 | cut -d':' -f2 | tr -d ' '); asn=$(echo "$whois_data" | grep -i "^origin:" | head -1 | cut -d':' -f2 | tr -d ' '); org=$(echo "$whois_data" | grep -i "^org-name:" | head -1 | cut -d':' -f2 | sed 's/^[ \t]*//'); echo "$count,$ip,$country,$asn,\"$org\""; done) | tee ${site}_ip_analysis_$(date +%Y%m%d_%H%M%S).csv
```

Replace the `site` variable above (or wildcard it to get all sites) with the site you want to analyze.

This should output the required CSV file in the current directory with the headers `count,ip,country,asn,org`.

You can swap `asn` and `org` interchangeably if you prefer.

## Output

The tool creates a directory named `asn-ip-analysis-{timestamp}[-excl-{countries}]` containing:

- requests_by_country_treemap.html
- unique_ips_by_country_treemap.html
- requests_by_asn_bar.html

Example output folder:

```bash
asn-ip-analysis-20231025_143022-excl-US-CN/
├── requests_by_country_treemap.html
├── unique_ips_by_country_treemap.html
└── requests_by_asn_bar.html
```

## Licence

MIT License