#!/usr/bin/env python3
"""
Cursor Admin API 프록시 서버
CORS 문제를 해결하고 실제 API 호출을 중계합니다.

🚨 포트 설정 규칙 (MANDATORY)
- 프록시 서버: 포트 8001 고정
- dash.html: localhost:8001 고정
- 이 설정을 변경하면 안 됩니다!
- 모든 개발자는 이 규칙을 따라야 합니다!

🚀 대시보드 실행 프로토콜 (MANDATORY)
사용자가 "대시보드 실행"을 요청하면 다음 순서로 자동 실행:
1. 기존 프록시 서버 프로세스 찾아서 종료
2. 프록시 서버 포트 8001로 재시작
3. localhost:8001/dash.html 접속 안내
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import base64
from urllib.error import HTTPError, URLError
import ssl
import subprocess
import os
import sys
import time

def kill_existing_proxy_servers():
    """기존 프록시 서버 프로세스들을 찾아서 종료"""
    try:
        # Windows에서 포트 8001 사용 중인 프로세스 찾기
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if ':8001' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    print(f"🔍 포트 8001에서 실행 중인 프로세스 발견: PID {pid}")
                    
                    # 프로세스 종료
                    kill_result = subprocess.run(['taskkill', '/PID', pid, '/F'], 
                                              capture_output=True, text=True)
                    if kill_result.returncode == 0:
                        print(f"✅ 프로세스 {pid} 종료 완료")
                    else:
                        print(f"⚠️ 프로세스 {pid} 종료 실패: {kill_result.stderr}")
        
        # Python 프로세스 중 프록시 서버 관련 프로세스 확인
        python_result = subprocess.run(['tasklist'], capture_output=True, text=True)
        python_lines = python_result.stdout.split('\n')
        
        for line in python_lines:
            if 'python' in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    print(f"🔍 Python 프로세스 발견: PID {pid}")
                    
                    # 안전하게 종료 (강제 종료는 마지막 수단)
                    kill_result = subprocess.run(['taskkill', '/PID', pid, '/F'], 
                                              capture_output=True, text=True)
                    if kill_result.returncode == 0:
                        print(f"✅ Python 프로세스 {pid} 종료 완료")
        
        print("🔄 기존 프로세스 정리 완료")
        time.sleep(2)  # 프로세스 종료 대기
        
    except Exception as e:
        print(f"⚠️ 프로세스 정리 중 오류: {e}")

def start_dashboard():
    """대시보드 실행 프로토콜 - 자동화된 실행"""
    print("🚀 Samsung AI Experience Group 대시보드 실행을 시작합니다...")
    
    # 1단계: 기존 프록시 서버 프로세스 종료
    print("\n1️⃣ 기존 프록시 서버 프로세스 정리 중...")
    kill_existing_proxy_servers()
    
    # 2단계: 프록시 서버 포트 8001로 재시작
    print("\n2️⃣ 프록시 서버를 포트 8001로 시작 중...")
    try:
        # 백그라운드에서 프록시 서버 시작
        proxy_process = subprocess.Popen([sys.executable, 'proxy_server.py'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        
        # 서버 시작 대기
        time.sleep(3)
        
        if proxy_process.poll() is None:
            print("✅ 프록시 서버가 성공적으로 시작되었습니다!")
        else:
            print("❌ 프록시 서버 시작 실패")
            return False
            
    except Exception as e:
        print(f"❌ 프록시 서버 시작 중 오류: {e}")
        return False
    
    # 3단계: 대시보드 접속 안내
    print("\n3️⃣ 대시보드 접속 준비 완료!")
    print("=" * 60)
    print("🎯 대시보드 접속 방법:")
    print("🌐 브라우저에서 다음 URL로 접속하세요:")
    print("   http://localhost:8001/dash.html")
    print("=" * 60)
    print("📊 대시보드 기능:")
    print("   • Overview: 팀 활동 통계")
    print("   • Members: 멤버 관리")
    print("   • Usage: 사용량 분석")
    print("   • Settings: 설정 관리")
    print("=" * 60)
    print("🛑 서버를 중지하려면 Ctrl+C를 누르세요.")
    print("=" * 60)
    
    return True

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
    """프록시 서버 실행
    
    🚨 중요: 포트는 항상 8001로 고정되어야 합니다.
    - 프록시 서버: 포트 8001
    - dash.html: localhost:8001
    - 이 설정을 변경하면 안 됩니다!
    """
    with socketserver.TCPServer(("", port), CursorAPIProxy) as httpd:
        print(f"🚀 Cursor API 프록시 서버가 포트 {port}에서 실행 중입니다...")
        print(f"📊 대시보드 접속: http://localhost:{port}/dash.html")
        print("🛑 서버를 중지하려면 Ctrl+C를 누르세요.")
        print("⚠️  포트 설정: 프록시 서버와 dash.html은 항상 포트 8001 사용")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 서버를 중지합니다...")
            httpd.shutdown()

if __name__ == "__main__":
    # 명령행 인수 확인
    if len(sys.argv) > 1 and sys.argv[1] == "--start-dashboard":
        # 대시보드 실행 프로토콜 실행
        start_dashboard()
    else:
        # 일반적인 프록시 서버 실행
        run_proxy_server() 
