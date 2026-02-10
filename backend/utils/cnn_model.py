"""
CNN Model loader for X-ray diagnosis using DenseNet121.
Ported from DiagnoMed with enhancements for DDX integration.
"""
import os
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple, List
import cv2

from backend.config import settings
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)

# X-ray condition labels from DenseNet121 trained model
XRAY_LABELS = [
    "Atelectasis", "Cardiomegaly", "Consolidation", "Edema", "Effusion",
    "Emphysema", "Fibrosis", "Hernia", "Infiltration", "Mass", "Nodule",
    "Pleural_Thickening", "Pneumonia", "Pneumothorax"
]

# Model paths
MODEL_DIR = settings.data_dir.parent / "models" / "cnn_model"
MODEL_PATH = MODEL_DIR / "densenet.hdf5"
HEATMAP_FOLDER = settings.data_dir.parent / "static" / "heatmaps"
UPLOADS_FOLDER = settings.data_dir.parent / "static" / "uploads"

# Ensure directories exist
HEATMAP_FOLDER.mkdir(parents=True, exist_ok=True)
UPLOADS_FOLDER.mkdir(parents=True, exist_ok=True)

# Global model instance
_cnn_model = None
_model_loaded = False


def load_densenet_model():
    """Load DenseNet121 model with pre-trained weights."""
    global _cnn_model, _model_loaded
    
    if _model_loaded:
        return _cnn_model
    
    try:
        import tensorflow as tf
        from tensorflow.keras.applications import DenseNet121
        from tensorflow.keras.models import Model
        
        logger.info("Building DenseNet121 architecture...")
        base_model = DenseNet121(weights=None, include_top=False, input_shape=(320, 320, 3))
        x = tf.keras.layers.GlobalAveragePooling2D()(base_model.output)
        x = tf.keras.layers.Dense(len(XRAY_LABELS), activation="sigmoid")(x)
        model = Model(inputs=base_model.input, outputs=x)
        
        if MODEL_PATH.exists():
            logger.info(f"Loading weights from: {MODEL_PATH}")
            model.load_weights(str(MODEL_PATH), by_name=True, skip_mismatch=True)
            logger.info("DenseNet weights loaded successfully")
        else:
            logger.warning(f"Model weights not found: {MODEL_PATH}")
            logger.warning("CNN predictions will use random weights - download model for accurate results")
        
        _cnn_model = model
        _model_loaded = True
        return model
        
    except ImportError as e:
        logger.error(f"TensorFlow not installed: {e}")
        return None
    except Exception as e:
        logger.error(f"Could not load DenseNet model: {e}")
        return None


def generate_gradcam(
    img_array: np.ndarray,
    model,
    original_image_path: Optional[str] = None,
    last_conv_layer_name: str = "conv5_block16_concat"
) -> Optional[str]:
    """
    Generate GradCAM heatmap for a preprocessed image array.
    
    Args:
        img_array: Preprocessed image (1, 320, 320, 3)
        model: Loaded DenseNet model
        original_image_path: Path to original image for overlay
        last_conv_layer_name: Name of last conv layer for gradients
        
    Returns:
        Path to saved GradCAM image, or None on failure
    """
    try:
        import tensorflow as tf
        from tensorflow.keras.models import Model
        
        grad_model = Model(
            inputs=model.input,
            outputs=[model.get_layer(last_conv_layer_name).output, model.output]
        )
        
        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(img_array)
            pred_index = tf.argmax(predictions[0])
            loss = predictions[:, pred_index]
        
        grads = tape.gradient(loss, conv_outputs)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        
        conv_outputs = conv_outputs[0].numpy()
        pooled_grads = pooled_grads.numpy()
        
        heatmap = np.mean(conv_outputs * pooled_grads, axis=-1)
        heatmap = np.maximum(heatmap, 0)
        if np.max(heatmap) > 0:
            heatmap /= np.max(heatmap)
        
        # Resize and colorize
        heatmap = cv2.resize(heatmap, (224, 224))
        heatmap = np.uint8(255 * heatmap)
        heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        # Overlay on original if available
        if original_image_path and Path(original_image_path).exists():
            original = cv2.imread(original_image_path)
            if original is not None:
                original = cv2.resize(original, (224, 224))
                superimposed = cv2.addWeighted(original, 0.6, heatmap_colored, 0.4, 0)
                
                # Save GradCAM
                gradcam_filename = Path(original_image_path).stem + "_gradcam.jpg"
                gradcam_path = HEATMAP_FOLDER / gradcam_filename
                cv2.imwrite(str(gradcam_path), superimposed)
                logger.info(f"GradCAM saved: {gradcam_path}")
                return str(gradcam_path)
        
        # Save heatmap only
        heatmap_filename = f"heatmap_{np.random.randint(10000)}.jpg"
        heatmap_path = HEATMAP_FOLDER / heatmap_filename
        cv2.imwrite(str(heatmap_path), heatmap_colored)
        return str(heatmap_path)
        
    except Exception as e:
        logger.error(f"GradCAM generation failed: {e}")
        return None


def predict_xray(image_path: str) -> Dict:
    """
    Run X-ray prediction using DenseNet121.
    
    Args:
        image_path: Path to X-ray image file
        
    Returns:
        Dict with prediction results:
        - predicted_label: Top predicted condition
        - confidence: Confidence score (0-1)
        - all_predictions: List of (label, probability) for all 14 conditions
        - gradcam_path: Path to GradCAM visualization
    """
    model = load_densenet_model()
    
    if model is None:
        return {
            "predicted_label": "Model Not Available",
            "confidence": 0.0,
            "all_predictions": [],
            "gradcam_path": None,
            "error": "TensorFlow/model not loaded"
        }
    
    try:
        import tensorflow as tf
        from tensorflow.keras.applications.densenet import preprocess_input
        
        # Load and preprocess image
        img = tf.keras.preprocessing.image.load_img(image_path, target_size=(320, 320))
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        # Predict
        predictions = model.predict(img_array, verbose=0)
        pred_index = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][pred_index])
        predicted_label = XRAY_LABELS[pred_index] if pred_index < len(XRAY_LABELS) else "Unknown"
        
        # Get all predictions sorted by probability
        all_preds = [(XRAY_LABELS[i], float(predictions[0][i])) 
                     for i in range(len(XRAY_LABELS))]
        all_preds.sort(key=lambda x: x[1], reverse=True)
        
        # Generate GradCAM
        gradcam_path = generate_gradcam(img_array, model, image_path)
        
        logger.info(f"X-ray prediction: {predicted_label} ({confidence:.2%})")
        
        return {
            "predicted_label": predicted_label,
            "confidence": confidence,
            "all_predictions": all_preds[:5],  # Top 5
            "gradcam_path": gradcam_path
        }
        
    except Exception as e:
        logger.error(f"X-ray prediction error: {e}")
        return {
            "predicted_label": "Error",
            "confidence": 0.0,
            "all_predictions": [],
            "gradcam_path": None,
            "error": str(e)
        }


def get_xray_labels() -> List[str]:
    """Get list of conditions the CNN can detect."""
    return XRAY_LABELS.copy()
