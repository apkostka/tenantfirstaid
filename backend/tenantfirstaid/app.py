from flask import Flask, request, jsonify

from .chat import chat
from .shared import CACHE
from .submit_feedback import submit_feedback
from .get_feedback import get_feedback
from .prompt import get_prompt, set_prompt

app = Flask(__name__)


@app.get("/api/history/<session_id>")
def history(session_id):
    return jsonify(CACHE.get(session_id, []))


app.add_url_rule("/api/query", view_func=chat, methods=["POST"])
app.add_url_rule("/api/get_feedback", view_func=get_feedback, methods=["POST"])
app.add_url_rule("/api/feedback", view_func=submit_feedback, methods=["POST"])
app.add_url_rule(
    "/api/prompt", endpoint="prompt_get", view_func=get_prompt, methods=["GET"]
)
app.add_url_rule(
    "/api/prompt", endpoint="prompt_post", view_func=set_prompt, methods=["POST"]
)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
