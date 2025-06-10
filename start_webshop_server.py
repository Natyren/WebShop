#!/usr/bin/env python3
"""
Helper script to start and manage WebShop server
"""

import subprocess
import time
import requests
import os
import signal
import sys
from pathlib import Path

class WebShopServerManager:
    def __init__(self, port=3000, host='127.0.0.1'):
        self.port = port
        self.host = host
        self.base_url = f'http://{host}:{port}'
        self.server_process = None
    
    def is_server_running(self):
        """Check if WebShop server is already running."""
        try:
            response = requests.get(f'{self.base_url}/', timeout=3)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def find_server_script(self):
        """Find the WebShop server script in common locations."""
        possible_paths = [
            'web_agent_site/server.py',
            'server.py',
            'webshop/server.py',
            '../webshop/server.py',
            './web_agent_site/server/app.py',
            './server/app.py'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Try to find any server-related files
        for root, dirs, files in os.walk('.'):
            for file in files:
                if 'server' in file.lower() and file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    if 'test' not in full_path.lower():
                        return full_path
        
        return None
    
    def start_server(self):
        """Start the WebShop server."""
        if self.is_server_running():
            print(f"✅ WebShop server is already running at {self.base_url}")
            return True
        
        server_script = self.find_server_script()
        if not server_script:
            print("❌ Could not find WebShop server script.")
            print("Please make sure the server script is available and start it manually:")
            print(f"   python server.py --port {self.port}")
            return False
        
        print(f"🚀 Starting WebShop server using {server_script}...")
        
        try:
            # Start server process
            self.server_process = subprocess.Popen([
                sys.executable, server_script, 
                '--port', str(self.port),
                '--host', self.host
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            max_wait = 30  # seconds
            wait_interval = 1
            
            for i in range(max_wait):
                if self.is_server_running():
                    print(f"✅ WebShop server started successfully at {self.base_url}")
                    return True
                time.sleep(wait_interval)
                print(f"⏳ Waiting for server to start... ({i+1}/{max_wait})")
            
            print("❌ Server failed to start within the timeout period")
            self.stop_server()
            return False
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the WebShop server."""
        if self.server_process:
            print("🛑 Stopping WebShop server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
    
    def restart_server(self):
        """Restart the WebShop server."""
        self.stop_server()
        time.sleep(2)
        return self.start_server()

def main():
    """Main function to run the server manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description='WebShop Server Manager')
    parser.add_argument('--port', type=int, default=3000, help='Port to run server on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind server to')
    parser.add_argument('--action', choices=['start', 'stop', 'restart', 'status'], 
                       default='start', help='Action to perform')
    
    args = parser.parse_args()
    
    manager = WebShopServerManager(port=args.port, host=args.host)
    
    def signal_handler(sig, frame):
        print("\n🛑 Received interrupt signal, stopping server...")
        manager.stop_server()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.action == 'start':
        if manager.start_server():
            print("Server started successfully. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            sys.exit(1)
    
    elif args.action == 'stop':
        manager.stop_server()
    
    elif args.action == 'restart':
        manager.restart_server()
    
    elif args.action == 'status':
        if manager.is_server_running():
            print(f"✅ Server is running at {manager.base_url}")
        else:
            print("❌ Server is not running")

if __name__ == '__main__':
    main() 