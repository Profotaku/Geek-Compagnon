
from app import app, render_template, jsonify
@app.errorhandler(404)
def resource_not_found(e, client):
    if client == 'app':
        return jsonify(error=str(e)), 404
    else:
        return render_template('public/404.html'), 404