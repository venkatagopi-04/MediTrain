# MediTrain - AI-powered Medical Symptom Classifier and Assistant

## Overview

MediTrain is an AI-powered web application designed to classify symptoms, provide medical condition predictions, and suggest remedies. Utilizing Google Generative AI and MySQL for user interaction tracking, MediTrain ensures accurate medical assistance while reminding users to consult healthcare professionals for proper diagnosis and treatment.

## Features

* **Symptom Classification**: Classifies user input into relevant medical symptom classes.
* **Follow-up Interaction**: Engages users with follow-up questions to further refine symptom assessment.
* **Condition Prediction**: Suggests probable medical conditions based on symptom analysis.
* **Remedy Suggestions**: Provides remedies and common tablets based on identified conditions.
* **User Interaction Logging**: Tracks user queries and responses for ongoing assistance.

## Prerequisites

To run MediTrain locally, ensure you have the following:

* Python 3.8+
* A valid **Google Generative AI API key** in the `config.json` file
* Libraries specified in `requirements.txt`
* MySQL installed and set up for database interaction

## Installation

1. Clone this repository:
   
   git clone https://github.com/your-username/MediTrain.git
   cd MediTrain
   

2. Create a virtual environment and activate it:
   
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
 

3. Install the dependencies:

   pip install -r requirements.txt


4. Set up your environment variables by creating a `config.json` file in the root directory with the following content:
   
   {
     "GENAI_API_KEY": "your_google_generative_ai_api_key"
   }
  

5. Ensure your MySQL database is configured. The script will automatically create the required table `user_interactions`.

## Usage

1. Run the application:
   
   python app.py
  

2. Open the application in your browser (default: [http://localhost:5000](http://localhost:5000/)).

3. Interact with MediTrain by typing medical queries in the provided input box.

## Project Structure

* **`app.py`** : Main Flask application script.
* **`requirements.txt`** : List of required Python packages.
* **`config.json`** : Configuration file containing sensitive API keys (not included in the repository).
* **`Symptoms_Dataset.xlsx`** : Excel dataset for symptom classification, conditions, remedies, and follow-up questions.

## Key Libraries

* **Flask**: For building the web application.
* **Google Generative AI (Gemini)**: Powers the symptom classification and follow-up response generation.
* **MySQL**: For storing user interactions and responses.
* **Pandas**: For managing and processing the symptom dataset.
* **Python-dotenv**: For managing environment variables.

## Important Notes

* MediTrain is designed as a symptom classifier and assistant but does not provide medical diagnoses or treatment plans.
* Always consult a certified healthcare professional for medical concerns.

## Future Enhancements

* Implement a richer conversation flow for more personalized assistance.
* Improve AI models for more accurate symptom classification and treatment suggestions.
* Add real-time alerts or notifications for urgent conditions.

## License

This project is licensed under the MIT License.
