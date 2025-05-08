import logging

import grpc
from inference_service.proto import inference_pb2
from inference_service.proto import inference_pb2_grpc
from inference_service.server.model_handler import ModelHandler


class InferenceServicer(inference_pb2_grpc.InferenceServiceServicer):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_handler = ModelHandler()
        self.logger.info("InferenceServicer initialized")

    def Predict(self, request, context):
        self.logger.info(f"Received prediction request: {request.text[:50]}...")

        try:
            prediction, confidence, rating = self.model_handler.predict(request.text)

            response = inference_pb2.PredictResponse(
                prediction=str(prediction), confidence=float(confidence), rating=rating
            )

            self.logger.info(f"Prediction successful: {rating}")
            return response

        except Exception as e:
            self.logger.error(f"Prediction failed: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Prediction failed: {str(e)}")
            return inference_pb2.PredictResponse()

    def Health(self, request, context):
        status = self.model_handler.check_health()
        response = inference_pb2.HealthResponse(
            status=(
                inference_pb2.HealthResponse.Status.SERVING
                if status
                else inference_pb2.HealthResponse.Status.NOT_SERVING
            )
        )
        return response
