import os
import cv2
import uuid
import logging
import joblib
import numpy as np
from PIL import Image, ImageDraw
from sklearn.cluster import KMeans
from transformers import AutoImageProcessor, AutoModelForImageClassification
from ultralytics import YOLO
from django.conf import settings

logger = logging.getLogger(__name__)

# Standardized Model Names
MODEL_PLANT_DISEASE = 'Plant Disease'
MODEL_COTTON_PESTS = 'Cotton Pests'
MODEL_TOMATO = 'Tomato'
MODEL_BANANA = 'Banana'
MODEL_MANGO = 'Mango'
MODEL_SOIL_NUTRITION = 'Soil Nutrition'

MODEL_PATHS = {
    MODEL_PLANT_DISEASE: {
        'processor': 'A2H0H0R1/swin-tiny-patch4-window7-224-plant-disease-new',
        'model': 'A2H0H0R1/swin-tiny-patch4-window7-224-plant-disease-new'
    },
    MODEL_COTTON_PESTS: {
        'processor': 'RohithN2004/Cotton-pests',
        'model': 'RohithN2004/Cotton-pests'
    },
    MODEL_TOMATO: {
        'model': os.path.join(settings.BASE_DIR, 'models', 'Tomato.pt')
    },
    MODEL_BANANA: {
        'model': os.path.join(settings.BASE_DIR, 'models', 'Banana.pt')
    },
    MODEL_MANGO: { 
        'model': os.path.join(settings.BASE_DIR, 'models', 'mango.pt')
    },
    MODEL_SOIL_NUTRITION: {
        'regressor': os.path.join(settings.BASE_DIR, 'models', 'best_regressor_model.pkl'),
        'classifier': os.path.join(settings.BASE_DIR, 'models', 'best_classifier_model.pkl'),
        'label_encoder': os.path.join(settings.BASE_DIR, 'models', 'label_encoder.pkl')
    }
}

class MLEngine:
    _instance = None
    _loaded_models = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLEngine, cls).__new__(cls)
        return cls._instance

    def load_model(self, model_name):
        """Load the specified model or return from cache."""
        if model_name not in MODEL_PATHS:
            raise ValueError(f"Unknown model: {model_name}")

        if model_name in self._loaded_models:
            return self._loaded_models[model_name]

        config = MODEL_PATHS[model_name]
        
        try:
            if model_name in [MODEL_PLANT_DISEASE, MODEL_COTTON_PESTS]:
                processor = AutoImageProcessor.from_pretrained(config['processor'])
                model = AutoModelForImageClassification.from_pretrained(config['model'])
                self._loaded_models[model_name] = (processor, model)
                logger.info(f"Loaded model: {model_name} from Hugging Face")
                
            elif model_name in [MODEL_TOMATO, MODEL_BANANA, MODEL_MANGO]:
                model_path = config['model']
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"Model file not found: {model_path}")
                model = YOLO(model_path)
                self._loaded_models[model_name] = (None, model)
                logger.info(f"Loaded model: {model_name} from {model_path}")
                
            elif model_name == MODEL_SOIL_NUTRITION:
                regressor_path, classifier_path, le_path = config['regressor'], config['classifier'], config['label_encoder']
                for path in [regressor_path, classifier_path, le_path]:
                    if not os.path.exists(path):
                        raise FileNotFoundError(f"Model file not found: {path}")
                best_regressor = joblib.load(regressor_path)
                best_classifier = joblib.load(classifier_path)
                le = joblib.load(le_path)
                self._loaded_models[model_name] = (None, (best_regressor, best_classifier, le))
                logger.info(f"Loaded model: {model_name} from local PKL files")
                
            return self._loaded_models[model_name]
            
        except FileNotFoundError as e:
            logger.error(f"FileNotFoundError: {str(e)}")
            raise ValueError(f"Failed to load model: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {str(e)}")
            raise ValueError(f"Failed to load model: {str(e)}")

    def process_image(self, image_file, model_name, request):
        """Main entry point to process an image with a specified model."""
        processor, model = self.load_model(model_name)
        image = Image.open(image_file).convert('RGB')

        if model_name in [MODEL_PLANT_DISEASE, MODEL_COTTON_PESTS]:
            return self._process_transformer(image, processor, model)
        elif model_name in [MODEL_TOMATO, MODEL_BANANA, MODEL_MANGO]:
            return self._process_yolo(image, model, request)
        elif model_name == MODEL_SOIL_NUTRITION:
            return self._process_soil(image, model)

    def _process_transformer(self, image, processor, model):
        inputs = processor(images=image, return_tensors="pt")
        outputs = model(**inputs)
        probabilities = outputs.logits.softmax(dim=-1)
        predicted_class = probabilities.argmax().item()
        confidence = probabilities[0][predicted_class].item()

        return {
            "predicted_class": model.config.id2label[predicted_class],
            "confidence": confidence
        }

    def _process_yolo(self, image, model, request):
        results = model(image)

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

        return {
            "predictions": predictions,
            "image_with_bboxes_url": image_url
        }

    def _process_soil(self, image, model):
        image_np = np.array(image)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        smoothed_image = cv2.GaussianBlur(image_bgr, (5, 5), 0)
        reshaped_image = smoothed_image.reshape((-1, 3))
        
        # NOTE: KMeans with large images takes a very long time on CPU.
        # Resizing by a factor to speed up clustering
        small_image = cv2.resize(image_bgr, (100, 100))
        reshaped_small = small_image.reshape((-1, 3))
        
        kmeans = KMeans(n_clusters=3, random_state=0, n_init='auto').fit(reshaped_small)
        dominant_color = kmeans.cluster_centers_[0]

        best_regressor_model, best_classifier_model, le = model
        regression_pred = best_regressor_model.predict([dominant_color])[0]
        classifier_pred_proba = best_classifier_model.predict_proba([dominant_color])[0]
        classifier_pred = np.argmax(classifier_pred_proba)
        class_label = le.inverse_transform([classifier_pred])[0]
        confidence = classifier_pred_proba[classifier_pred]

        return {
            "regression_prediction": float(regression_pred),
            "classifier_prediction": class_label,
            "confidence": float(confidence)
        }

ml_engine = MLEngine()
