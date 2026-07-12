from app import app
from app import config as _cfg

if __name__ == '__main__':
    # Debug follows APP_ENV (on in dev, off in production) unless overridden by
    # FLASK_DEBUG — never hardcode debug=True, which exposes the Werkzeug console.
    app.run(host='0.0.0.0', port=8000, debug=_cfg.DEBUG)
