#!/usr/bin/env python3

import sys
import subprocess
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

captured_output = b""
process = None
should_run = True

def run_binary(args):
    global captured_output, process, should_run

    while should_run:
        captured_output = b""
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        print(f"Started process with PID: {process.pid}")
        
        while True:
            try:
                chunk = process.stdout.read(1024)
                if not chunk:
                    break
                captured_output += chunk
                print(chunk.decode(), end='', flush=True)
            except Exception as e:
                print(f"Error reading output: {e}")
                break
        
        exit_code = process.wait()
        print(f"Process exited with code: {exit_code}")
        
        if not should_run:
            break
        
        print("Restarting in 5 seconds...")
        time.sleep(5)

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/get_out':
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.end_headers()
            self.wfile.write(captured_output)
        elif self.path == '/stop':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Stopping the binary...')
            stop_binary()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')

def run_server(port=4444):
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"Server running on port {port}")
    httpd.serve_forever()

def stop_binary():
    global should_run, process
    should_run = False
    if process:
        process.terminate()
    time.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./runner.py <binary> [args...]")
        sys.exit(1)

    binary_thread = threading.Thread(target=run_binary, args=(sys.argv[1:],))
    binary_thread.start()

    try:
        run_server()
    except KeyboardInterrupt:
        print("Shutting down...")
        stop_binary()
        binary_thread.join()
        sys.exit(0)
