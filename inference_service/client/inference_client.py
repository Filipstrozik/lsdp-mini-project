import grpc
import logging
import argparse
from inference_service.proto import inference_pb2
from inference_service.proto import inference_pb2_grpc
from inference_service.utils.logging_utils import setup_logging


class InferenceClient:
    def __init__(self, host="localhost", port=50051):
        self.logger = logging.getLogger(__name__)
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)
        self.logger.info(f"Client initialized, connecting to {host}:{port}")

    def predict(self, text):
        self.logger.info(f"Sending prediction request: {text[:50]}...")
        request = inference_pb2.PredictRequest(text=text)

        try:
            response = self.stub.Predict(request)
            self.logger.info(f"Received prediction: {response.rating}")
            return response
        except grpc.RpcError as e:
            self.logger.error(f"RPC error: {e.code()}, {e.details()}")
            return None

    def check_health(self):
        self.logger.info("Checking service health...")
        request = inference_pb2.HealthRequest()

        try:
            response = self.stub.Health(request)
            status = (
                "SERVING"
                if response.status == inference_pb2.HealthResponse.Status.SERVING
                else "NOT_SERVING"
            )
            self.logger.info(f"Service health status: {status}")
            return response.status == inference_pb2.HealthResponse.Status.SERVING
        except grpc.RpcError as e:
            self.logger.error(f"Health check failed: {e.code()}, {e.details()}")
            return False


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="Inference Client")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", default=50051, type=int, help="Server port")
    parser.add_argument("--text", required=True, help="Text for prediction")
    args = parser.parse_args()

    client = InferenceClient(args.host, args.port)

    # Check health
    if not client.check_health():
        print("Service is not healthy, exiting.")
        return

    # Make prediction
    response = client.predict(args.text)
    if response:
        print(f"Prediction: {response.prediction}")
        print(f"Confidence: {response.confidence:.4f}")
        print(f"Rating: {response.rating}")


if __name__ == "__main__":
    main()
