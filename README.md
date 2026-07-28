# 🧠 Brain Tumor Detection System

An AI-powered web application that detects brain tumors from MRI images using a Deep Learning model (VGG19). The project provides an easy-to-use web interface for MRI image upload, prediction, Grad-CAM visualization, secure OTP authentication, and an AI chatbot for educational purposes.

> **⚠ Disclaimer:** This project is developed **only for educational and research purposes**. It is **not a medical device** and must **not** be used for clinical diagnosis or treatment decisions.

---

#  Features

-  Brain Tumor Detection using Deep Learning (VGG19)
-  Upload MRI Brain Images
-  Predict Tumor Type
-  Grad-CAM Heatmap Visualization
-  Email OTP Authentication
-  AI Chatbot powered by Groq API
-  SQLite Database
-  Responsive Web Interface

---

#  Technologies Used

## Frontend
- HTML5
- CSS3
- JavaScript

## Backend
- Python
- Flask

## Database
- SQLite

## Deep Learning
- TensorFlow
- Keras
- VGG19

## Other Tools
- Groq API
- SMTP Email
- Git & GitHub

---

#  Project Structure

```
Brain-Tumor-Detection-System-Academic-

│── app.py
│── requirements.txt
│── runtime.txt
│── Profile
│── README.md
│
├── static/
├── templates/
├── team_25/
│
├── brain_tumour.ipynb
├── train_model.ipynb
```

---

#  Installation

## 1. Clone the Repository

```bash
git clone https://github.com/sinchana-kt/Brain-Tumor-Detection-System-Academic-.git
```

## 2. Open the Project

```bash
cd Brain-Tumor-Detection-System-Academic-
```

## 3. Install Required Packages

```bash
pip install -r requirements.txt
```

## 4. Download the Trained Model

The trained model (`final_model.keras`) is not included in this repository because GitHub does not allow files larger than 100 MB.

Place the downloaded model in the project root folder before running the application.

## 5. Run the Application

```bash
python app.py
```

---

#  Model Information

- Model: **VGG19**
- Framework: TensorFlow / Keras
- Dataset: Brain MRI Images
- Output Classes:
  - Glioma
  - Meningioma
  - Pituitary
  - No Tumor

---

#  Screenshots

You can add screenshots of:

- Home Page
- MRI Upload Page
- Prediction Result
- Grad-CAM Visualization
- AI Chatbot

---

#  Future Improvements

- Deploy on Cloud
- User Dashboard
- Medical Report Generation
- Model Performance Analytics
- Multi-language Support

---

#  Developer

**Sinchana K T**

Bachelor of Engineering (Computer Science & Engineering)

Academic Project – Brain Tumor Detection System

---

#  Support

If you find this project useful, please consider giving it a  on GitHub.