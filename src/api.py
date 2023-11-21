from flask import Flask, request, Response  # type: ignore
import logging
from rayclusterscaler_api import  rayclusterscaler_api
import os

logger = logging.getLogger("rayclusterscaler_api")
app = Flask(__name__)
app.register_blueprint(rayclusterscaler_api)

@app.route("/healthz")
def alive():
    return "{'status': 'Healthy'}"


if __name__ == "__main__":

    lvl = logging.getLevelName(os.environ.get("LOG_LEVEL", "WARNING"))
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    log = logging.getLogger("extendedapi_server")
    log.setLevel(logging.WARNING)


    debug = os.environ.get("FLASK_ENV") == "development"


    app.run(
        host=os.environ.get("FLASK_HOST", "0.0.0.0"),
        port=6000,
        debug=debug,
    )
