# 🛡️ RakshaUID: Identity Defense System

**RakshaUID** is an advanced AI-powered identity verification platform designed to detect Aadhaar fraud. It combines Deep Learning (CNN), Optical Character Recognition (OCR), and Biometric Face Verification into a strict 3-stage security workflow to ensure only authentic identities are verified.

---

## 🚀 Key Features

* **🔍 3-Stage Verification Workflow:**
    1.  **Document Analysis:** Uses a trained **CNN Model (TensorFlow)** to distinguish valid Aadhaar cards from non-Aadhaar documents.
    2.  **Biometric Face Match:** Uses **OpenCV (LBPH Face Recognizer)** to match the photo on the ID card with a live webcam feed or uploaded user photo.
    3.  **Data Extraction & QR Validation:** Extracts text using **PaddleOCR** and cross-references it with the decoded **QR Code** data for consistency.
    

* **🤖 Fraud Detection Engine:** Analyzes image forensics (tampering traces), data consistency, and ML-based fraud probability scores.
* **📂 Secure Database:** Stores verified records in **SQLite** for instant future lookups and duplicate prevention.
* **💻 Interactive Dashboard:** A modern, responsive web interface built with **FastAPI** and **JavaScript** featuring Dark/Light mode and real-time status updates.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.10+, FastAPI, Uvicorn
* **Deep Learning:** TensorFlow / Keras (CNN Classification)
* **Computer Vision:** OpenCV (`opencv-contrib-python`), PaddleOCR
* **Machine Learning:** Scikit-Learn (Random Forest for Fraud Probability)
* **Database:** SQLite
* **Frontend:** HTML5, CSS3, JavaScript (Fetch API)
