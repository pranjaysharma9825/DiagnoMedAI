import os
from model_api import predict_image

def test_prediction():
    test_image_path = "static/uploads/xray_image_2.png"

    print("🧠 Starting model inference test...")
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        return

    result = predict_image(test_image_path)

    if result:
        print("\n✅ MODEL OUTPUT")
        print(f"🧩 Predicted Label: {result['label']}")
        print(f"📊 Confidence Score: {result['confidence']:.2f}")
        print(f"🔥 GradCAM Path: {result['gradcam_web']}")
        print(f"🧠 Local GradCAM File: {result['gradcam_local']}")

        # ✅ Check that GradCAM file actually exists
        gradcam_local_path = result.get("gradcam_local")
        if gradcam_local_path and os.path.exists(gradcam_local_path):
            print("🟢 GradCAM file verified and exists.")
        else:
            print("⚠️ GradCAM file missing or path incorrect.")

    else:
        print("❌ Model prediction failed.")

if __name__ == "__main__":
    test_prediction()
