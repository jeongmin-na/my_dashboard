#!/usr/bin/env python3
"""
Samsung AI Experience Group Dashboard - Vercel 배포용
Flask 기반 웹 애플리케이션으로 대시보드를 제공합니다.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import base64
from urllib.error import HTTPError, URLError
import ssl
import os

app = Flask(__name__)
CORS(app)  # CORS 활성화

# 환경 변수에서 API 키 가져오기
CURSOR_API_KEY = os.environ.get('CURSOR_API_KEY', '')

class CursorAPIProxy:
    """Cursor Admin API 프록시 클래스"""
    
    def __init__(self):
        self.base_url = "https://api.cursor.sh"
        self.api_key = CURSOR_API_KEY
    
    def handle_api_request(self, method, path, data=None):
        """API 요청을 처리하고 응답을 반환합니다."""
        try:
            # API 엔드포인트 구성
            url = f"{self.base_url}{path}"
            
            # 헤더 설정
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            # 요청 데이터 준비
            request_data = None
            if data:
                request_data = json.dumps(data)
            
            # API 요청 실행
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, data=request_data, timeout=30)
            else:
                return {'error': '지원하지 않는 HTTP 메서드입니다.'}, 405
            
            # 응답 처리
            if response.status_code == 200:
                try:
                    return response.json(), 200
                except json.JSONDecodeError:
                    return {'data': response.text}, 200
            else:
                return {'error': f'API 오류: {response.status_code}'}, response.status_code
                
        except requests.exceptions.RequestException as e:
            return {'error': f'네트워크 오류: {str(e)}'}, 500
        except Exception as e:
            return {'error': f'서버 오류: {str(e)}'}, 500

# API 프록시 인스턴스 생성
api_proxy = CursorAPIProxy()

@app.route('/')
def index():
    """메인 대시보드 페이지"""
    return send_from_directory('.', 'index.html')

@app.route('/api/<path:subpath>', methods=['GET', 'POST', 'OPTIONS'])
def api_proxy_route(subpath):
    """API 프록시 엔드포인트"""
    if request.method == 'OPTIONS':
        # CORS preflight 요청 처리
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
    
    # API 요청 처리
    method = request.method
    path = f"/{subpath}"
    
    # POST 요청의 경우 데이터 추출
    data = None
    if method == 'POST' and request.is_json:
        data = request.get_json()
    
    # API 프록시를 통해 요청 처리
    result, status_code = api_proxy.handle_api_request(method, path, data)
    
    response = jsonify(result)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, status_code

@app.route('/health')
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'service': 'Samsung AI Experience Group Dashboard',
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found(error):
    """404 오류 처리"""
    return jsonify({'error': '페이지를 찾을 수 없습니다.'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500 오류 처리"""
    return jsonify({'error': '서버 내부 오류가 발생했습니다.'}), 500

if __name__ == '__main__':
    # 개발 환경에서만 실행
    app.run(debug=True, host='0.0.0.0', port=8001) 
