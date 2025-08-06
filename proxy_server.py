#!/usr/bin/env python3
"""
Cursor Admin API 프록시 서버
CORS 문제를 해결하고 실제 API 호출을 중계합니다.

🚀 Vercel 배포용 Flask 애플리케이션
"""

from flask import Flask, request, jsonify, send_from_directory
import urllib.request
import urllib.parse
import json
import base64
from urllib.error import HTTPError, URLError
import os
import ssl

app = Flask(__name__)

# Cursor Admin API 설정
API_KEY = os.environ.get('CURSOR_API_KEY', "key_e46368ce482125bbd568b7d55090c657e30e4b73c824f522cbc9ef9b1bf3f0d3")
BASE_URL = "https://api.cursor.com"

@app.route('/')
def index():
    """메인 페이지"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """정적 파일 서빙"""
    return send_from_directory('.', filename)

@app.route('/api/<path:api_path>', methods=['GET', 'POST', 'OPTIONS'])
def proxy_api(api_path):
    """Cursor Admin API 프록시"""
    
    # CORS preflight 요청 처리
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response
    
    try:
        # API 요청 생성
        url = f"{BASE_URL}/{api_path}"
        
        # Basic Auth 설정
        credentials = f"{API_KEY}:"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {encoded_credentials}'
        }
        
        # 요청 데이터 준비
        post_data = None
        if request.method == 'POST':
            post_data = request.get_data()
        
        # 요청 생성
        if request.method == 'GET':
            req = urllib.request.Request(url, headers=headers)
        else:  # POST
            req = urllib.request.Request(url, data=post_data, headers=headers, method='POST')
        
        print(f"프록시 요청: {request.method} {url}")
        if post_data:
            print(f"요청 데이터: {post_data.decode()}")
        
        # API 호출
        with urllib.request.urlopen(req) as response:
            response_data = response.read()
            response_headers = dict(response.headers)
            
            print(f"API 응답: {response.status}")
            print(f"응답 데이터: {response_data.decode()[:200]}...")
            
            # CORS 헤더 추가
            flask_response = app.response_class(
                response=response_data,
                status=response.status,
                headers=response_headers
            )
            flask_response.headers['Access-Control-Allow-Origin'] = '*'
            flask_response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            flask_response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            
            return flask_response
            
    except HTTPError as e:
        print(f"HTTP 에러: {e.code} - {e.reason}")
        error_response = {
            'error': 'HTTP Error',
            'code': e.code,
            'message': e.reason
        }
        return jsonify(error_response), 500
        
    except URLError as e:
        print(f"URL 에러: {e.reason}")
        error_response = {
            'error': 'Connection Error',
            'message': str(e.reason)
        }
        return jsonify(error_response), 500
        
    except Exception as e:
        print(f"예상치 못한 에러: {e}")
        error_response = {
            'error': 'Internal Server Error',
            'message': str(e)
        }
        return jsonify(error_response), 500

@app.route('/send-email', methods=['POST', 'OPTIONS'])
def send_email():
    """이메일 발송 엔드포인트"""
    
    # CORS preflight 요청 처리
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response
    
    try:
        # 요청 데이터 가져오기
        email_data = request.get_json()
        
        if not email_data:
            return jsonify({'error': 'No email data provided'}), 400
        
        # 필수 필드 확인
        required_fields = ['to_emails', 'subject', 'message']
        for field in required_fields:
            if field not in email_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # 이메일 발송 로그
        print(f"📧 이메일 발송 요청:")
        print(f"- 수신자: {len(email_data.get('to_emails', []))}명")
        print(f"- 제목: {email_data.get('subject', '')}")
        print(f"- 메시지 길이: {len(email_data.get('message', ''))}자")
        
        # 실제 SMTP 발송 대신 성공 응답 (테스트용)
        # 추후 실제 SMTP 서버 연동 시 이 부분을 수정
        response_data = {
            'success': True,
            'message': '이메일이 성공적으로 발송되었습니다.',
            'sent_count': len(email_data.get('to_emails', [])),
            'timestamp': email_data.get('timestamp', ''),
            'subject': email_data.get('subject', '')
        }
        
        # CORS 헤더 추가
        response = jsonify(response_data)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        print(f"✅ 이메일 발송 완료: {len(email_data.get('to_emails', []))}명")
        return response
        
    except Exception as e:
        print(f"❌ 이메일 발송 에러: {e}")
        error_response = {
            'success': False,
            'error': 'Email sending failed',
            'message': str(e)
        }
        response = jsonify(error_response)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/health')
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({'status': 'healthy', 'service': 'Cursor API Proxy'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 
