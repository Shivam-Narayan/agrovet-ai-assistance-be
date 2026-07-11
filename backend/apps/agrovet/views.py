from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from transformers import AutoImageProcessor, AutoModelForImageClassification
from ultralytics import YOLO
import os, cv2, uuid, logging, joblib
from sklearn.cluster import KMeans
import numpy as np
from PIL import Image, ImageDraw
from django.conf import settings
from .swagger import PREDICT_SWAGGER
from apps.account.models import UserActivity

# Set up logging
logger = logging.getLogger(__name__)

# Define model paths separately
MODEL_PATHS = {
    'Plant disease': {
        'processor': 'A2H0H0R1/swin-tiny-patch4-window7-224-plant-disease-new',
        'model': 'A2H0H0R1/swin-tiny-patch4-window7-224-plant-disease-new'
    },
    'Cotton Pests': {
        'processor': 'RohithN2004/Cotton-pests',
        'model': 'RohithN2004/Cotton-pests'
    },
    'Tomato': {
        'model': os.path.join(settings.BASE_DIR, 'models', 'Tomato.pt')
    },
    'Banana': {
        'model': os.path.join(settings.BASE_DIR, 'models', 'Banana.pt')
    },
    'mango': { 
        'model': os.path.join(settings.BASE_DIR, 'models', 'mango.pt')
    },
    'Soil Nutrition': {
        'regressor': os.path.join(settings.BASE_DIR, 'models', 'best_regressor_model.pkl'),
        'classifier': os.path.join(settings.BASE_DIR, 'models', 'best_classifier_model.pkl'),
        'label_encoder': os.path.join(settings.BASE_DIR, 'models', 'label_encoder.pkl')
    }
}

def load_model(model_name):
    """Load the specified model and processor based on model_name."""
    try:
        if model_name not in MODEL_PATHS:
            raise ValueError(f"Unknown model: {model_name}")

        config = MODEL_PATHS[model_name]
        if model_name in ["Plant disease", "Cotton Pests"]:
            processor = AutoImageProcessor.from_pretrained(config['processor'])
            model = AutoModelForImageClassification.from_pretrained(config['model'])
            logger.info(f"Loaded model: {model_name} from Hugging Face ({config['model']})")
            return processor, model
        elif model_name in ["Tomato", "Banana", "mango"]:
            model_path = config['model']
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            model = YOLO(model_path)
            logger.info(f"Loaded model: {model_name} from {model_path}")
            return None, model
        elif model_name == "Soil Nutrition":
            regressor_path = config['regressor']
            classifier_path = config['classifier']
            le_path = config['label_encoder']
            for path in [regressor_path, classifier_path, le_path]:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Model file not found: {path}")
            best_regressor_model = joblib.load(regressor_path)
            best_classifier_model = joblib.load(classifier_path)
            le = joblib.load(le_path)
            model = (best_regressor_model, best_classifier_model, le)
            logger.info(f"Loaded model: {model_name} from {regressor_path}, {classifier_path}, {le_path}")
            return None, model
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError: {str(e)}")
        raise ValueError(f"Failed to load model: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading model {model_name}: {str(e)}")
        raise ValueError(f"Failed to load model: {str(e)}")


@swagger_auto_schema(**PREDICT_SWAGGER)
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

    try:
        processor, model = load_model(model_name)
    except ValueError as e:
        return Response(
            {'error': str(e)},
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
            image = Image.open(image_file).convert('RGB')

            # ===== Plant disease / Cotton Pests =====
            if model_name in ["Plant disease", "Cotton Pests"]:
                inputs = processor(images=image, return_tensors="pt")
                outputs = model(**inputs)
                probabilities = outputs.logits.softmax(dim=-1)
                predicted_class = probabilities.argmax().item()
                confidence = probabilities[0][predicted_class].item()

                results_list.append({
                    "predicted_class": model.config.id2label[predicted_class],
                    "confidence": confidence
                })

            # ===== Tomato / Banana / Mango =====
            elif model_name in ["Tomato", "Banana", "mango"]:
                results = model(image)  # YOLO model inference

                draw = ImageDraw.Draw(image)
                predictions = []
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        cls_id = int(box.cls)
                        confidence = float(box.conf)
                        bbox = box.xyxy.tolist()[0]
                        class_name = result.names[cls_id]

                        draw.rectangle(bbox, outline='red', width=3)
                        draw.text((bbox[0], bbox[1] - 10), f"{class_name}: {confidence:.2f}", fill='red')

                        predictions.append({
                            "class": class_name,
                            "confidence": confidence,
                        })

                # Save annotated image
                save_dir = os.path.join(settings.MEDIA_ROOT, 'predictions')
                os.makedirs(save_dir, exist_ok=True)
                unique_filename = f"{uuid.uuid4()}.jpg"
                save_path = os.path.join(save_dir, unique_filename)
                image.save(save_path)

                image_url = request.build_absolute_uri(settings.MEDIA_URL + f'predictions/{unique_filename}')

                results_list.append({
                    "predictions": predictions,
                    "image_with_bboxes_url": image_url
                })

            # ===== Soil Nutrition =====
            elif model_name == "Soil Nutrition":
                image_np = np.array(image)
                image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
                smoothed_image = cv2.GaussianBlur(image_bgr, (5, 5), 0)
                reshaped_image = smoothed_image.reshape((-1, 3))
                kmeans = KMeans(n_clusters=3, random_state=0).fit(reshaped_image)
                dominant_color = kmeans.cluster_centers_[0]

                best_regressor_model, best_classifier_model, le = model
                regression_pred = best_regressor_model.predict([dominant_color])[0]
                classifier_pred_proba = best_classifier_model.predict_proba([dominant_color])[0]
                classifier_pred = np.argmax(classifier_pred_proba)
                class_label = le.inverse_transform([classifier_pred])[0]
                confidence = classifier_pred_proba[classifier_pred]

                results_list.append({
                    "regression_prediction": float(regression_pred),
                    "classifier_prediction": class_label,
                    "confidence": float(confidence)
                })

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
