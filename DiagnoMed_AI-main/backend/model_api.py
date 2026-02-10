import requests
from gradio_client import Client, handle_file
import os

# ---------------- CONFIG ----------------
# ⚠️ Replace with your Hugging Face Space name (exactly as shown in the URL)
HF_SPACE = "NoobMaster27/DDX"
HF_API = f"https://{HF_SPACE.lower().replace('/', '-')}.hf.space/"

print(f"✅ Using Hugging Face Space API: {HF_API}")

# ---------------- PREDICT FUNCTION ----------------
def predict_image(image_path: str):
    """
    Sends image to the Hugging Face Space and retrieves model prediction & GradCAM heatmap.
    """
    try:
        print(f"📤 Sending image to Hugging Face Space: {HF_SPACE}")
        client = Client(HF_SPACE)

        result = client.predict(
            img=handle_file(image_path),
            api_name="/predict"   # must match your app.py endpoint name in Hugging Face
        )

        # 🧩 Expected format:
        # result = [
        #   {'predictions': {'Pneumonia': 0.39, 'Edema': 0.23, 'Effusion': 0.11}, 'gradcam_url': '/file/gradcams/...jpg'},
        #   <gradcam image array>
        # ]

        if isinstance(result, list) and len(result) > 0:
            data = result[0]  # First dict element
            predictions = data.get("predictions", {})
            gradcam_url = data.get("gradcam_url")

            if not predictions:
                print("⚠️ No predictions returned.")
                return None

            # Extract top class
            top_label = max(predictions, key=predictions.get)
            confidence = predictions[top_label]

            print(f"✅ Top Prediction: {top_label} ({confidence*100:.2f}%)")
            print(f"🔥 GradCAM URL: {gradcam_url}")

            return {
                "label": top_label,
                "confidence": confidence,
                "predictions": predictions,
                "gradcam_url": gradcam_url,
            }
        else:
            print("⚠️ Unexpected response format from Hugging Face API:", result)
            return None

    except Exception as e:
        print(f"❌ Error calling Hugging Face Space: {e}")
        return None
