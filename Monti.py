from flask import Flask, render_template, request, send_from_directory
import google.generativeai as genai
import os
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

genai.configure(api_key="AIzaSyBloUL0um1Ft54FIONSP03EmY7jvAR5c6Q")

@app.route('/', methods=['GET', 'POST'])
def index():
    story = ""
    consequences = ""
    schema = ""
    scope = ""
    trace = ""
    model_file_url = None

    if request.method == 'POST':
        prompt_type = request.form.get("prompt_type")
        behavior_type = request.form.get("behavior_type")
        sentiment = request.form.get("sentiment")

        # Handle uploaded trace file (.mp or .txt)
        trace_file = request.files.get('trace_file')
        if trace_file:
            trace_filename = trace_file.filename
            content = trace_file.read().decode(errors="ignore")

            # Extract schema/scope/trace
            match = re.match(r"([A-Za-z0-9_]+)_scope_(\d+)_trace_(\d+)", trace_filename)
            if match:
                schema = match.group(1)
                scope = match.group(2)
                trace = match.group(3)

            # Prompt formatting
            base_prompt = f"""
            Tell me a narrative based on the attached model and image. Tell a story. Ensure that the story follows the subject of the attached image.
            Suggest a classification level of behaviors - unexpected, expected, positive, negative, neutral.

            Trace input:
            {content}

            Response format:
            Story:
            <Insert detailed story>

            Consequence:
            <Insert summary consequence>
            """

            model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
            response = model.generate_content(base_prompt)
            result = response.text

            if "Consequence:" in result:
                parts = result.split("Consequence:")
                story = parts[0].replace("Story:", "").strip()
                consequences = parts[1].strip()
            else:
                story = result
                consequences = "No separate consequence found — see story above."

        # Save image to static/uploads/
        model_image = request.files.get('model_file')
        if model_image and model_image.filename:
            filename = secure_filename(model_image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            model_image.save(filepath)
            model_file_url = f"/{filepath}"

    return render_template(
        'index.html',
        story=story,
        consequences=consequences,
        schema=schema,
        scope=scope,
        trace=trace,
        model_file_url=model_file_url
    )

if __name__ == '__main__':
    app.run(debug=True)
