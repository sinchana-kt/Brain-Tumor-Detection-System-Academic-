from flask import Flask, render_template, request, session, redirect, url_for
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from io import BytesIO
from groq import Groq 
import cv2
import base64
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------ CONFIG ------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

@app.before_request
def before_request():
    session.permanent = True

# Load ML model
MODEL_PATH = "final_model.keras"
model = load_model(MODEL_PATH)

CLASS_MAP = {
    0: "glioma",
    1: "meningioma",
    2: "notumor",
    3: "pituitary"
}
IMG_SIZE = (224, 224)

# GROQ CLOUD API KEY
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # Use environment variables for security
client = Groq(api_key=GROQ_API_KEY)
LLM_MODEL = "llama-3.3-70b-versatile"

# ------------------ DB SETUP ------------------
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.context_processor
def inject_user():
    return dict(user=session.get('user'))

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        otp TEXT,
        otp_expiry DATETIME
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS temp_users (
        email TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        otp TEXT,
        otp_expiry DATETIME
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        prediction TEXT,
        confidence REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT,
        hospital TEXT,
        case_id TEXT,
        amount REAL,
        story TEXT,
        image_data TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author TEXT NOT NULL,
        title TEXT NOT NULL,
        journey TEXT NOT NULL,
        medications TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

# ------------------ HELPER FUNCTIONS ------------------
def ask_llm(prediction, confidence, user_question=None):
    risk_note = "HIGH RISK" if prediction == "tumorous" else "LOW RISK"
    prompt = f"""
    You are a brain health assistant (NOT a doctor).
    MRI Result:
    - Prediction: {prediction}
    - Confidence: {confidence:.2f}
    - Risk Level: {risk_note}

    Explain clearly:
    1. What this result suggests
    2. Possible symptoms (general only)
    3. What the user should do next
    Keep it calm and not alarming.
    User question: {user_question if user_question else "Provide a general overview of these results."}
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=LLM_MODEL,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print("GROQ ERROR:", e)
        return "AI explanation currently unavailable. Please try again later."

def preprocess_image(img_file):
    img_bytes = BytesIO(img_file.read())
    img = image.load_img(img_bytes, target_size=IMG_SIZE)
    img_array = image.img_to_array(img)
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

# ------------------ ROUTES ------------------

@app.route("/home")
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("uploadmri.html", user=session['user'])

@app.route("/dashboard")
def dashboard():
    return render_template("uploadmri.html", user=session.get('user'))

@app.route("/donation")
def donation():
    conn = get_db()
    donations_data = conn.execute('SELECT * FROM donations ORDER BY id DESC').fetchall()
    conn.close()
    return render_template("MSdonation.html", donations=donations_data, user=session.get('user'))

@app.route("/submit_seek", methods=["POST"])
def submit_seek():
    name = request.form.get("name")
    contact = request.form.get("contact")
    hospital = request.form.get("hospital")
    case_id = request.form.get("case_id")
    amount = request.form.get("amount")
    story = request.form.get("story")
    
    # Handle image upload as base64
    image_data = None
    if 'proof' in request.files:
        files = request.files.getlist('proof')
        if files and files[0].filename != '':
            file_bytes = files[0].read()
            image_data = base64.b64encode(file_bytes).decode('utf-8')

    conn = get_db()
    conn.execute('''
        INSERT INTO donations (name, contact, hospital, case_id, amount, story, image_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, contact, hospital, case_id, amount, story, image_data))
    conn.commit()
    conn.close()
    return redirect(url_for('donation'))

@app.route("/directories")
def directories():
    return render_template("contacts.html", user=session.get('user'))

@app.route("/")
def landing():
    return render_template("landing.html", user=session.get('user'))

@app.route("/vos")
def vos():
    conn = get_db()
    stories_data = conn.execute('SELECT * FROM stories ORDER BY id DESC').fetchall()
    conn.close()
    return render_template("vos.html", stories=stories_data, user=session.get('user'))

@app.route("/add_story", methods=["POST"])
def add_story():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    title = request.form.get("title")
    journey = request.form.get("journey")
    medications = request.form.get("medications")
    author = session.get('user')
    
    conn = get_db()
    conn.execute('INSERT INTO stories (author, title, journey, medications) VALUES (?, ?, ?, ?)',
                 (author, title, journey, medications))
    conn.commit()
    conn.close()
    return redirect(url_for('vos'))

@app.route("/about")
def about():
    return render_template("about.html", user=session.get('user'))

# ------------------ LOGIN / REGISTER ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user:
            if check_password_hash(user["password"], password):
                session['user'] = user["name"]
                session['user_id'] = user["id"]
                next_page = request.args.get('next') or url_for('home')
                return redirect(next_page)
            else:
                return render_template("login.html", error="Incorrect password")
        
        return render_template("login.html", error="Account not found. Please sign up.")

    return render_template("login.html", next=request.args.get('next'))

#@app.route("/signup_init", methods=["POST"])
@app.route("/signup_init", methods=["POST"])
#@app.route("/signup_init", methods=["POST"])
def signup_init():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if user:
        conn.close()
        return jsonify({"error": "User already exists"}), 400

    hashed_password = generate_password_hash(password)

    otp = str(random.randint(1000, 9999))

    conn.execute(
        """
        INSERT OR REPLACE INTO temp_users
        (email, name, password, otp, otp_expiry)
        VALUES (?, ?, ?, ?, datetime('now', '+10 minutes'))
        """,
        (email, name, hashed_password, otp)
    )

    conn.commit()
    conn.close()

    if send_email_otp(email, otp, is_signup=True):
        return jsonify({
            "success": True,
            "message": "OTP sent successfully"
        })
    else:
        return jsonify({
            "error": "Failed to send OTP"
        }), 500
@app.route("/signup_verify", methods=["POST"])
#@app.route("/signup_verify", methods=["POST"])
def signup_verify():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")

    conn = get_db()

    print("Email entered:", email)
    print("OTP entered:", otp)

    temp_user = conn.execute(
        "SELECT * FROM temp_users WHERE email = ? AND otp = ? AND otp_expiry >= datetime('now')",
        (email, otp)
    ).fetchone()

    print("Database result:", temp_user)

    if temp_user:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (temp_user["name"], email, temp_user["password"])
        )

        user_id = cursor.lastrowid

        conn.execute(
            "DELETE FROM temp_users WHERE email = ?",
            (email,)
        )

        conn.commit()
        conn.close()

        session["user"] = temp_user["name"]
        session["user_id"] = user_id

        return jsonify({
            "success": True,
            "message": "Account verified and created successfully"
        })

    conn.close()
    return jsonify({"error": "Invalid or expired OTP"}), 400

@app.route("/logout")
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

# ------------------ PREDICT ------------------
@app.route("/predict", methods=["POST"])
def predict():
    if 'user' not in session:
        return "Unauthorized", 401

    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    file_bytes = file.read()
    img = preprocess_image(BytesIO(file_bytes))

    npimg = np.frombuffer(file_bytes, np.uint8)
    original_img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    original_img = cv2.resize(original_img, IMG_SIZE)

    preds = model.predict(img)[0]
    class_index = np.argmax(preds)
    confidence = float(preds[class_index])
    label = CLASS_MAP[class_index]

    # GRAD-CAM
    last_conv_layer = None
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            last_conv_layer = layer.name
            break

    heatmap_img_base64 = None
    if last_conv_layer:
        grad_model = tf.keras.models.Model(
            [model.inputs],
            [model.get_layer(last_conv_layer).output, model.output]
        )
        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(img)
            class_channel = predictions[:, np.argmax(predictions[0])]
        grads = tape.gradient(class_channel, conv_outputs)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        conv_outputs = conv_outputs[0]
        heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap).numpy()
        heatmap = np.maximum(heatmap, 0)
        if np.max(heatmap) != 0:
            heatmap /= np.max(heatmap)

        heatmap = cv2.resize(heatmap, (IMG_SIZE[1], IMG_SIZE[0]))
        heatmap = np.uint8(255 * heatmap)
        heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        superimposed = cv2.addWeighted(original_img, 0.6, heatmap_colored, 0.4, 0)
        
        _, buffer = cv2.imencode('.jpg', superimposed)
        heatmap_img_base64 = base64.b64encode(buffer).decode('utf-8')

    session['last_prediction'] = label
    session['confidence'] = confidence

    # STORE HISTORY + COMPARE using DB
    conn = get_db()
    user_id = session.get('user_id')
    previous = None

    if user_id:
        prev_record = conn.execute('SELECT prediction FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,)).fetchone()
        if prev_record:
            previous = prev_record['prediction']
            
        conn.execute('INSERT INTO history (user_id, prediction, confidence) VALUES (?, ?, ?)', (user_id, label, confidence))
        conn.commit()
    conn.close()

    explanation = ask_llm(label, confidence)

    return jsonify({
        "prediction": str(label).strip().lower(),
        "confidence": float(round(confidence, 3)),
        "explanation": explanation,
        "heatmap": heatmap_img_base64,
        "previous_prediction": previous
    })

# ------------------ CHATBOT ------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    context = f"""
    Previous MRI Result:
    Prediction: {session.get('last_prediction')}
    Confidence: {session.get('confidence')}
    """
    prompt = f"You are a brain health assistant. Do NOT diagnose. Context: {context} User: {message}"

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=LLM_MODEL,
        )
        return {"reply": chat_completion.choices[0].message.content}
    except Exception as e:
        print("CHAT ERROR:", e)
        return {"reply": "Chatbot temporarily unavailable."}

# ------------------ OTP / PASSWORD RESET ------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL")  
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") 

def send_email_otp(recipient, otp, is_signup=False):
    try:
        subject = "brAIn - Verify your email" if is_signup else "brAIn - Password Reset OTP"
        msg = MIMEText(f"Your OTP is: {otp}\nIt will expire in 10 minutes.")
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Email sending error:", e)
        return False

@app.route("/send_otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400
        
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    is_signup_flow = False
    
    if not user:
        # Check if it's a pending signup
        user = conn.execute('SELECT * FROM temp_users WHERE email = ?', (email,)).fetchone()
        is_signup_flow = True
    
    if not user:
        conn.close()
        return jsonify({"error": "Account not found"}), 404
        
    otp = str(random.randint(1000, 9999))
    
    if send_email_otp(email, otp, is_signup=is_signup_flow):
        if is_signup_flow:
            conn.execute("UPDATE temp_users SET otp = ?, otp_expiry = datetime('now', '+10 minutes') WHERE email = ?", (otp, email))
        else:
            conn.execute("UPDATE users SET otp = ?, otp_expiry = datetime('now', '+10 minutes') WHERE email = ?", (otp, email))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "OTP sent", "otp": otp})
    else:
        conn.close()
        return jsonify({"error": "Failed to send email. Please check SMTP configuration."}), 500

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if user and user['otp'] == otp:
        valid = conn.execute("SELECT 1 FROM users WHERE email = ? AND otp = ? AND otp_expiry >= datetime('now')", (email, otp)).fetchone()
        if valid:
            conn.close()
            return jsonify({"success": True, "message": "OTP verified"})
        else:
            conn.close()
            return jsonify({"error": "OTP has expired"}), 400
            
    conn.close()
    return jsonify({"error": "Invalid OTP"}), 400

@app.route("/reset_password", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data.get("email")
    new_password = data.get("password")
    
    if not email or not new_password:
        return jsonify({"error": "Email and new password are required"}), 400
        
    hashed_password = generate_password_hash(new_password)
    
    conn = get_db()
    conn.execute("UPDATE users SET password = ?, otp = NULL, otp_expiry = NULL WHERE email = ?", (hashed_password, email))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Password reset successfully"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)