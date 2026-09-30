from flask import Flask, jsonify, request

app = Flask(__name__)

# Giả lập database trong bộ nhớ
posts = [
    {"id": 1, "title": "Bài viết mẫu 1", "content": "Nội dung bài viết 1", "author_id": 1},
    {"id": 2, "title": "Bài viết mẫu 2", "content": "Nội dung bài viết 2", "author_id": 2},
]

# 1. GET /api/v1/posts - Lấy danh sách bài viết
@app.route('/api/v1/posts', methods=['GET'])
def get_posts():
    # Hỗ trợ query params: ?limit=10&page=1
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    start = (page - 1) * limit
    end = start + limit
    return jsonify({
        "status": "success",
        "total": len(posts),
        "data": posts[start:end]
    }), 200

# 2. POST /api/v1/posts - Tạo bài viết mới
@app.route('/api/v1/posts', methods=['POST'])
def create_post():
    payload = request.get_json() or {}
    
    if not payload.get('title') or not payload.get('content'):
        return jsonify({"error": "Thiếu 'title' hoặc 'content'"}), 400

    new_post = {
        "id": len(posts) + 1,
        "title": payload['title'],
        "content": payload['content'],
        "author_id": payload.get('author_id', 1)
    }
    posts.append(new_post)
    return jsonify({
        "status": "success",
        "data": new_post
    }), 201

# 3. GET /api/v1/posts/ - Lấy chi tiết bài viết
@app.route('/api/v1/posts/', methods=['GET'])
def get_post(post_id):
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        return jsonify({"error": "Không tìm thấy bài viết"}), 404
    return jsonify({"status": "success", "data": post}), 200

# 4. PUT /api/v1/posts/ - Cập nhật toàn bộ bài viết
@app.route('/api/v1/posts/', methods=['PUT'])
def update_post(post_id):
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        return jsonify({"error": "Không tìm thấy bài viết"}), 404
    
    payload = request.get_json() or {}
    post['title'] = payload.get('title', post['title'])
    post['content'] = payload.get('content', post['content'])
    return jsonify({"status": "success", "data": post}), 200

# 5. DELETE /api/v1/posts/ - Xóa bài viết
@app.route('/api/v1/posts/', methods=['DELETE'])
def delete_post(post_id):
    global posts
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        return jsonify({"error": "Không tìm thấy bài viết"}), 404
    
    posts = [p for p in posts if p["id"] != post_id]
    return jsonify({"status": "success", "message": "Đã xóa bài viết thành công"}), 200

if __name__ == '__main__':
    app.run(debug=True)