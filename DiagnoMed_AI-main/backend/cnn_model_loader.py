import os
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.models import Model
from tensorflow.keras.applications.densenet import preprocess_input

# ------------------ CONFIG ------------------
MODEL_PATH = os.path.join("cnn_model", "densenet.hdf5")
HEATMAP_FOLDER = os.path.join("static", "heatmaps")
os.makedirs(HEATMAP_FOLDER, exist_ok=True)

LABELS = [
    "Atelectasis", "Cardiomegaly", "Consolidation", "Edema", "Effusion",
    "Emphysema", "Fibrosis", "Hernia", "Infiltration", "Mass", "Nodule",
    "Pleural_Thickening", "Pneumonia", "Pneumothorax"
]

# ------------------ LOAD MODEL ------------------
def load_densenet_model():
    """Safely load DenseNet model with pre-trained weights."""
    try:
        print("🧠 Building DenseNet121 architecture...")
        base_model = DenseNet121(weights=None, include_top=False, input_shape=(320, 320, 3))
        x = tf.keras.layers.GlobalAveragePooling2D()(base_model.output)
        x = tf.keras.layers.Dense(len(LABELS), activation="sigmoid")(x)
        model = Model(inputs=base_model.input, outputs=x)

        print(f"📦 Loading weights from: {MODEL_PATH}")
        model.load_weights(MODEL_PATH, by_name=True, skip_mismatch=True)
        print("✅ DenseNet weights loaded successfully.")
        return model
    except Exception as e:
        print(f"❌ Could not load DenseNet model: {e}")
        return None


model = load_densenet_model()
if model:
    print("✅ Model successfully initialized and ready for inference!")


# ------------------ GRADCAM GENERATOR ------------------
def generate_gradcam(img_array, model, last_conv_layer_name="conv5_block16_concat", output_path=None):
    """Generate GradCAM heatmap for a preprocessed image array."""
    try:
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

        # Convert heatmap to image
        heatmap = cv2.resize(heatmap, (224, 224))
        heatmap = np.uint8(255 * heatmap)
        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

        # If image file was provided, overlay it
        if output_path:
            original = cv2.imread(output_path)
            if original is None:
                raise ValueError(f"Cannot read image from {output_path}")
            original = cv2.resize(original, (224, 224))
            superimposed_img = cv2.addWeighted(original, 0.6, heatmap, 0.4, 0)
            gradcam_filename = os.path.basename(output_path).replace('.', '_gradcam.')
            gradcam_save_path = os.path.join(HEATMAP_FOLDER, gradcam_filename)
            cv2.imwrite(gradcam_save_path, superimposed_img)
            print(f"🔥 GradCAM saved: {gradcam_save_path}")
            return gradcam_save_path
        else:
            print("⚠️ No image path provided, returning only heatmap array.")
            return heatmap

    except Exception as e:
        print("❌ GradCAM generation failed:", e)
        return None


# ------------------ PREDICTION FUNCTION ------------------
def predict_xray(img_input):
    """
    Run CNN prediction and GradCAM.
    Supports:
        - img_input: path to image file (str)
        - img_input: preprocessed numpy array (shape: (1, 320, 320, 3))
    Returns:
        (predicted_label, confidence, heatmap_info)
    """
    try:
        if model is None:
            raise RuntimeError("Model not loaded")

        # Handle both input types
        if isinstance(img_input, str):
            # If given a path, load and preprocess it
            print(f"📂 Loading image from path: {img_input}")
            img = tf.keras.preprocessing.image.load_img(img_input, target_size=(320, 320))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)
            image_path = img_input
        else:
            # Assume preprocessed numpy array
            img_array = img_input
            image_path = None

        # Model prediction
        preds = model.predict(img_array)
        pred_index = int(np.argmax(preds))
        confidence = float(np.max(preds))
        predicted_label = LABELS[pred_index] if pred_index < len(LABELS) else "Unknown"

        # GradCAM
        gradcam_path = None
        if image_path:
            gradcam_path = generate_gradcam(img_array, model, output_path=image_path)
        else:
            print("⚠️ No file path, GradCAM image not saved.")

        heatmap_info = None
        if gradcam_path:
            heatmap_info = {
                "web_path": f"/static/heatmaps/{os.path.basename(gradcam_path)}",
                "local_path": os.path.abspath(gradcam_path),
            }

        print(f"✅ Prediction: {predicted_label} ({confidence:.2f})")
        return predicted_label, confidence, heatmap_info

    except Exception as e:
        print("❌ Error in predict_image:", e)
        return "Error", 0.0, None
