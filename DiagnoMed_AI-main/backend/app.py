import requests
import json
import mimetypes
import glob
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
import uuid

# ------------------ LOAD ENVIRONMENT ------------------
load_dotenv(override=True)
os.getenv("DATABASE_URL")
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# ------------------ FLASK CONFIG ------------------
app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

# ------------------ DATABASE CONFIG ------------------
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ------------------ FILE PATHS ------------------
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ------------------ HUGGING FACE MODEL CONFIG ------------------
# Use the new Hugging Face Space provided by your friend
HF_SPACE = "yashganatra-ipd"  # new Hugging Face Space name (from https://yashganatra-ipd.hf.space/)
HF_BASE_URL = "https://yashganatra-ipd.hf.space"
print(f"✅ Using Hugging Face Space: {HF_SPACE} -> {HF_BASE_URL}")

# ------------------ DATABASE MODEL ------------------
class PatientCase(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_name = db.Column(db.String(120))
    age = db.Column(db.Integer)
    blood_type = db.Column(db.String(10))
    symptoms = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    gradcam_url = db.Column(db.String(255))
    cnn_output = db.Column(db.Text)
    confidence = db.Column(db.Float)
    analysis_output = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_name": self.patient_name,
            "age": self.age,
            "blood_type": self.blood_type,
            "symptoms": self.symptoms,
            "image_url": self.image_url,
            "gradcam_url": self.gradcam_url,
            "cnn_output": self.cnn_output,
            "confidence": self.confidence,
            "analysis_output": self.analysis_output,
        }

# ------------------ CALL HUGGING FACE MODEL ------------------
def call_huggingface_model(image_path):
    """
    Try several reasonable HTTP POST variants against the Space `/run/predict`
    endpoint and parse common response shapes. Returns a dict similar to the
    previous implementation or None on failure.
    """
    url = HF_BASE_URL.rstrip("/") + "/run/predict"

    mime = mimetypes.guess_type(image_path)[0] or "application/octet-stream"

    # Try a couple of multipart patterns Gradio spaces commonly accept.
    attempts = []
    attempts_details = []

    # Pattern A: `data` JSON placeholder + numbered data_0 file
    try:
        with open(image_path, "rb") as f:
            files = {
                "data": (None, json.dumps([None])),
                "data_0": (os.path.basename(image_path), f, mime),
            }
            print(f"📤 Posting to {url} using Pattern A...")
            r = requests.post(url, files=files, timeout=60)
            attempts.append((r.status_code, r.text[:1000]))
            attempts_details.append({"url": url, "pattern": "A", "status": r.status_code, "text": r.text[:5000]})
            if r.ok:
                try:
                    resp = r.json()
                except Exception:
                    resp = r.text
                parsed = _parse_space_response(resp)
                if parsed:
                    return parsed
    except Exception as e:
        print("⚠️ Pattern A failed:", e)

    # Pattern B: simple file upload to /predict (some spaces expose this)
    try:
        predict_url = HF_BASE_URL.rstrip("/") + "/predict"
        with open(image_path, "rb") as f:
            # Try key 'image' first (existing)
            files = {"image": (os.path.basename(image_path), f, mime)}
            print(f"📤 Posting to {predict_url} using Pattern B (image key)...")
            r = requests.post(predict_url, files=files, timeout=60)
            attempts.append((r.status_code, r.text[:1000]))
            attempts_details.append({"url": predict_url, "pattern": "B-image", "status": r.status_code, "text": r.text[:5000]})
            if r.ok:
                try:
                    resp = r.json()
                except Exception:
                    resp = r.text
                parsed = _parse_space_response(resp)
                if parsed:
                    return parsed

        # Try posting under key 'file' because some FastAPI endpoints expect that
        try:
            with open(image_path, "rb") as f2:
                files = {"file": (os.path.basename(image_path), f2, mime)}
                print(f"📤 Posting to {predict_url} using Pattern B (file key)...")
                r = requests.post(predict_url, files=files, timeout=60)
                attempts.append((r.status_code, r.text[:1000]))
                attempts_details.append({"url": predict_url, "pattern": "B-file", "status": r.status_code, "text": r.text[:5000]})
                if r.ok:
                    try:
                        resp = r.json()
                    except Exception:
                        resp = r.text
                    parsed = _parse_space_response(resp)
                    if parsed:
                        return parsed
        except Exception as e:
            print("⚠️ Pattern B (file key) failed:", e)
    except Exception as e:
        print("⚠️ Pattern B failed:", e)

    # Pattern C: fallback - post file under generic key 'file'
    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, mime)}
            print(f"📤 Posting to {url} using Pattern C...")
            r = requests.post(url, files=files, timeout=60)
            attempts.append((r.status_code, r.text[:1000]))
            attempts_details.append({"url": url, "pattern": "C", "status": r.status_code, "text": r.text[:5000]})
            if r.ok:
                try:
                    resp = r.json()
                except Exception:
                    resp = r.text
                parsed = _parse_space_response(resp)
                if parsed:
                    return parsed
    except Exception as e:
        print("⚠️ Pattern C failed:", e)

    print("❌ All HTTP attempts failed. Attempts summary:", attempts)
    # attach attempts_details for debugging via test endpoint
    return {"_error": "all_attempts_failed", "attempts": attempts_details}


