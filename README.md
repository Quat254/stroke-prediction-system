# Omeka Stroke Prediction System

# Stroke Prediction System

## Overview

The Stroke Prediction System is a machine learning-based web application designed to assess an individual's risk of stroke using health-related data. The system analyzes key medical indicators and applies a trained machine learning model to generate predictions that may help support early risk awareness and preventative healthcare decisions.

This project demonstrates how data science and machine learning can be applied to healthcare analytics and predictive modelling.

## Features

* User registration and authentication
* Stroke risk prediction using a trained machine learning model
* Health data input and analysis
* Assessment history tracking
* Administrative dashboard for system monitoring
* User feedback system
* System announcements for users

## Technologies Used

* **Python**
* **Scikit-learn**
* **Pandas**
* **NumPy**
* **Flask (Web Framework)**
* **HTML / CSS / JavaScript**
* **Machine Learning Algorithms**

## Machine Learning Workflow

The prediction model follows a standard machine learning pipeline:

1. **Data Collection** – Healthcare dataset containing patient risk indicators.
2. **Data Preprocessing** – Handling missing values and feature normalization.
3. **Feature Selection** – Identifying key predictors such as age, hypertension, BMI, and glucose level.
4. **Model Training** – Training machine learning models using Scikit-learn.
5. **Model Evaluation** – Testing model accuracy and prediction performance.
6. **Deployment** – Integrating the trained model into a Flask web application.

## Project Structure

```
stroke-prediction-system/
│
├── app/                 # Web application files
├── model/               # Machine learning model
├── dataset/             # Stroke dataset
├── templates/           # HTML frontend pages
├── static/              # CSS, JS and assets
├── StrokeApp.sh         # Script to run the application
└── requirements.txt     # Project dependencies
```

## Installation

Clone the repository:

```bash
git clone https://github.com/Quat254/stroke-prediction-system.git
cd stroke-prediction-system
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
./StrokeApp.sh
```

Once the application starts, open your web browser and navigate to the provided URL.

## How the System Works

Users enter relevant health data such as age, BMI, hypertension status, and other indicators. The system processes the input data through a trained machine learning model that predicts the likelihood of stroke risk. The prediction results are displayed through a user-friendly web interface.

## Learning Outcomes

This project helped develop practical experience in:

* Machine learning model development
* Data preprocessing and analysis
* Predictive healthcare analytics
* Backend development using Flask
* Integrating ML models into web applications

## Future Improvements

* Improve model accuracy using advanced algorithms
* Add real-time health monitoring integrations
* Implement data visualization dashboards
* Deploy the system as a cloud-based application

## Access

Once running, access the application through your web browser at the displayed URL.

## Support

Contact system administrator for assistance.
