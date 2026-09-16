from flask import Flask, jsonify

ORDERS = {
    "1": {"id": "1", "status": "pending"},
    "2": {"id": "2", "status": "shipped"},
    "3": {"id": "3", "status": "delivered"},
}

app5 = Flask(__name__)

@app5.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return jsonify({"error": "not found"}), 404

    if order["status"] in ("shipped", "delivered"):
        return jsonify({"error": "cannot delete"}), 409

    ORDERS.pop(order_id, None)
    return "", 204

if __name__ == "__main__":
    app5.run(port=5000, debug=True)