import socket
import json
import base64
import logging
import os
import time
import threading
import random
import string
import csv
import argparse

# Global configuration
SERVER_ADDRESS = ('172.18.0.2', 8889)
# Increase base timeout for large files
BASE_TIMEOUT = 180  # 3 minutes
# Add maximum retries for connection attempts
MAX_RETRIES = 3

class MultithreadingStressTest:
    def __init__(self, server_address=SERVER_ADDRESS):
        self.server_address = server_address
        self.results = []
        self.result_lock = threading.Lock()
        
    def get_test_file(self, size_mb):
        """Get the path to a test file with specified size"""
        file_path = f'./test_files/{size_mb}mb.txt'
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Test file {file_path} not found. Please make sure it exists.")
        
        return file_path
    
    def send_command(self, command_str="", timeout=BASE_TIMEOUT):
        """Send command to server with timeout and retry logic"""
        retries = 0
        last_exception = None
        
        # Calculate timeout based on command size
        if len(command_str) > 1000000:  # If command is large (>1MB)
            timeout = max(timeout, len(command_str) // 100000)  # Scale timeout with size
        
        while retries < MAX_RETRIES:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            try:
                sock.connect(self.server_address)
                sock.sendall((command_str + "\r\n\r\n").encode())
                
                data_received = ""
                while True:
                    data = sock.recv(4096)  # Larger buffer for better performance
                    if data:
                        data_received += data.decode()
                        if "\r\n\r\n" in data_received:
                            break
                    else:
                        break
                        
                return json.loads(data_received.split("\r\n\r\n")[0])
            except Exception as e:
                last_exception = e
                retries += 1
                if retries < MAX_RETRIES:
                    # Exponential backoff with jitter
                    wait_time = (2 ** retries) + random.random()
                    print(f"  Command failed, retrying in {wait_time:.1f}s ({retries}/{MAX_RETRIES})...")
                    time.sleep(wait_time)
            finally:
                sock.close()
        
        # If we get here, all retries failed
        return {'status': 'ERROR', 'data': f"After {MAX_RETRIES} retries: {str(last_exception)}"}
    
    def run_comprehensive_test(self, server_workers):
        """Run comprehensive stress test with all combinations"""
        logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Test parameters as specified in requirements
        operations = ['download', 'upload']
        file_sizes = [10, 50, 100]  # MB
        client_workers = [1, 5, 50]
        
        results = []
        test_num = 1
        
        print(f"Starting Multithreading Stress Test (Server Workers: {server_workers})")
        print("=" * 80)
        
        for operation in operations:
            for file_size in file_sizes:
                for num_clients in client_workers:
                    print(f"\nTest {test_num}: {operation}, {file_size}MB, {num_clients} clients, {server_workers} server workers")
                    print("-" * 60)
                    
                    try:
                        result_threading = self.run_single_test(
                            operation, file_size, num_clients
                        )
                        result_threading.update({
                            'no': test_num,
                            'operation': operation,
                            'volume_mb': file_size,
                            'client_workers': num_clients,
                            'server_workers': server_workers,
                            'concurrency_type': 'multithreading'
                        })
                        results.append(result_threading)
                        
                        print(f"Multithreading - Success: {result_threading['client_success']}, Failed: {result_threading['client_failed']}")
                        
                    except Exception as e:
                        print(f"Multithreading test failed: {e}")
                        results.append(self.create_error_result(test_num, operation, file_size, num_clients, server_workers, 'multithreading', str(e)))
                    
                    test_num += 1
                    
                    # Short delay between tests
                    time.sleep(1)
        
        # Save and display results
        self.save_results_to_csv(results, server_workers)
        self.print_summary_table(results)
        
        return results
    
    def run_single_test(self, operation, file_size_mb, num_workers):
        """Run a single stress test"""
        test_id = int(time.time())
        filename_base = f"test_{file_size_mb}mb_{test_id}"
        
        # Get test file path
        filepath = self.get_test_file(file_size_mb)
        
        # For download test, upload files first
        if operation == 'download':
            print(f"  Pre-uploading files for download test using {filepath}...")
            self.pre_upload_files(filepath, filename_base, num_workers)
        
        # Run the test
        start_time = time.time()
        results = self.run_multithreading_test(operation, filepath, filename_base, num_workers)
        end_time = time.time()
        total_time = end_time - start_time
        
        return self.analyze_test_results(results, total_time)
    
    def pre_upload_files(self, filepath, filename_base, num_workers):
        """Pre-upload files for download testing with adaptive behavior"""
        print(f"  Reading file {filepath}...")
        try:
            with open(filepath, 'rb') as f:
                file_content = base64.b64encode(f.read()).decode()
            
            print(f"  File size (base64): {len(file_content)/1024/1024:.2f} MB")
            print(f"  Uploading {num_workers} files for download test...")
            
            success_count = 0
            server_workers = int(os.environ.get('SERVER_WORKERS', '1'))
            
            # If server has few workers, reduce concurrency
            batch_size = min(5, max(1, server_workers)) 
            batches = [range(i, min(i+batch_size, num_workers)) for i in range(0, num_workers, batch_size)]
            
            for batch in batches:
                batch_threads = []
                batch_results = []
                
                # Process each batch with threads
                for i in batch:
                    def upload_file(idx):
                        print(f"  Uploading file {idx+1}/{num_workers}...", end="", flush=True)
                        command = f"UPLOAD {filename_base}_{idx}.dat {file_content}"
                        # Scale timeout with file size
                        timeout = max(BASE_TIMEOUT, len(file_content) // 50000)
                        result = self.send_command(command, timeout=timeout)
                        
                        if result['status'] == 'OK':
                            print(" OK")
                            batch_results.append(True)
                        else:
                            print(f" FAILED: {result.get('data', 'Unknown error')}")
                            batch_results.append(False)
                    
                    t = threading.Thread(target=upload_file, args=(i,))
                    batch_threads.append(t)
                    t.start()
                
                # Wait for batch to complete
                for t in batch_threads:
                    t.join()
                
                success_count += sum(1 for r in batch_results if r)
                
                # If current batch had failures, wait a bit longer before next batch
                if batch_results.count(False) > 0:
                    time.sleep(5)
            
            print(f"  Pre-upload complete. Success: {success_count}, Failed: {num_workers - success_count}")
            
            if success_count < num_workers:
                print("  WARNING: Some pre-upload files failed. Download test may not be accurate.")
                
            # If too many failures, adjust timeout and retry count for main test
            if success_count < num_workers // 2:
                print("  CRITICAL: More than 50% uploads failed. Server may be overwhelmed.")
                
            return success_count
            
        except Exception as e:
            print(f"  ERROR during pre-upload: {str(e)}")
            return 0
    
    def run_multithreading_test(self, operation, filepath, filename_base, num_workers):
        """Run test using direct thread creation"""
        threads = []
        results = []
        
        # Create thread-safe container for results
        thread_results = []
        
        # Define thread functions that add results to our container
        def upload_thread(worker_id):
            try:
                result = self.upload_worker(worker_id, filepath, filename_base)
                with self.result_lock:
                    thread_results.append(result)
            except Exception as e:
                with self.result_lock:
                    thread_results.append({
                        'success': False, 
                        'error': str(e), 
                        'duration': 0, 
                        'bytes': 0,
                        'worker_id': worker_id
                    })
        
        def download_thread(worker_id):
            try:
                result = self.download_worker(worker_id, filename_base)
                with self.result_lock:
                    thread_results.append(result)
            except Exception as e:
                with self.result_lock:
                    thread_results.append({
                        'success': False, 
                        'error': str(e), 
                        'duration': 0, 
                        'bytes': 0,
                        'worker_id': worker_id
                    })
        
        # Create and start threads
        for i in range(num_workers):
            if operation == 'upload':
                t = threading.Thread(target=upload_thread, args=(i,))
            elif operation == 'download':
                t = threading.Thread(target=download_thread, args=(i,))
            
            threads.append(t)
            t.start()
            
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        return thread_results
    
    def upload_worker(self, worker_id, filepath, filename_base):
        """Upload worker function"""
        start_time = time.time()
        
        try:
            with open(filepath, 'rb') as f:
                file_content = base64.b64encode(f.read()).decode()
            
            command = f"UPLOAD {filename_base}_{worker_id}.dat {file_content}"
            result = self.send_command(command, timeout=300)  # Increased timeout for large files
            
            end_time = time.time()
            duration = end_time - start_time
            bytes_transferred = len(file_content) if result['status'] == 'OK' else 0
            
            return {
                'success': result['status'] == 'OK',
                'duration': duration,
                'bytes': bytes_transferred,
                'worker_id': worker_id,
                'error': result.get('data', '') if result['status'] != 'OK' else ''
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                'success': False,
                'duration': end_time - start_time,
                'bytes': 0,
                'error': str(e),
                'worker_id': worker_id
            }
    
    def download_worker(self, worker_id, filename_base):
        """Download worker function"""
        start_time = time.time()
        
        try:
            command = f"GET {filename_base}_{worker_id}.dat"
            result = self.send_command(command, timeout=120)
            
            end_time = time.time()
            duration = end_time - start_time
            bytes_transferred = len(result['data_file']) if result['status'] == 'OK' else 0
            
            return {
                'success': result['status'] == 'OK',
                'duration': duration,
                'bytes': bytes_transferred,
                'worker_id': worker_id
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                'success': False,
                'duration': end_time - start_time,
                'bytes': 0,
                'error': str(e),
                'worker_id': worker_id
            }
    
    def analyze_test_results(self, results, total_time):
        """Analyze test results"""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        if successful:
            avg_duration = sum(r['duration'] for r in successful) / len(successful)
            total_bytes = sum(r['bytes'] for r in successful)
            avg_throughput = total_bytes / sum(r['duration'] for r in successful) if sum(r['duration'] for r in successful) > 0 else 0
        else:
            avg_duration = 0
            total_bytes = 0
            avg_throughput = 0
        
        return {
            'total_time': total_time,
            'avg_duration_per_client': avg_duration,
            'throughput_per_client': avg_throughput,
            'client_success': len(successful),
            'client_failed': len(failed),
            'server_success': len(successful),  # Assuming server success matches client success
            'server_failed': len(failed),
            'total_bytes': total_bytes
        }
    
    def create_error_result(self, test_num, operation, file_size, num_clients, num_servers, concurrency_type, error):
        """Create error result entry"""
        return {
            'no': test_num,
            'operation': operation,
            'volume_mb': file_size,
            'client_workers': num_clients,
            'server_workers': num_servers,
            'concurrency_type': concurrency_type,
            'total_time': 0,
            'avg_duration_per_client': 0,
            'throughput_per_client': 0,
            'client_success': 0,
            'client_failed': num_clients,
            'server_success': 0,
            'server_failed': num_clients,
            'error': error
        }
    
    def save_results_to_csv(self, results, server_workers):
        """Save results to CSV file"""
        filename = f'multithreading_test_results_{server_workers}_workers_{int(time.time())}.csv'
        
        fieldnames = [
            'no', 'operation', 'volume_mb', 'client_workers', 'server_workers',
            'total_time', 'avg_duration_per_client', 'throughput_per_client',
            'client_success', 'client_failed', 'server_success', 'server_failed'
        ]
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                row = {field: result.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"\n✓ Results saved to {filename}")
    
    def print_summary_table(self, results):
        """Print comprehensive results table"""
        print(f"\n{'='*150}")
        print("MULTITHREADING STRESS TEST RESULTS")
        print(f"{'='*150}")
        
        header = f"{'No':<4} {'Op':<8} {'Vol':<5} {'C.W':<4} {'S.W':<4} {'Time':<8} {'Avg(s)':<8} {'Tput':<12} {'C.Succ':<6} {'C.Fail':<6} {'S.Succ':<6} {'S.Fail':<6}"
        print(header)
        print("-" * 150)
        
        for result in results:
            row = (f"{result.get('no', ''):<4} "
                   f"{result.get('operation', ''):<8} "
                   f"{result.get('volume_mb', '')}MB{'':<2} "
                   f"{result.get('client_workers', ''):<4} "
                   f"{result.get('server_workers', ''):<4} "
                   f"{result.get('total_time', 0):<8.2f} "
                   f"{result.get('avg_duration_per_client', 0):<8.2f} "
                   f"{result.get('throughput_per_client', 0):<12.0f} "
                   f"{result.get('client_success', 0):<6} "
                   f"{result.get('client_failed', 0):<6} "
                   f"{result.get('server_success', 0):<6} "
                   f"{result.get('server_failed', 0):<6}")
            print(row)

def main():
    parser = argparse.ArgumentParser(description='Multithreading Stress Test for File Server')
    parser.add_argument('--server-ip', default='172.18.0.2', help='Server IP address')
    parser.add_argument('--server-port', type=int, default=8889, help='Server port')
    parser.add_argument('--server-workers', type=int, default=5, 
                        help='Number of workers on the server side (1, 5, or 50)')
    args = parser.parse_args()
    
    # Ensure test files exist
    for size in [10, 50, 100]:
        file_path = f'./test_files/{size}mb.txt'
        if not os.path.exists(file_path):
            print(f"ERROR: Test file {file_path} not found.")
            print("Please make sure the following files exist in the test_files directory:")
            print("  - 10mb.txt")
            print("  - 50mb.txt") 
            print("  - 100mb.txt")
            return
    
    server_address = (args.server_ip, args.server_port)
    
    print("File Server Multithreading Stress Test")
    print("======================================")
    print(f"Target Server: {server_address[0]}:{server_address[1]}")
    print(f"Server Workers: {args.server_workers}")
    print(f"Test Files: 10mb.txt, 50mb.txt, 100mb.txt")
    print(f"Test Combinations: 2 operations × 3 volumes × 3 client workers = 18 tests")
    print()
    
    test = MultithreadingStressTest(server_address)
    results = test.run_comprehensive_test(args.server_workers)
    
    print(f"\n✓ Multithreading stress test completed!")
    print(f"✓ Total tests run: {len(results)}")
    print(f"✓ Results saved to CSV file")

if __name__ == "__main__":
    main()
