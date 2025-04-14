#!/bin/bash

# It is advised you use a PRO API key from ip-api.com otherwise you will be rate limited.
#
# Input file format:
# Space-separated file with two columns:
# Column 1: Count (number of occurrences)
# Column 2: IP address
# Example:
#    1 45.164.77.202
#   10 168.227.216.2
#    4 202.45.119.130
#
# To generate from an Apache access log example command:
# zcat -f access.log.gz | cut -d ' ' -f1 | sort | uniq -c | sort -rn | column -t > unique-ips.log
#
# To generate from an nginx access log example command:
# zcat -f access.log.gz | cut -d '|' -f4 | sort | uniq -c | sort -rn | column -t > unique-ips.log

input_file="/path/to/unique-ips.log" # Replace with your input file name
rate_limit=0.03 # secs
api_key="abc1234567890" # Replace with your ip-api.com PRO API key

# First check endpoint with a single request
printf "Checking endpoint availability with test request ==> "
curl -s -i https://pro.ip-api.com/json/1.1.1.1?key=${api_key} > /dev/null
echo ""

# Then run the full processing with validation
(echo "count,ip,country,asn,org,host" && (cat ${input_file} | while read -r count ip; do 
    response=$(curl -s "https://pro.ip-api.com/json/${ip}?key=${api_key}")
    
    # Validate JSON response and retry if invalid
    while ! echo "$response" | jq -e . >/dev/null 2>&1; do
        sleep $rate_limit
        response=$(curl -s "https://pro.ip-api.com/json/${ip}?key=${api_key}")
    done
    
    # Run host command and extract hostname
    host_result=$(host "$ip" 2>/dev/null)
    if [[ $? -eq 0 && "$host_result" == *"pointer"* ]]; then
        hostname=$(echo "$host_result" | grep "pointer" | awk '{print $NF}')
    else
        hostname="NA"
    fi
    
    # Extract fields and create CSV line
    if echo "$response" | jq -e '.countryCode and .as' >/dev/null; then
        country=$(echo "$response" | jq -r '.countryCode')
        asn=$(echo "$response" | jq -r '.as')
        org=$(echo "$response" | jq -r '.org')
        echo "$count,$ip,$country,\"$asn\",\"$org\",\"$hostname\""
    fi
    
    sleep $rate_limit
    
done)) | tee ip_analysis_$(date +%Y%m%d_%H%M%S).csv
