"""
公共卫生考研成绩排名系统 - Flask 后端
依赖安装: pip install flask flask-cors
运行: python app.py
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import time
import hashlib

app = Flask(__name__, static_folder='static')
CORS(app)

DB_PATH = 'scores.db'

# ============================================================
# 管理员密码配置（建议部署后修改）
# ============================================================
ADMIN_PASSWORD = 'pku2024'  # ← 修改这里


def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()


ADMIN_HASH = hash_pwd(ADMIN_PASSWORD)


# ============================================================
# 数据库初始化
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nick    TEXT    NOT NULL,
            school  TEXT    NOT NULL,
            s1      REAL    NOT NULL,
            s2      REAL    NOT NULL,
            s3      REAL    NOT NULL,
            total   REAL    NOT NULL,
            note    TEXT    DEFAULT '',
            created INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


init_db()


# ============================================================
# 工具函数
# ============================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    return {
        'id':      row['id'],
        'nick':    row['nick'],
        'school':  row['school'],
        's1':      row['s1'],
        's2':      row['s2'],
        's3':      row['s3'],
        'total':   row['total'],
        'note':    row['note'],
        'created': row['created'],
    }


# ============================================================
# API 路由
# ============================================================

# 获取所有成绩
@app.route('/api/scores', methods=['GET'])
def get_scores():
    conn = get_db()
    rows = conn.execute('SELECT * FROM scores ORDER BY total DESC').fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])


# 添加成绩
@app.route('/api/scores', methods=['POST'])
def add_score():
    data = request.get_json()
    nick   = str(data.get('nick', '')).strip()
    school = str(data.get('school', '')).strip()
    note   = str(data.get('note', '')).strip()

    try:
        s1 = float(data.get('s1'))
        s2 = float(data.get('s2'))
        s3 = float(data.get('s3'))
    except (TypeError, ValueError):
        return jsonify({'error': '成绩格式错误'}), 400

    if not nick:
        return jsonify({'error': '昵称不能为空'}), 400
    if not school:
        return jsonify({'error': '院校不能为空'}), 400
    if not (0 <= s1 <= 100):
        return jsonify({'error': '政治成绩应在 0-100 之间'}), 400
    if not (0 <= s2 <= 100):
        return jsonify({'error': '英语成绩应在 0-100 之间'}), 400
    if not (0 <= s3 <= 300):
        return jsonify({'error': '353综合应在 0-300 之间'}), 400

    total = s1 + s2 + s3
    created = int(time.time() * 1000)

    conn = get_db()
    conn.execute(
        'INSERT INTO scores (nick, school, s1, s2, s3, total, note, created) VALUES (?,?,?,?,?,?,?,?)',
        (nick, school, s1, s2, s3, total, note, created)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True}), 201


# 删除成绩（需要管理员密码）
@app.route('/api/scores/<int:score_id>', methods=['DELETE'])
def delete_score(score_id):
    data = request.get_json() or {}
    pwd  = str(data.get('password', ''))

    if hash_pwd(pwd) != ADMIN_HASH:
        return jsonify({'error': '管理员密码错误'}), 403

    conn = get_db()
    result = conn.execute('DELETE FROM scores WHERE id = ?', (score_id,))
    conn.commit()
    conn.close()

    if result.rowcount == 0:
        return jsonify({'error': '记录不存在'}), 404
    return jsonify({'ok': True})


# 清空所有数据（需要管理员密码）
@app.route('/api/scores/all', methods=['DELETE'])
def clear_all():
    data = request.get_json() or {}
    pwd  = str(data.get('password', ''))

    if hash_pwd(pwd) != ADMIN_HASH:
        return jsonify({'error': '管理员密码错误'}), 403

    conn = get_db()
    conn.execute('DELETE FROM scores')
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


# 前端页面（优先从当前目录提供 index.html，否则从 static/）
@app.route('/')
def index():
    if os.path.isfile('index.html'):
        return send_from_directory('.', 'index.html')
    return send_from_directory('static', 'index.html')


# ============================================================
# 启动
# ============================================================
if __name__ == '__main__':
    # 生产环境请用 gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app
    # 本地用 5001 避免与 macOS AirPlay 占用的 5000 冲突
    app.run(host='0.0.0.0', port=5001, debug=False)
