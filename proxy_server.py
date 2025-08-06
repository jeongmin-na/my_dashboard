#!/usr/bin/env python3
"""
Cursor Admin API 프록시 서버
CORS 문제를 해결하고 실제 API 호출을 중계합니다.
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import base64
from urllib.error import HTTPError, URLError
import ssl

class CursorAPIProxy(http.server.SimpleHTTPRequestHandler):
    """Cursor Admin API 프록시 핸들러"""
    
    def __init__(self, *args, **kwargs):
        self.api_key = "key_e46368ce482125bbd568b7d55090c657e30e4b73c824f522cbc9ef9b1bf3f0d3"
        self.base_url = "https://api.cursor.com"
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        """CORS preflight 요청 처리"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def do_GET(self):
        """GET 요청 처리"""
        if self.path.startswith('/teams/'):
            self.handle_api_request('GET')
        else:
            # 정적 파일 서빙
            super().do_GET()
    
    def do_POST(self):
        """POST 요청 처리"""
        if self.path.startswith('/teams/'):
            self.handle_api_request('POST')
        else:
            self.send_error(404, "Not Found")
    
    def handle_api_request(self, method):
        """API 요청 처리"""
        try:
            # 요청 본문 읽기
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = None
            if content_length > 0:
                post_data = self.rfile.read(content_length)
            
            # API 요청 생성
            url = f"{self.base_url}{self.path}"
            
            # Basic Auth 설정
            credentials = f"{self.api_key}:"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {encoded_credentials}'
            }
            
            # 요청 생성
            if method == 'GET':
                req = urllib.request.Request(url, headers=headers)
            else:  # POST
                req = urllib.request.Request(url, data=post_data, headers=headers, method='POST')
            
            print(f"프록시 요청: {method} {url}")
            if post_data:
                print(f"요청 데이터: {post_data.decode()}")
            
            # API 호출
            with urllib.request.urlopen(req) as response:
                response_data = response.read()
                response_headers = response.headers
                
                print(f"API 응답: {response.status}")
                print(f"응답 데이터: {response_data.decode()[:200]}...")
                
                # CORS 헤더 추가
                self.send_response(response.status)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                
                # 원본 응답 헤더 복사
                for header, value in response_headers.items():
                    if header.lower() not in ['transfer-encoding', 'connection']:
                        self.send_header(header, value)
                
                self.end_headers()
                self.wfile.write(response_data)
                
        except HTTPError as e:
            print(f"HTTP 에러: {e.code} - {e.reason}")
            error_response = {
                'error': 'HTTP Error',
                'code': e.code,
                'message': e.reason
            }
            self.send_error_response(500, json.dumps(error_response))
            
        except URLError as e:
            print(f"URL 에러: {e.reason}")
            error_response = {
                'error': 'Connection Error',
                'message': str(e.reason)
            }
            self.send_error_response(500, json.dumps(error_response))
            
        except Exception as e:
            print(f"예상치 못한 에러: {e}")
            error_response = {
                'error': 'Internal Server Error',
                'message': str(e)
            }
            self.send_error_response(500, json.dumps(error_response))
    
    def send_error_response(self, status_code, error_data):
        """에러 응답 전송"""
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(error_data.encode())

def run_proxy_server(port=8001):
    """프록시 서버 실행"""
    with socketserver.TCPServer(("", port), CursorAPIProxy) as httpd:
        print(f"🚀 Cursor API 프록시 서버가 포트 {port}에서 실행 중입니다...")
        print(f"📊 대시보드 접속: http://localhost:{port}/dash.html")
        print("🛑 서버를 중지하려면 Ctrl+C를 누르세요.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 서버를 중지합니다...")
            httpd.shutdown()

if __name__ == "__main__":
    run_proxy_server() 
