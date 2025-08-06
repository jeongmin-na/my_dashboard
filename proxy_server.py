#!/usr/bin/env python3
"""
향상된 Cursor Admin API 프록시 서버
- 실제 API 호출 실패 시 자동으로 Mock 데이터 제공
- 개발 환경에서 안정적인 테스트 가능
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
import platform
from datetime import datetime, timedelta
import random

def generate_mock_members():
    """Mock 멤버 데이터 생성"""
    members = [
        {
            "id": 1,
            "name": "김철수",
            "email": "kim.cheolsu@company.com",
            "usage": 245,
            "lastActive": "2025-08-06T09:30:00Z",
            "role": "Senior Developer",
            "tokensUsed": 15420,
            "sessionsCount": 23
        },
        {
            "id": 2,
            "name": "이영희", 
            "email": "lee.younghee@company.com",
            "usage": 189,
            "lastActive": "2025-08-06T11:15:00Z",
            "role": "Product Manager",
            "tokensUsed": 12350,
            "sessionsCount": 18
        },
        {
            "id": 3,
            "name": "박민수",
            "email": "park.minsu@company.com", 
            "usage": 156,
            "lastActive": "2025-08-05T16:45:00Z",
            "role": "Frontend Developer",
            "tokensUsed": 9680,
            "sessionsCount": 15
        },
        {
            "id": 4,
            "name": "최수정",
            "email": "choi.sujeong@company.com",
            "usage": 298,
            "lastActive": "2025-08-06T14:20:00Z", 
            "role": "Team Lead",
            "tokensUsed": 18970,
            "sessionsCount": 31
        },
        {
            "id": 5,
            "name": "정현우",
            "email": "jung.hyunwoo@company.com",
            "usage": 134,
            "lastActive": "2025-08-06T08:10:00Z",
            "role": "Backend Developer", 
            "tokensUsed": 8240,
            "sessionsCount": 12
        }
    ]
    return members

def generate_mock_events(start_date, end_date, count=100):
    """Mock 이벤트 데이터 생성"""
    events = []
    activities = ['chat', 'autocomplete', 'edit', 'debug', 'refactor', 'generate']
    members = generate_mock_members()
    
    for i in range(count):
        # 시작일과 종료일 사이의 랜덤 날짜 생성
        time_between = end_date - start_date
        random_seconds = random.randint(0, int(time_between.total_seconds()))
        random_date = start_date + timedelta(seconds=random_seconds)
        
        member = random.choice(members)
        
        events.append({
            "id": f"event_{i}",
            "userId": member["id"],
            "userName": member["name"],
            "timestamp": random_date.isoformat() + "Z",
            "activity": random.choice(activities),
            "duration": random.randint(30, 300),
            "tokensUsed": random.randint(50, 500),
            "model": random.choice(['cursor-small', 'cursor-medium', 'cursor-large']),
            "cost": round(random.random() * 2, 4)
        })
    
    return sorted(events, key=lambda x: x['timestamp'], reverse=True)

class EnhancedCursorAPIProxy(http.server.SimpleHTTPRequestHandler):
    """향상된 Cursor API 프록시 핸들러 - Mock 데이터 지원"""
    
    def __init__(self, *args, **kwargs):
        self.api_key = "key_e46368ce482125bbd568b7d55090c657e30e4b73c824f522cbc9ef9b1bf3f0d3"
        self.base_url = "https://api.cursor.com"
        self.use_mock_data = os.environ.get('USE_MOCK_DATA', 'true').lower() == 'true'
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """로그 메시지 포맷 개선"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{self.address_string()}] {format % args}")
    
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
        elif self.path == '/':
            # 루트 경로 접속 시 dash.html로 리다이렉트
            self.send_response(302)
            self.send_header('Location', '/dash.html')
            self.end_headers()
        elif self.path == '/health':
            # 헬스체크 엔드포인트
            self.send_json_response({'status': 'ok', 'message': 'Proxy server is running'})
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
        """API 요청 처리 - 실패 시 Mock 데이터 제공"""
        try:
            # Mock 데이터 모드가 활성화된 경우 바로 Mock 데이터 반환
            if self.use_mock_data:
                print(f"🔄 Mock 모드: {method} {self.path}")
                self.handle_mock_request(method)
                return
            
            # 실제 API 호출 시도
            response_data = self.call_real_api(method)
            
            if response_data:
                print(f"✅ 실제 API 응답 성공: {method} {self.path}")
                self.send_json_response(response_data)
            else:
                raise Exception("API 응답 없음")
                
        except Exception as e:
            print(f"⚠️ 실제 API 호출 실패, Mock 데이터로 대체: {e}")
            self.handle_mock_request(method)
    
    def call_real_api(self, method):
        """실제 API 호출"""
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
        
        # SSL 컨텍스트 설정
        ssl_context = ssl.create_default_context()
        
        # API 호출
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            response_data = response.read()
            return json.loads(response_data.decode())
    
    def handle_mock_request(self, method):
        """Mock 데이터 요청 처리"""
        if '/teams/members' in self.path:
            # 멤버 데이터 Mock
            members = generate_mock_members()
            self.send_json_response(members)
            
        elif '/teams/filtered-usage-events' in self.path:
            # 이벤트 데이터 Mock
            if method == 'POST':
                # POST 데이터 읽기
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = {}
                if content_length > 0:
                    post_body = self.rfile.read(content_length)
                    post_data = json.loads(post_body.decode())
                
                # 날짜 범위 파싱
                start_date = datetime.fromtimestamp(post_data.get('startDate', time.time() - 30*24*60*60) / 1000)
                end_date = datetime.fromtimestamp(post_data.get('endDate', time.time()) / 1000)
                page_size = post_data.get('pageSize', 100)
                
                # Mock 이벤트 생성
                events = generate_mock_events(start_date, end_date, page_size)
                
                response_data = {
                    "events": events,
                    "totalPages": 1,
                    "currentPage": post_data.get('page', 1),
                    "totalEvents": len(events),
                    "statistics": {
                        "totalMembers": 5,
                        "activeMembers": 4,
                        "totalTokensUsed": sum(e['tokensUsed'] for e in events),
                        "averageTokensPerEvent": sum(e['tokensUsed'] for e in events) // len(events) if events else 0
                    }
                }
                
                self.send_json_response(response_data)
            else:
                self.send_json_response([])
        else:
            # 기본 빈 응답
            self.send_json_response([])
    
    def send_json_response(self, data):
        """JSON 응답 전송"""
        response_json = json.dumps(data, ensure_ascii=False)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_json.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(response_json.encode('utf-8'))

