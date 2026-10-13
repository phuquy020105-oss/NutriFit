# Add inside the existing create_app() after CORS is configured.
# Do not replace backend/app/__init__.py wholesale.
from app.routes.chatbot import chatbot_bp
app.register_blueprint(chatbot_bp)
