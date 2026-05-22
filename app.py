from flask import Flask, render_template, request, jsonify, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
# env
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()  # .env 파일 로드

app.secret_key = os.getenv('SECRET_KEY')

# MySQL 설정 (환경에 맞게 수정)
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def init_db():
    """앱 구동 시 자동으로 DB 및 테이블 생성 (DDL)"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']} DEFAULT CHARACTER SET utf8mb4")
        cursor.close()
        conn.close()

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        # 사용자 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(50) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # 게시글 테이블 (작성자 연결)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("💡 DB 초기화 완료")
    except Exception as e:
        print(f"❌ DB 초기화 실패: {e}")

def get_db():
    return mysql.connector.connect(**db_config)

@app.route('/')
def home():
    return render_template('index.html')

# --- AUTH API ---
@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'name': session['name'], 'id': session['user_id']})
    return jsonify({'logged_in': False})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (data.get('username'),))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and check_password_hash(user['password'], data.get('password')):
        session['user_id'] = user['id']
        session['name'] = user['name']
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '계정 정보가 일치하지 않습니다.'}), 401

@app.route('/api/auth/join', methods=['POST'])
def join():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    try:
        hashed_pw = generate_password_hash(data.get('password'))
        cursor.execute("INSERT INTO users (username, password, name) VALUES (%s, %s, %s)", 
                       (data.get('username'), hashed_pw, data.get('name')))
        conn.commit()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False, 'message': '이미 존재하는 아이디입니다.'}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

# --- CRUD API ---
@app.route('/api/posts', methods=['GET'])
def get_posts():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.id, p.title, u.name as author, DATE_FORMAT(p.created_at, '%Y-%m-%d') as date 
        FROM posts p JOIN users u ON p.user_id = u.id ORDER BY p.id DESC
    """)
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(posts)

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.id, p.title, p.content, u.name as author, p.user_id 
        FROM posts p JOIN users u ON p.user_id = u.id WHERE p.id = %s
    """, (post_id,))
    post = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if post:
        is_owner = (session.get('user_id') == post['user_id'])
        return jsonify({'post': post, 'is_owner': is_owner})
    return jsonify({'message': '글이 없습니다.'}), 404

@app.route('/api/posts', methods=['POST'])
def write_post():
    if 'user_id' not in session: return jsonify({'message': '로그인 필요'}), 401
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO posts (title, content, user_id) VALUES (%s, %s, %s)", 
                   (data.get('title'), data.get('content'), session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def edit_post(post_id):
    if 'user_id' not in session: return jsonify({'message': '로그인 필요'}), 401
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE posts SET title = %s, content = %s WHERE id = %s AND user_id = %s", 
                   (data.get('title'), data.get('content'), post_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    if 'user_id' not in session: return jsonify({'message': '로그인 필요'}), 401
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id = %s AND user_id = %s", (post_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