def _parse_space_response(resp):
    """Normalize different Space response shapes into the expected dict."""
    try:
        # If response is a list, prefer first element
        if isinstance(resp, list) and len(resp) > 0:
            data = resp[0]
        elif isinstance(resp, dict):
            # Some spaces return {'data': [...]}
            if "data" in resp and isinstance(resp["data"], list) and len(resp["data"])>0:
                data = resp["data"][0]
            else:
                data = resp
        else:
            return None

        # data should be a dict with 'predictions' key in many apps
        predictions = None
        gradcam_url = None
        if isinstance(data, dict):
            predictions = data.get("predictions") or data.get("prediction") or data.get("preds")
            gradcam_url = data.get("gradcam_url") or data.get("gradcam")

        if not predictions:
            return None

        # Convert mapping to list of tuples if necessary
        if isinstance(predictions, dict):
            sorted_preds = sorted(predictions.items(), key=lambda x: x[1], reverse=True)[:3]
        elif isinstance(predictions, list):
            # already list of (label,score) pairs
            sorted_preds = predictions[:3]
        else:
            return None

        top_label, top_confidence = sorted_preds[0]

        gradcam_full = (HF_BASE_URL + gradcam_url) if gradcam_url and not str(gradcam_url).startswith("http") else gradcam_url

        return {
            "top_label": top_label,
            "top_confidence": float(top_confidence),
            "top3": sorted_preds,
            "gradcam_url": gradcam_full,
        }
    except Exception as e:
        print("⚠️ Error parsing response:", e)
        return None

