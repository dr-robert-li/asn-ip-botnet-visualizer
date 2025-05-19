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
rate_limit=0.03 # fp secs between ip-api requests
host_rate_limit=1 # integer timeout in seconds for DNS host lookups 
rate_limit_pause=3600 # 60 minutes pause if all keys are rate limited
timeout_seconds=10 # Timeout in seconds before retrying IP
max_retries=3 # Maximum number of retry attempts per IP before giving up

# Array of API keys - add all your keys here
api_keys=(
    "1stAPIKey" 
    "2ndAPIKey"
    "3rdAPIKey"
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
    
    # Make the request with multiple timeout options
    curl -s --connect-timeout 5 --max-time $timeout_seconds "$endpoint"
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
        echo "ERROR: No valid API keys and free tier doesn't work. Cannot continue." >&2
        exit 1
    fi
    
    current_key_index=$((current_key_index + 1))
    
    # If we've gone through all keys
    if [ $current_key_index -ge ${#valid_api_keys[@]} ]; then
        # Increment cycle count
        cycle_count=$((cycle_count + 1))
        
        # If we've cycled through all keys max_retries times, pause
        if [ $cycle_count -ge $max_retries ]; then
            echo "WARNING: All API keys have been cycled through $max_retries times." >&2
            echo "You are limited to 45 requests per minute. If repeatedly breached, you will be banned for 1 hour." >&2
            pause_min=$(echo "scale=1; $rate_limit_pause/60" | bc)
            echo "Pausing for $pause_min minutes to avoid permanent ban..." >&2
            sleep $rate_limit_pause
            cycle_count=0
        fi
        
        # Reset to first key
        current_key_index=0
    fi
    
    current_key="${valid_api_keys[current_key_index]}"
    echo "Switching to API key: ${current_key:-<no key (free tier)>} (cycle $cycle_count of $max_retries)" >&2
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
        
        # Check if response is empty
        if [ -z "$response" ]; then
            echo "WARNING: Empty response or timeout for IP: $ip. Rotating API key." >&2
            rotate_api_key
            retry_count=$((retry_count + 1))
            continue
        fi
        
        # Check if response is valid JSON
        if echo "$response" | jq -e . >/dev/null 2>&1; then
            # Check if the response indicates a failure
            if echo "$response" | jq -e '.status == "fail"' >/dev/null 2>&1; then
                error_message=$(echo "$response" | jq -r '.message')
                echo "API Error: $error_message" >&2
                rotate_api_key
                retry_count=$((retry_count + 1))
            else
                # Valid successful response
                break
            fi
        else
            # Invalid JSON or timeout occurred
            echo "Request failed or timed out for IP: $ip. Rotating API key." >&2
            rotate_api_key
            retry_count=$((retry_count + 1))
        fi
        
        # Add a small delay between retries
        sleep 1
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

# Generate the output filename
output_filename="ip_analysis_$(date +%Y%m%d_%H%M%S).csv"
echo "Starting IP analysis. Results will be written to: $output_filename" >&2
echo "This may take some time depending on the number of IPs to process..." >&2

# Then run the full processing with validation
(echo "count,ip,country,asn,org,host" && (cat ${input_file} | while read -r count ip; do 
    # Print status message to stderr, not stdout
    echo "===> Processing IP: $ip" >&2
    response=$(make_api_request "$ip")
    
    # Check if dig command exists
    if command -v dig >/dev/null 2>&1; then
        # Use dig with configurable timeout
        hostname=$(dig +short -x "$ip" +time=$host_rate_limit +tries=1 2>/dev/null)
        if [ -z "$hostname" ]; then
            hostname="NA"
        fi
    else
        # Fallback to host command if dig is not available
        host_pid_file=$(mktemp)
        error_file=$(mktemp)
        (host "$ip" > "$host_pid_file" 2> "$error_file") &
        host_pid=$!

        # Wait for host command with configurable timeout
        host_wait=0
        while [ $(echo "$host_wait < $host_rate_limit" | bc) -eq 1 ] && kill -0 $host_pid 2>/dev/null; do
            sleep 0.1
            host_wait=$(echo "$host_wait + 0.1" | bc)
        done

        # If process is still running, kill it
        if kill -0 $host_pid 2>/dev/null; then
            # Redirect kill output to /dev/null to avoid "Terminated" messages
            kill $host_pid > /dev/null 2>&1
            wait $host_pid > /dev/null 2>&1
            hostname="NA"
        else
            host_result=$(cat "$host_pid_file")
            if [[ -n "$host_result" && "$host_result" == *"pointer"* ]]; then
                hostname=$(echo "$host_result" | grep "pointer" | awk '{print $NF}')
            else
                hostname="NA"
            fi
        fi

        # Clean up temp files
        rm -f "$host_pid_file" "$error_file"
    fi
    
    # Extract fields and create CSV line
    if [ -n "$response" ] && echo "$response" | jq -e '.countryCode and .as' >/dev/null 2>&1; then
        country=$(echo "$response" | jq -r '.countryCode')
        asn=$(echo "$response" | jq -r '.as')
        org=$(echo "$response" | jq -r '.org')
        echo "$count,$ip,$country,$asn,\"$org\",\"$hostname\""
    else
        # Print error message to stderr, not stdout
        echo "Could not process IP: $ip after multiple attempts with all API keys" >&2
        echo "$count,$ip,NA,NA,\"NA\",\"$hostname\""
    fi
    
    sleep $rate_limit
    
done)) | tee "$output_filename"

echo "Analysis complete. Results saved to: $output_filename" >&2
