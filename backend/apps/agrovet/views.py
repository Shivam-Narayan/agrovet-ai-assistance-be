from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from apps.account.models import UserActivity
from rest_framework import serializers
from .ml_engine import ml_engine

@extend_schema(
    tags=['Agrovet Predictions'],
    summary="Predict using selected model",
    description="Predict using selected model. Requires JWT token from /api/account/login/ in Authorization header.",
    parameters=[
        OpenApiParameter(
            name='model_name',
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Model to use for prediction. Must be one of: Plant Disease, Cotton Pests, Tomato, Banana, Mango, Soil Nutrition"
        )
    ],
    request=inline_serializer(
        name='PredictionRequest',
        fields={'image': serializers.FileField()}
    ),
    responses={
        200: inline_serializer(
            name='PredictionResponse',
            fields={
                'results': serializers.ListField(
                    child=serializers.DictField()
                )
            }
        ),
        400: inline_serializer(
            name='PredictionError',
            fields={'error': serializers.CharField()}
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def predict(request):
    """Handle prediction requests for the specified model."""
    model_name = request.query_params.get('model_name')
    if not model_name:
        return Response(
            {'error': "model_name is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if 'image' not in request.FILES:
        return Response(
            {'error': "At least one image file is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    images = request.FILES.getlist('image')
    results_list = []

    for image_file in images:
        try:
            # Delegate all ML processing to the ml_engine service
            prediction_result = ml_engine.process_image(image_file, model_name, request)
            results_list.append(prediction_result)
        except ValueError as e:
            # This handles Unknown Model or FileNotFoundError
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            results_list.append({
                "error": f"Failed to process image '{image_file.name}': {str(e)}"
            })

    # Log prediction activity
    UserActivity.objects.create(
        user=request.user,
        activity_type='prediction',
        details={
            'model': model_name,
            'results': results_list
        }
    )

    return Response({"results": results_list}, status=status.HTTP_200_OK)
