#!/usr/bin/env python3
"""飞书 Base API 代理服务器 —— 供 题库预览.html 调用"""

import json, subprocess, os, sys, time, http.server, urllib.parse, mimetypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
BASES_FILE = os.path.join(OUTPUT_DIR, 'bases.json')

# 要读取的字段列表（与 html 中一致）
FIELDS = [
    "题干", "题型", "年级", "学期", "来源", "页码",
    "选项", "答案", "解析", "有确定解", "难度",
    "知识点标签", "思想标签", "模型标签",
]

def load_bases():
    with open(BASES_FILE, 'r') as f:
        return json.load(f).get('bases', {})

def fetch_all_records(base_token, table_id):
    """从飞书 Base 拉取全部记录，处理分页"""
    all_data = []
    offset = 0
    limit = 200

    while True:
        cmd = [
            'lark-cli', 'base', '+record-list',
            '--base-token', base_token,
            '--table-id', table_id,
            '--format', 'json',
            '--as', 'user',
            '--limit', str(limit),
            '--offset', str(offset),
        ]
        for f in FIELDS:
            cmd += ['--field-id', f]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None, f"lark-cli error: {result.stderr}"

        resp = json.loads(result.stdout)
        if not resp.get('ok'):
            return None, resp.get('error', 'unknown error')

        data = resp['data']
        records = data.get('data', [])
        fields = data.get('fields', FIELDS)
        all_data.extend(records)

        if not data.get('has_more'):
            break
        offset += limit
        time.sleep(0.3)

    return all_data, fields

def decode_path(path):
    return urllib.parse.unquote(path.split('?')[0])

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = decode_path(self.path)

        if path == '/api/bases':
            self._json(load_bases())
            return

        if path.startswith('/api/questions/'):
            base_name = urllib.parse.unquote(self.path[len('/api/questions/'):].split('?')[0])
            bases = load_bases()
            if base_name not in bases:
                self._error(404, f'Base not found: {base_name}')
                return

            info = bases[base_name]
            base_token = info.get('base_token')
            # 找 base-info.json 拿 table_id
            base_info_file = os.path.join(OUTPUT_DIR, base_name, 'base-info.json')
            if not os.path.exists(base_info_file):
                self._error(404, 'base-info.json not found')
                return
            with open(base_info_file) as f:
                bi = json.load(f)
            table_id = bi.get('qb_table_id')
            if not table_id:
                self._error(404, 'qb_table_id not found')
                return

            records, fields = fetch_all_records(base_token, table_id)
            if records is None:
                self._error(500, fields)
                return

            self._json({'fields': fields, 'records': records})
            return

        if path == '/' or path.endswith('/题库预览.html') or path.endswith('/index.html'):
            filename = '题库预览.html' if '题库预览' in path else 'index.html'
            file_path = os.path.join(BASE_DIR, filename)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self._error(404, 'HTML not found')
            return

        # static files (images, etc.)
        rel = path.lstrip('/')
        file_path = os.path.normpath(os.path.join(BASE_DIR, rel))
        if file_path.startswith(BASE_DIR) and os.path.isfile(file_path):
            ct = 'application/octet-stream'
            if file_path.endswith('.jpg') or file_path.endswith('.jpeg'): ct = 'image/jpeg'
            elif file_path.endswith('.png'): ct = 'image/png'
            elif file_path.endswith('.gif'): ct = 'image/gif'
            elif file_path.endswith('.svg'): ct = 'image/svg+xml'
            elif file_path.endswith('.css'): ct = 'text/css'
            elif file_path.endswith('.js'): ct = 'application/javascript'
            with open(file_path, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', ct)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self._error(404, 'Not found')

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code, msg):
        self._json({'error': str(msg)}, code)

    def log_message(self, fmt, *args):
        print(fmt % args, file=sys.stderr)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
    server = http.server.HTTPServer(('0.0.0.0', port), ProxyHandler)
    print(f'Proxy server at http://localhost:{port}')
    server.serve_forever()