# ------------------ PATIENT UPLOAD ROUTE ------------------
@app.route("/api/patient/submit", methods=["POST"])
def submit_patient_case():
    try:
        name = request.form.get("name", "Anonymous")
        age = request.form.get("age")
        blood_type = request.form.get("blood_type")
        symptoms = request.form.get("symptoms", "")
        image_file = request.files.get("image")

        if not image_file:
            return jsonify({"error": "No image uploaded"}), 400

        # ------------------ SAVE IMAGE ------------------
        filename = f"{uuid.uuid4()}_{image_file.filename}"
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(image_path)
        print(f"📸 Saved image at {image_path}")

        # ------------------ MODEL INFERENCE ------------------
        prediction = call_huggingface_model(image_path)
        print("🔎 Prediction received:", prediction)

        # If the helper returned the special failure object, surface a concise error
        if isinstance(prediction, dict) and prediction.get("_error") == "all_attempts_failed":
            print("❌ Model HTTP attempts failed:", prediction.get("attempts"))
            return jsonify({"error": "Model inference failed"}), 500

        if not prediction:
            return jsonify({"error": "Model inference failed"}), 500

        # Some endpoints wrap the parsed result under a 'prediction' key.
        if isinstance(prediction, dict) and "prediction" in prediction:
            prediction = prediction["prediction"]

        # Validate expected keys
        if not all(k in prediction for k in ("top_label", "top_confidence", "top3")):
            print("❌ Unexpected prediction shape:", prediction)
            return jsonify({"error": "Unexpected model response"}), 500

        cnn_output = prediction["top_label"]
        confidence = prediction["top_confidence"]
        gradcam_url = prediction.get("gradcam_url")

        top3 = prediction["top3"]
        analysis_output = "Top 3 Predictions: " + ", ".join(
            [f"{k} ({v*100:.2f}%)" for k, v in top3]
        )

        # ------------------ SAVE TO DATABASE ------------------
        case = PatientCase(
            patient_name=name,
            age=age,
            blood_type=blood_type,
            symptoms=symptoms,
            image_url=f"/static/uploads/{filename}",
            gradcam_url=gradcam_url,
            cnn_output=cnn_output,
            confidence=confidence,
            analysis_output=analysis_output,
        )

        db.session.add(case)
        db.session.commit()
        print("✅ Case saved to database!")

        # ------------------ RESPONSE ------------------
        return jsonify({
            "message": "Case submitted successfully!",
            "cnn_output": cnn_output,
            "confidence": confidence,
            "gradcam_url": gradcam_url,
            "image_url": f"/static/uploads/{filename}",
            "analysis_output": analysis_output
        }), 200

    except Exception as e:
        print(f"❌ Error in /api/patient/submit: {e}")
        return jsonify({"error": str(e)}), 500


# ------------------ TEST PREDICT ROUTE ------------------
@app.route('/api/test/predict', methods=['POST'])
def test_predict():
    """Endpoint to test model inference directly.

    Accepts form file `image`. If not provided, will pick the first image
    found in the uploads folder. Returns raw parsed model output.
    """
    try:
        image_file = request.files.get('image')
        if image_file:
            filename = f"test_{uuid.uuid4()}_{image_file.filename}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
        else:
            files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*'))
            if not files:
                return jsonify({"error": "No uploaded images available for test"}), 400
            image_path = files[0]

        prediction = call_huggingface_model(image_path)

        # If call_huggingface_model returned the special failure dict, include attempts when debug
        debug = request.args.get('debug') == '1'
        if isinstance(prediction, dict) and prediction.get('_error') == 'all_attempts_failed':
            if debug:
                return jsonify({"error": "Model inference failed", "attempts": prediction.get('attempts')}), 500
            else:
                return jsonify({"error": "Model inference failed"}), 500

        if not prediction:
            return jsonify({"error": "Model inference failed"}), 500

        return jsonify({"prediction": prediction}), 200
    except Exception as e:
        print("❌ Error in /api/test/predict:", e)
        return jsonify({"error": str(e)}), 500


# ------------------ DOCTOR FETCH ALL CASES ------------------
@app.route('/api/doctor/cases', methods=['GET'])
def get_doctor_cases():
    try:
        cases = PatientCase.query.all()
        return jsonify([
            {
                "id": c.id,
                "patient_name": c.patient_name,
                "age": c.age,
                "blood_type": c.blood_type,
                "symptoms": c.symptoms,
                "cnn_output": c.cnn_output,
                "analysis_output": c.analysis_output,
                "image_url": c.image_url,
                "gradcam_url": c.gradcam_url,
            }
            for c in cases
        ])
    except Exception as e:
        print("❌ Error fetching doctor cases:", e)
        return jsonify({"error": "Server error"}), 500


# ------------------ FRONTEND ROUTE ------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    dist_dir = os.path.join(os.path.dirname(__file__), "dist")
    if not os.path.exists(dist_dir):
        return jsonify({"message": "✅ Backend running, DB connected!"})

    if path != "" and os.path.exists(os.path.join(dist_dir, path)):
        return send_from_directory(dist_dir, path)
    else:
        return send_from_directory(dist_dir, "index.html")

# ------------------ MAIN ENTRY ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Database initialized successfully.")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
