# app.py

import logging
import os
from pathlib import Path
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from ariadne import (
    gql,
    graphql_sync,
    make_executable_schema,
    load_schema_from_path,
    QueryType,
)
from ariadne.explorer.playground import PLAYGROUND_HTML

from inference_service.client.inference_client import InferenceClient
from inference_service.utils.logging_utils import setup_logging

# ----- resolvers -----
query = QueryType()


@query.field("hello")
def resolve_hello(_, info):
    return "Hi there"


@query.field("predict")
def resolve_predict(_, info, text):
    # initialize gRPC client
    client = InferenceClient(
        host=os.getenv("GRPC_INFERENCE_HOST", "localhost"),
        port=int(os.getenv("GRPC_INFERENCE_PORT", "50051")),
    )
    if not client.check_health():
        # service down → return null
        return None
    resp = client.predict(text)
    if resp is None:
        return None
    return {
        "prediction": resp.prediction,
        "confidence": resp.confidence,
        "rating": resp.rating,
    }


# ----- schema setup -----
schema_path = Path(__file__).parent / "schema.graphql"
type_defs = gql(load_schema_from_path(str(schema_path)))
schema = make_executable_schema(type_defs, query)


def create_app():
    setup_logging()
    app = Flask(
        __name__,
        static_url_path="",
        static_folder="../frontend/build",
        template_folder="../frontend/build",
    )
    CORS(app)  # enable CORS for all routes and origins

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/graphql", methods=["GET"])
    def playground():
        return PLAYGROUND_HTML, 200

    @app.route("/graphql", methods=["POST"])
    def graphql_server():
        data = request.get_json()
        success, result = graphql_sync(
            schema,
            data,
            context_value=request,
            debug=app.debug,
        )
        status = 200 if success else 400
        return jsonify(result), status

    return app


if __name__ == "__main__":
    # run Flask dev server
    app = create_app()
    app.run(host="localhost", port=5000, debug=True)
