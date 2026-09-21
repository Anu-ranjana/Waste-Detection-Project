# 🚮 AI-Powered Waste Detection & Anti-Littering System

An AI-based computer vision project combining **waste detection, anti-littering monitoring, and intelligent violation management** to support cleaner and more sustainable environments.

The project integrates YOLO-based object detection with computer vision techniques to identify waste, monitor littering-related activities, and support automated environmental monitoring.

---

## 📌 Project Overview

Waste accumulation and littering are major environmental challenges in urban and public spaces. Manual monitoring can be time-consuming and difficult to scale.

This project combines two computer vision applications into a unified repository:

* **YOLO Waste Detection:** Detects and analyzes waste using trained object detection models.
* **Anti-Littering System:** Uses computer vision-based monitoring, pose detection, and facial recognition components to support littering violation identification and fine management.

The combined system is designed to explore how artificial intelligence can assist in environmental monitoring and anti-littering initiatives.

---

## ✨ Key Features

### 🚮 1. YOLO Waste Detection

* AI-based waste detection using YOLO.
* Image-based waste analysis.
* Video-based monitoring support.
* Camera detection functionality.
* Web interface for waste detection.
* Detection results and event data management.

### 🛡️ 2. Anti-Littering System

* Computer vision-based activity monitoring.
* Pose detection using MoveNet.
* Face recognition components.
* Fine management using an Excel database.
* Web-based monitoring interface.
* Automated workflow scripts for application execution.

### 🤖 3. Integrated Computer Vision

* Trained machine learning models.
* Image and video processing.
* Computer vision pipelines.
* Modular Python implementation.
* Separate application components within one combined repository.

---

## 🏗️ Project Architecture

```text
AI-Powered Waste Detection & Anti-Littering System
│
├── YOLO Waste Detection
│   ├── Image Detection
│   ├── Video Detection
│   ├── Camera Monitoring
│   ├── Waste Detection Model
│   └── Web Interface
│
└── Anti-Littering System
    ├── Pose Detection (MoveNet)
    ├── Face Recognition
    ├── Fine Management
    ├── Computer Vision Pipeline
    └── Web Application
```

---

## 📂 Repository Structure

```text
Waste-Detection-Project/
│
├── Anti-Littering-System-Computer-Vision/
│   ├── FineDatabase/
│   │   └── fines.xlsx
│   ├── MoveNet/
│   │   └── tflite/
│   ├── webapp/
│   │   ├── static/
│   │   ├── templates/
│   │   ├── app.py
│   │   └── pipeline.py
│   ├── IntegratedArchitecture.py
│   ├── move-net.py
│   ├── best.pt
│   ├── requirements.txt
│   ├── install_requirements.bat
│   ├── run.bat
│   └── run_web.bat
│
├── YOLO-Waste-Detection/
│   ├── Image/
│   ├── data/
│   ├── static/
│   ├── templates/
│   ├── app.py
│   ├── waste_detector.py
│   ├── throwing_waste_detector.py
│   ├── detect_camera.py
│   ├── smoking_detector.py
│   ├── email_notifier.py
│   ├── best_model.pt
│   ├── smoking_model.pt
│   ├── Waste_Detection.ipynb
│   ├── requirements
│   ├── run.bat
│   └── run_web.bat
│
├── .gitignore
└── README.md
```

---

## 🛠️ Technologies Used

| Technology                     | Purpose                            |
| ------------------------------ | ---------------------------------- |
| Python                         | Core programming language          |
| YOLO                           | Object detection                   |
| Computer Vision                | Image and video analysis           |
| MoveNet                        | Pose detection                     |
| Face Recognition               | Facial identification components   |
| Flask / Python Web Application | Web interface components           |
| JavaScript                     | Frontend interaction               |
| HTML & CSS                     | Web interface                      |
| OpenCV                         | Computer vision processing         |
| Jupyter Notebook               | Model experimentation and analysis |

*Note: Confirm the exact frameworks and libraries in your requirements files before finalizing the technology list.*

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Anu-ranjana/Waste-Detection-Project.git
```

Navigate to the project directory:

```bash
cd Waste-Detection-Project
```

### 2. Set Up the Environment

Make sure Python is installed on your system.

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

For the YOLO Waste Detection module:

```bash
cd YOLO-Waste-Detection
pip install -r requirements.txt
```

For the Anti-Littering System:

```bash
cd ..\Anti-Littering-System-Computer-Vision
pip install -r requirements.txt
```

### 4. Run the Applications

Follow the instructions in each module's README and startup scripts to launch the relevant application.

---

## 🧪 Project Applications

### Waste Detection

The YOLO module includes scripts for waste detection using images, videos, and camera input.

### Anti-Littering Monitoring

The anti-littering module includes computer vision pipelines, pose detection components, face recognition-related files, and fine management functionality.

**Implementation details and supported workflows should be verified against the application code.**

---

## 🌍 Potential Impact

* Supports AI-assisted environmental monitoring.
* Helps explore automated waste detection.
* Demonstrates computer vision applications for anti-littering initiatives.
* Provides a modular foundation for future smart-city and sustainability projects.

---

## 🔮 Future Enhancements

* Real-time waste detection optimization.
* Improved littering event classification.
* Enhanced dashboard and analytics.
* Cloud-based deployment.
* Notification and reporting improvements.
* Model performance evaluation.
* Integration with broader environmental monitoring systems.

---

## 👩‍💻 Author

**Anu-ranjana**

GitHub: [@Anu-ranjana](https://github.com/Anu-ranjana)

---

## 📄 License

Refer to the LICENSE files included in the respective project directories for licensing information.

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub!
