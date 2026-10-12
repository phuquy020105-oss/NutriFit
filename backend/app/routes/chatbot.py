import json

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    request,
    stream_with_context,
)

from app.services.chatbot_service import (
    ChatbotServiceError,
    generate_reply,
    stream_reply,
)


chatbot_bp = Blueprint(
    "chatbot",
    __name__,
    url_prefix="/api/chatbot",
)


@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    """Nhận câu hỏi và trả lời từ NutriFit AI."""

    # 1. Kiểm tra Content-Type
    if not request.is_json:
        return jsonify({
            "success": False,
            "message": "Request phải có Content-Type: application/json.",
        }), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Dữ liệu gửi lên không hợp lệ.",
        }), 400

    # 2. Kiểm tra câu hỏi
    message = data.get("message")

    if not isinstance(message, str) or not message.strip():
        return jsonify({
            "success": False,
            "message": "Vui lòng nhập câu hỏi.",
        }), 400

    message = message.strip()

    if len(message) > 2000:
        return jsonify({
            "success": False,
            "message": "Câu hỏi tối đa 2000 ký tự.",
        }), 400

    # 3. Kiểm tra lịch sử hội thoại
    history = data.get("history", [])

    if not isinstance(history, list):
        return jsonify({
            "success": False,
            "message": "Lịch sử hội thoại không hợp lệ.",
        }), 400

    # Chỉ lấy các trường cần thiết từ lịch sử.
    safe_history = []

    for item in history[-12:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if (
            role in ("user", "assistant", "model")
            and isinstance(content, str)
            and content.strip()
        ):
            safe_history.append({
                "role": role,
                "content": content.strip()[:2000],
            })

    # 4. Nếu Frontend yêu cầu streaming, trả lời từng đoạn.
    if data.get("stream") is True:

        def generate_events():
            try:
                for piece in stream_reply(message, safe_history):
                    event = {
                        "type": "chunk",
                        "text": piece,
                    }

                    yield (
                        "data: "
                        + json.dumps(event, ensure_ascii=False)
                        + "\n\n"
                    )

                yield (
                    "data: "
                    + json.dumps({"type": "done"})
                    + "\n\n"
                )

            except ChatbotServiceError as exc:
                current_app.logger.warning(
                    "Chatbot streaming error: %s",
                    exc,
                )

                event = {
                    "type": "error",
                    "message": str(exc),
                }

                yield (
                    "data: "
                    + json.dumps(event, ensure_ascii=False)
                    + "\n\n"
                )

            except Exception:
                current_app.logger.exception(
                    "Unexpected error in NutriFit Chatbox streaming"
                )

                event = {
                    "type": "error",
                    "message": "Chatbox gặp lỗi không mong đợi. Vui lòng thử lại.",
                }

                yield (
                    "data: "
                    + json.dumps(event, ensure_ascii=False)
                    + "\n\n"
                )

        return Response(
            stream_with_context(generate_events()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # 5. Nếu không yêu cầu streaming, trả JSON như API cũ.
    try:
        reply = generate_reply(message, safe_history)

        return jsonify({
            "success": True,
            "reply": reply,
        }), 200

    except ChatbotServiceError as exc:
        return jsonify({
            "success": False,
            "message": str(exc),
        }), exc.status_code

    except Exception:
        current_app.logger.exception(
            "Unexpected error in NutriFit Chatbox"
        )

        return jsonify({
            "success": False,
            "message": "Chatbox gặp lỗi không mong đợi. Vui lòng thử lại.",
        }), 500