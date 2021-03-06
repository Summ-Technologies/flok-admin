import summ_logging
import summ_web

app = summ_web.create_app(__name__)
summ_logging.configure_logging(app.config, debug=app.config.get("DEBUG", False))
summ_web.setup_cors(app)
db = summ_web.create_db(app)
api = summ_web.create_api(app)
summ_web.setup_webargs()

from . import routes

routes.add_routes(api)
