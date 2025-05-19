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

# User configurable settings
input_file="unique-ips.log" # Replace with your input file name
rate_limit=0.03 # secs between requests
timeout_seconds=10 # Request timeout in seconds
rate_limit_pause=3600 # 60 minutes pause if all keys are rate limited
max_retries=3 # Maximum number of retry attempts per IP before giving up

# Array of API keys - ADD YOUR API KEYS HERE - IP-API PRO ALLOWS UP TO 10
api_keys=(
    "1stapikey" 
    "2ndapikey"
    "3rdapikey"
)

# Array to store valid API keys
valid_api_keys=()

current_key_index=0
current_key=""
cycle_count=0
free_tier_works=false

# Function to make API request with a specific key or no key
make_api_request_with_key() {
    local ip=$1
    local key=$2
    local endpoint
    
    # Use different endpoint based on whether we have a key
    if [ -n "$key" ]; then
        endpoint="https://pro.ip-api.com/json/${ip}?key=${key}"
    else
        # Free endpoint with no API key
        endpoint="http://ip-api.com/json/${ip}"
    fi
    
    # Make the request with timeout
    curl -s -m $timeout_seconds "$endpoint"
}

# Function to rotate to the next API key
rotate_api_key() {
    # If we have no valid API keys but free tier works, use that
    if [ ${#valid_api_keys[@]} -eq 0 ] && [ "$free_tier_works" = true ]; then
        current_key=""
        return
    fi
    
    # If we have no valid keys and free tier doesn't work, nothing we can do
    if [ ${#valid_api_keys[@]} -eq 0 ]; then
        echo "ERROR: No valid API keys and free tier doesn't work. Cannot continue."
        exit 1
    fi
    
    current_key_index=$((current_key_index + 1))
    
    # If we've gone through all keys
    if [ $current_key_index -ge ${#valid_api_keys[@]} ]; then
        # Increment cycle count
        cycle_count=$((cycle_count + 1))
        
        # If we've cycled through all keys max_retries times, pause
        if [ $cycle_count -ge $max_retries ]; then
            echo "WARNING: All API keys have been cycled through $max_retries times."
            echo "You are limited to 45 requests per minute. If repeatedly breached, you will be banned for 1 hour."
            pause_min=$(echo "scale=1; $rate_limit_pause/60" | bc)
            echo "Pausing for $pause_min minutes to avoid permanent ban..."
            sleep $rate_limit_pause
            cycle_count=0
        fi
        
        # Reset to first key
        current_key_index=0
    fi
    
    current_key="${valid_api_keys[current_key_index]}"
    echo "Switching to API key: ${current_key:-<no key (free tier)>} (cycle $cycle_count of $max_retries)"
}

# Function to make API request with timeout and retry logic
make_api_request() {
    local ip=$1
    local retry_count=0
    local response=""
    
    # Reset cycle count for each new IP request
    cycle_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        response=$(make_api_request_with_key "$ip" "$current_key")
        
        # Check if response is valid JSON
        if echo "$response" | jq -e . >/dev/null 2>&1; then
            # Check if the response indicates a failure
            if echo "$response" | jq -e '.status == "fail"' >/dev/null 2>&1; then
                error_message=$(echo "$response" | jq -r '.message')
                echo "API Error: $error_message"
                rotate_api_key
                retry_count=$((retry_count + 1))
            else
                # Valid successful response
                break
            fi
        else
            # Invalid JSON or timeout occurred
            echo "Request failed or timed out for IP: $ip. Rotating API key."
            rotate_api_key
            retry_count=$((retry_count + 1))
        fi
    done
    
    echo "$response"
}

# Test all API keys and keep only the valid ones
echo "Testing all API keys..."
for key in "${api_keys[@]}"; do
    printf "Testing API key: $key ... "
    response=$(make_api_request_with_key "1.1.1.1" "$key")
    
    if echo "$response" | jq -e '.status == "success"' >/dev/null 2>&1; then
        echo "SUCCESS"
        valid_api_keys+=("$key")
    else
        error_message=$(echo "$response" | jq -r '.message // "Unknown error"')
        echo "FAILED ($error_message)"
    fi
    
    # Small delay between tests to avoid rate limiting
    sleep 1
done

# Also test with no API key as fallback
printf "Testing with no API key (free tier) ... "
response=$(make_api_request_with_key "1.1.1.1" "")
if echo "$response" | jq -e '.status == "success"' >/dev/null 2>&1; then
    echo "SUCCESS"
    free_tier_works=true
    
    # If no valid API keys, add empty string to valid_api_keys
    if [ ${#valid_api_keys[@]} -eq 0 ]; then
        valid_api_keys+=("")
    fi
else
    error_message=$(echo "$response" | jq -r '.message // "Unknown error"')
    echo "FAILED ($error_message)"
    free_tier_works=false
fi

# Check if we have any valid keys or free tier access
if [ ${#valid_api_keys[@]} -eq 0 ] && [ "$free_tier_works" = false ]; then
    echo "No valid API keys or free tier access found. Exiting."
    exit 1
fi

# Set initial key
if [ ${#valid_api_keys[@]} -gt 0 ]; then
    current_key="${valid_api_keys[0]}"
else
    current_key=""
fi

echo "Found ${#valid_api_keys[@]} valid API key(s)"
if [ "$free_tier_works" = true ]; then
    echo "Free tier access is available as fallback"
fi
echo "Starting with: ${current_key:-<no key (free tier)>}"

# Then run the full processing with validation
(echo "count,ip,country,asn,org,host" && (cat ${input_file} | while read -r count ip; do 
    response=$(make_api_request "$ip")
    
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
        echo "$count,$ip,$country,$asn,\"$org\",\"$hostname\""
    else
        echo "Could not process IP: $ip after multiple attempts with all API keys"
        echo "$count,$ip,NA,NA,\"NA\",\"$hostname\""
    fi
    
    sleep $rate_limit
    
done)) | tee ip_analysis_$(date +%Y%m%d_%H%M%S).csv
