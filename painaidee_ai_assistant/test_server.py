#!/usr/bin/env python3
"""
Simple HTTP server for testing 3D model functionality
This can run without FastAPI dependencies
"""

import http.server
import socketserver
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.model_routes import model_selector

class ModelAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            # Serve the main HTML file
            self.serve_file('static/index.html', 'text/html')
        elif path.startswith('/static/'):
            # Serve static files
            file_path = path[1:]  # Remove leading slash
            if os.path.exists(file_path):
                if file_path.endswith('.html'):
                    self.serve_file(file_path, 'text/html')
                elif file_path.endswith('.css'):
                    self.serve_file(file_path, 'text/css')
                elif file_path.endswith('.js'):
                    self.serve_file(file_path, 'application/javascript')
                else:
                    super().do_GET()
            else:
                self.send_error(404)
        elif path.startswith('/ai/models'):
            # Handle model API endpoints
            if path == '/ai/models':
                self.handle_list_models()
            elif path.startswith('/ai/models/'):
                model_name = path.split('/')[-1]
                self.handle_get_model_info(model_name)
            else:
                self.send_error(404)
        elif path.startswith('/models/'):
            # Serve 3D model files
            model_name = path.split('/')[-1]
            self.serve_model_file(model_name)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/ai/select_model':
            self.handle_select_model()
        else:
            self.send_error(404)
    
    def serve_file(self, file_path, content_type):
        """Serve a file with specified content type"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', str(len(content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404)
    
    def serve_model_file(self, model_name):
        """Serve 3D model files"""
        try:
            model_info = model_selector.get_model_info(model_name)
            file_path = model_info["path"]
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Content-Disposition', f'attachment; filename="{model_name}"')
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)
        except Exception as e:
            print(f"Error serving model file: {e}")
            self.send_error(500)
    
    def handle_list_models(self):
        """Handle /ai/models endpoint"""
        try:
            models = model_selector.list_available_models()
            response = {
                "models": models,
                "count": len(models),
                "status": "success"
            }
            self.send_json_response(response)
        except Exception as e:
            self.send_json_response({"error": str(e), "status": "error"}, 500)
    
    def handle_get_model_info(self, model_name):
        """Handle /ai/models/{model_name} endpoint"""
        try:
            model_info = model_selector.get_model_info(model_name)
            response = {
                "model": model_info,
                "status": "success"
            }
            self.send_json_response(response)
        except FileNotFoundError:
            self.send_json_response({"error": f"Model {model_name} not found", "status": "not_found"}, 404)
        except Exception as e:
            self.send_json_response({"error": str(e), "status": "error"}, 500)
    
    def handle_select_model(self):
        """Handle /ai/select_model endpoint"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            question = request_data.get("question", "")
            language = request_data.get("language", "en")
            
            if not question:
                raise ValueError("Question is required")
            
            result = model_selector.analyze_question(question)
            
            response = {
                "question": question,
                "language": language,
                "model_selection": result,
                "status": "success"
            }
            self.send_json_response(response)
        except Exception as e:
            self.send_json_response({"error": str(e), "status": "error"}, 500)
    
    def send_json_response(self, data, status_code=200):
        """Send a JSON response"""
        response_data = json.dumps(data, indent=2)
        
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(response_data.encode('utf-8'))))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(response_data.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    PORT = 8000
    
    print(f"🚀 Starting PaiNaiDee AI Assistant Server...")
    print(f"📡 Server running at: http://localhost:{PORT}")
    print(f"🌐 Open in browser: http://localhost:{PORT}")
    print(f"📁 Models directory: {model_selector.models_dir}")
    print(f"🎯 Available models: {len(model_selector.list_available_models())}")
    print("=" * 60)
    
    with socketserver.TCPServer(("", PORT), ModelAPIHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")

if __name__ == "__main__":
    main()