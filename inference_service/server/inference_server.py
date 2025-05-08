import grpc
import time
import logging
from concurrent import futures

from inference_service.proto import inference_pb2_grpc
from inference_service.server.inference_service import InferenceServicer
from inference_service.utils.logging_utils import setup_logging


def serve(port=50051):
    setup_logging()
    logger = logging.getLogger(__name__)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(
        InferenceServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info(f"Server started, listening on port {port}")

    try:
        while True:
            time.sleep(86400)  # One day in seconds
    except KeyboardInterrupt:
        server.stop(0)
        logger.info("Server stopped")


if __name__ == "__main__":
    serve()
