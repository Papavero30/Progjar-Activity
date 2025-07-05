#!/bin/bash

#ab -n jumlah_request -c jumlah_konkuren http://localhost:8887/testing
#ab -n jumlah_request -c jumlah_konkuren http://localhost:8887/testing.txt

# Function to check if server is running
check_server() {
    local host=$1
    local port=$2
    local name=$3
    
    # Try connecting with timeout
    timeout 3 bash -c "</dev/tcp/$host/$port" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ $name Server detected on $host:$port"
        return 0
    else
        echo "✗ $name Server not running on $host:$port"
        return 1
    fi
}

echo "=== HTTP Server Performance Testing ==="
echo "Auto-detecting available servers..."

thread_pool_available=false
process_pool_available=false
thread_pool_host=""
process_pool_host=""

# Check servers on multiple hosts
hosts=("172.16.16.101" "localhost" "127.0.0.1")

for host in "${hosts[@]}"; do
    # Check Thread Pool Server (8885)
    if check_server $host 8885 "Thread Pool"; then
        thread_pool_available=true
        thread_pool_host=$host
        break
    fi
done

for host in "${hosts[@]}"; do
    # Check Process Pool Server (8889)  
    if check_server $host 8889 "Process Pool"; then
        process_pool_available=true
        process_pool_host=$host
        break
    fi
done

echo ""

if [ "$thread_pool_available" = false ] && [ "$process_pool_available" = false ]; then
    echo "No servers are currently running!"
    echo "Please start at least one server on mesin1 (172.16.16.101):"
    echo "  python server_thread_pool_http.py"
    echo "  python server_process_pool_http.py"
    exit 1
fi

echo "Available testing options:"
if [ "$thread_pool_available" = true ]; then
    echo "1. Thread Pool Server Testing ($thread_pool_host:8885)"
fi
if [ "$process_pool_available" = true ]; then
    echo "2. Process Pool Server Testing ($process_pool_host:8889)"
fi
if [ "$thread_pool_available" = true ] && [ "$process_pool_available" = true ]; then
    echo "3. Both Servers Testing"
fi
echo "4. Directory Operations Testing"
echo "========================================"

read -p "Select test mode: " choice

case $choice in
    1)
        if [ "$thread_pool_available" = true ]; then
            echo "Testing Thread Pool Server on $thread_pool_host:8885..."
            echo "Basic request test:"
            ab -n 100 -c 10 http://$thread_pool_host:8885/
            echo ""
            echo "Directory listing test:"
            ab -n 50 -c 5 http://$thread_pool_host:8885/listdir
        else
            echo "Thread Pool Server is not running!"
        fi
        ;;
    2)
        if [ "$process_pool_available" = true ]; then
            echo "Testing Process Pool Server on $process_pool_host:8889..."
            echo "Basic request test:"
            ab -n 100 -c 10 http://$process_pool_host:8889/
            echo ""
            echo "Directory listing test:"
            ab -n 50 -c 5 http://$process_pool_host:8889/listdir
        else
            echo "Process Pool Server is not running!"
        fi
        ;;
    3)
        if [ "$thread_pool_available" = true ] && [ "$process_pool_available" = true ]; then
            echo "Testing both servers..."
            echo "Thread Pool Server ($thread_pool_host:8885):"
            ab -n 100 -c 10 http://$thread_pool_host:8885/
            echo ""
            echo "Process Pool Server ($process_pool_host:8889):"
            ab -n 100 -c 10 http://$process_pool_host:8889/
        else
            echo "Both servers are not running!"
        fi
        ;;
    4)
        # Test with any available server
        if [ "$thread_pool_available" = true ]; then
            host=$thread_pool_host
            port=8885
            server_name="Thread Pool"
        elif [ "$process_pool_available" = true ]; then
            host=$process_pool_host
            port=8889
            server_name="Process Pool"
        fi
        
        echo "Testing directory operations on $server_name Server ($host:$port)..."
        echo "Directory listing test:"
        ab -n 50 -c 5 http://$host:$port/listdir
        echo ""
        echo "Basic connectivity test:"
        ab -n 30 -c 3 http://$host:$port/
        ;;
    *)
        echo "Invalid choice"
        ;;
esac

# Original test for compatibility (if server on 8887 is available)
for host in "${hosts[@]}"; do
    if check_server $host 8887 "Legacy" >/dev/null 2>&1; then
        echo ""
        echo "Original test (for compatibility):"
        ab -n 100 -c 50 http://$host:8887/testing.txt
        break
    fi
done

