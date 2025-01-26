from flask import Flask, request, jsonify, render_template
import pandas as pd
import json  # Add this import statement at the top

import google.generativeai as genai
import mysql.connector
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)


with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Configure API key for generative model
genai.configure(api_key=config["GENAI_API_KEY"])

# API key configuration for generative model


# Load dataset
file_path = "Symptoms_Dataset.xlsx"  # Path to your Excel dataset
data = pd.read_excel(file_path)

# List of symptom classes
symptom_classes = list(data["Symptom"].unique())

# Configure MySQL connection
conn = mysql.connector.connect(
    host="localhost",  # Replace with your database host
    user="root",       # Replace with your database username
    password="",       # Replace with your database password
    database="meditrain"  # Replace with your database name
)
cursor = conn.cursor()

# Create tables if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_input TEXT NOT NULL,
    symptom_class VARCHAR(255) NOT NULL,
    question TEXT,
    answer TEXT,
    probable_condition TEXT,
    remedies TEXT,
    suggestions TEXT,
    common_tablets TEXT,
    followup_questions JSON,
    followup_answers JSON,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()

# Function to classify the symptom
def classify_symptom(user_input, symptom_classes):
    prompt = (
        "Classify the following input into one of the provided symptom classes:\n\n"
        f"Input: {user_input}\n\n"
        f"Symptom Classes: {', '.join(symptom_classes)}\n\n"
        "Answer with the most relevant symptom class."
    )
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    if response:
        return response.text.strip()
    else:
        return None

# Function to classify follow-up answers
def classify_followup(user_responses, possible_answers):
    user_input_summary = " ".join(user_responses)  # Combine all user inputs into a single string
    prompt = (
        f"User Responses: {user_input_summary}\n\n"
        f"Possible Answers: {', '.join(possible_answers)}\n\n"
        "Based on user responses, return a guaranteed possible answer."
    )
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    if response:
        return response.text.strip()
    else:
        return None

# Home route
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/about")
def about():
    return render_template("about.html")



# API route for symptom classification
@app.route("/classify_symptom", methods=["POST"])
def classify_symptom_api():
    user_input = request.json.get("user_input", "")

    if not user_input:
        return jsonify({"error": "Invalid input"}), 400

    # Predict symptom class
    predicted_symptom = classify_symptom(user_input, symptom_classes)
    if not predicted_symptom:
        return jsonify({"error": "Failed to classify symptom"}), 500

    # Fetch follow-up questions
    symptom_data = data[data["Symptom"] == predicted_symptom]
    followup_questions = symptom_data["Follow-up Question"].drop_duplicates().tolist()

    # Save to database
    cursor.execute(
        "INSERT INTO user_interactions (user_input, symptom_class) VALUES (%s, %s)",
        (user_input, predicted_symptom)
    )
    conn.commit()

    return jsonify({
        "predicted_symptom": predicted_symptom,
        "followup_questions": followup_questions
    })

@app.route("/handle_followup", methods=["POST"])
def handle_followup():
    current_question_index = request.json.get("question_index", 0)
    user_responses = request.json.get("user_responses", [])
    symptom = request.json.get("symptom", "")

    if not user_responses or not symptom:
        return jsonify({"error": "Invalid input"}), 400

    # Get all follow-up questions for the symptom
    symptom_data = data[data["Symptom"] == symptom]
    followup_questions = symptom_data["Follow-up Question"].drop_duplicates().tolist()

    # Validate question index
    if current_question_index >= len(followup_questions):
        return jsonify({"error": "Invalid question index"}), 400

    # Fetch the current question
    current_question = followup_questions[current_question_index]

    # Retrieve the existing entry for the user and symptom
    cursor.execute(
        "SELECT id, followup_questions, followup_answers FROM user_interactions WHERE symptom_class = %s ORDER BY id DESC LIMIT 1",
        (symptom,)
    )
    result = cursor.fetchone()

    # Initialize follow-up lists
    followup_questions_list = []
    followup_answers_list = []

    if result:
        interaction_id, questions_json, answers_json = result
        followup_questions_list = json.loads(questions_json) if questions_json else []
        followup_answers_list = json.loads(answers_json) if answers_json else []

    # Append the current question and user response
    followup_questions_list.append(current_question)
    followup_answers_list.append(user_responses[-1])

    # Save updated lists to the database
    cursor.execute(
        """
        UPDATE user_interactions SET 
        followup_questions = %s, 
        followup_answers = %s 
        WHERE id = %s
        """,
        (json.dumps(followup_questions_list), json.dumps(followup_answers_list), interaction_id)
    )
    conn.commit()

    # Check if it's the last follow-up question
    if current_question_index == len(followup_questions) - 1:
        # Classify collected user inputs
        possible_answers = symptom_data["Answer"].unique()
        if len(possible_answers) == 0:
            return jsonify({"error": "No possible answers available"}), 404

        classified_answer = classify_followup(user_responses, possible_answers)

        if not classified_answer:
            return jsonify({"error": "Failed to classify answer"}), 500

        # Match the classified answer
        classified_answer_lower = classified_answer.lower()
        matched_answer = None

        for answer in possible_answers:
            if answer.lower() in classified_answer_lower:
                matched_answer = answer
                break

        if not matched_answer:
            return jsonify({"error": "No matching answer found"}), 404

        # Fetch matched row
        matched_row = symptom_data[symptom_data["Answer"] == matched_answer]
        if matched_row.empty:
            return jsonify({"error": "No matching data found"}), 404

        # Prepare response details
        details = {
            "condition": matched_row.iloc[0]["Probable Condition"],
            "remedies": matched_row.iloc[0]["Remedies"],
            "suggestions": matched_row.iloc[0]["Suggestions"],
            "common_tablets": matched_row.iloc[0]["Common Tablets"]
        }

        # Save diagnosis results to database
        cursor.execute(
            """
            UPDATE user_interactions SET 
            probable_condition = %s, 
            remedies = %s, 
            suggestions = %s, 
            common_tablets = %s 
            WHERE id = %s
            """,
            (details["condition"], details["remedies"], details["suggestions"], details["common_tablets"], interaction_id)
        )
        conn.commit()

        return jsonify({"details": details, "is_complete": True})

    # Otherwise, proceed to the next follow-up question
    next_question_index = current_question_index + 1
    next_question = followup_questions[next_question_index]

    return jsonify({
        "next_question": next_question,
        "next_question_index": next_question_index,
        "is_complete": False
    })



@app.route("/get_user_interactions", methods=["GET"])
def get_user_interactions():
    cursor.execute("SELECT * FROM user_interactions ORDER BY timestamp DESC")
    rows = cursor.fetchall()

    user_interactions = []
    for row in rows:
        interaction = {
            "id": row[0],
            "user_input": row[1],
            "symptom_class": row[2],
            "question": row[3],
            "answer": row[4],
            "probable_condition": row[5],
            "remedies": row[6],
            "suggestions": row[7],
            "common_tablets": row[8],
            "timestamp": row[9],
            "followup_questions": json.loads(row[10]) if row[10] else [],
            "followup_answers": json.loads(row[11]) if row[11] else []
        }
        user_interactions.append(interaction)

    return jsonify(user_interactions)



# Run the app
if __name__ == "__main__":
    app.run(debug=True)
