from drf_yasg import openapi

PREDICT_SWAGGER = {
    'method': 'post',
    'operation_description': (
        "Predict using selected model. Requires JWT token from /api/account/login/ "
        "in Authorization header (Bearer <token>)."
    ),
    'request_body': None,
    'manual_parameters': [
        openapi.Parameter(
            'model_name', openapi.IN_QUERY,
            description=(
                "Model to use for prediction. Must be one of: Plant disease, Cotton Pests, "
                "Tomato, Banana, mango, Soil Nutrition"
            ),
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'image', openapi.IN_FORM,
            description=(
                "Image file for prediction (required for Plant disease, Cotton Pests, "
                "Tomato, Banana, mango models)"
            ),
            type=openapi.TYPE_FILE,
            required=False
        ),
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="JWT token (Bearer <token>) obtained from /api/account/login/",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    'responses': {
        200: openapi.Response(
            description="Prediction results",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'predicted_class': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Predicted class for image models (Plant disease, Cotton Pests)"
                    ),
                    'confidence': openapi.Schema(
                        type=openapi.TYPE_NUMBER,
                        description="Confidence score for image models"
                    ),
                    'predictions': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        description="List of predictions for YOLO models (Tomato, Banana, mango)",
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'class': openapi.Schema(type=openapi.TYPE_STRING),
                                'confidence': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'bbox': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    description="Bounding box coordinates [x1, y1, x2, y2]",
                                    items=openapi.Schema(type=openapi.TYPE_NUMBER)
                                )
                            }
                        )
                    ),
                    'image_with_bboxes_url': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="URL of the image with bounding boxes for YOLO models"
                    ),
                    'regression_prediction': openapi.Schema(
                        type=openapi.TYPE_NUMBER,
                        description="Regression output for Soil Nutrition"
                    ),
                    'classifier_prediction': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Classifier output for Soil Nutrition"
                    )
                }
            )
        ),
        400: openapi.Response(description="Bad request"),
        401: openapi.Response(description="Unauthorized")
    }
}
