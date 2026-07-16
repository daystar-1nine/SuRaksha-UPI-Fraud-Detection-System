from flask import jsonify

class AppError(Exception):
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['code'] = self.status_code
        return {"success": False, "error": rv}

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"success": False, "error": {"message": "Resource not found", "code": 404}}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "error": {"message": "Internal server error", "code": 500}}), 500