def run_enhanced_proxy_server(port=8001):
    """향상된 프록시 서버 실행"""
    try:
        with socketserver.TCPServer(("", port), EnhancedCursorAPIProxy) as httpd:
            mock_status = "활성화" if os.environ.get('USE_MOCK_DATA', 'true').lower() == 'true' else "비활성화"
            print(f"🚀 향상된 Cursor API 프록시 서버가 포트 {port}에서 실행 중입니다...")
            print(f"📊 대시보드 접속: http://localhost:{port}/dash.html")
            print(f"🔧 Mock 데이터 모드: {mock_status}")
            print("🛑 서버를 중지하려면 Ctrl+C를 누르세요.")
            print("=" * 60)
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n🛑 서버를 중지합니다...")
                httpd.shutdown()
                
    except OSError as e:
        if e.errno == 48 or "Address already in use" in str(e):
            print(f"❌ 포트 {port}가 이미 사용 중입니다.")
            print("🔧 기존 프로세스를 종료하고 다시 시도합니다...")
            kill_existing_proxy_servers()
            time.sleep(2)
            run_enhanced_proxy_server(port)
        else:
            print(f"❌ 서버 시작 실패: {e}")
            raise

def kill_existing_proxy_servers():
    """기존 프록시 서버 프로세스들을 찾아서 종료"""
    try:
        system = platform.system()
        
        if system == "Windows":
            # Windows에서 포트 8001 사용 중인 프로세스 찾기
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, shell=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if ':8001' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        print(f"🔍 포트 8001에서 실행 중인 프로세스 발견: PID {pid}")
                        
                        # 프로세스 종료
                        kill_result = subprocess.run(['taskkill', '/PID', pid, '/F'], 
                                                  capture_output=True, text=True, shell=True)
                        if kill_result.returncode == 0:
                            print(f"✅ 프로세스 {pid} 종료 완료")
                        else:
                            print(f"⚠️ 프로세스 {pid} 종료 실패")
        else:
            # Linux/macOS에서 포트 8001 사용 중인 프로세스 찾기
            try:
                result = subprocess.run(['lsof', '-ti:8001'], capture_output=True, text=True)
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid:
                            print(f"🔍 포트 8001에서 실행 중인 프로세스 발견: PID {pid}")
                            kill_result = subprocess.run(['kill', '-9', pid], capture_output=True, text=True)
                            if kill_result.returncode == 0:
                                print(f"✅ 프로세스 {pid} 종료 완료")
                            else:
                                print(f"⚠️ 프로세스 {pid} 종료 실패")
            except FileNotFoundError:
                print("⚠️ lsof 명령어를 찾을 수 없습니다.")
        
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
        # 현재 스크립트를 백그라운드에서 프록시 서버로 실행
        proxy_process = subprocess.Popen([sys.executable, __file__, '--proxy-only'],
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
    print("🔧 Mock 데이터 모드 제어:")
    print("   • Mock 모드 활성화: USE_MOCK_DATA=true python proxy_server.py")
    print("   • 실제 API 모드: USE_MOCK_DATA=false python proxy_server.py")
    print("=" * 60)
    print("🛑 서버를 중지하려면 Ctrl+C를 누르세요.")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    # 명령행 인수 확인
    if len(sys.argv) > 1:
        if sys.argv[1] == "--start-dashboard":
            # 대시보드 실행 프로토콜 실행
            success = start_dashboard()
            if success:
                # 대시보드 시작 후 메인 프로세스는 대기
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 대시보드를 종료합니다...")
        elif sys.argv[1] == "--proxy-only":
            # 프록시 서버만 실행
            run_enhanced_proxy_server()
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("🚀 Cursor Admin API 프록시 서버")
            print("=" * 50)
            print("사용법:")
            print("  python proxy_server.py --start-dashboard  # 대시보드 자동 실행")
            print("  python proxy_server.py --proxy-only       # 프록시 서버만 실행")
            print("  python proxy_server.py                    # 기본 프록시 서버 실행")
            print("")
            print("환경변수:")
            print("  USE_MOCK_DATA=true   # Mock 데이터 모드 (기본값)")
            print("  USE_MOCK_DATA=false  # 실제 API 호출 모드")
            print("")
            print("예시:")
            print("  USE_MOCK_DATA=true python proxy_server.py")
            print("  USE_MOCK_DATA=false python proxy_server.py --start-dashboard")
        else:
            print("❌ 알 수 없는 옵션입니다. --help를 사용하여 도움말을 확인하세요.")
    else:
        # 일반적인 프록시 서버 실행
        print("🔧 기본 모드로 프록시 서버를 시작합니다...")
        run_enhanced_proxy_server()
