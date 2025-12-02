from flask import Flask, render_template, request, jsonify
from teacher_ai import TeacherAssistant
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', '5242880'))  # 5MB default

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

assistant = TeacherAssistant()

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}

# System prompts for each service
SUMMARIZATION_PROMPT = """SYSTEM:
You are Teacher AI focused on academic summarizer. ONLY produce study-related output.

REQUIREMENTS (must follow exactly):
1. If input is not study-related, reply with exactly: "I can only help with study-related questions."
2. Do NOT ask clarifying questions. Backend will provide subject/grade if needed.
3. Primary output format:
   - Headline: Output type: Summary
   - 4-6 bullet points (each under 20 words)
   - One line key takeaway
4. Keep total summary length less than 200 words.

End of instructions."""

QA_PROMPT = """SYSTEM:
You are Teacher AI Assistant for academic Q&A. ONLY provide study-centered answers. If user enters anything unrelated to study, reply exactly: "I can only help with study-related questions. Please enter a topic or academic question."

RESPONSE FORMAT (must follow exactly):
1. Top header line: "Explanation"
2. Short definition (1-2 sentences) starting with "Definition:"
3. Concise explanation in 3-6 bullet points.
4. One short example labelled "Example:"
5. Total answer length less than 300 words.

End of instructions."""

QUESTION_GENERATOR_PROMPT = """SYSTEM:
You are Teacher AI generate exam-style questions. If user input unrelated to study, reply exactly: "I can help with study-related questions. Please enter a topic or academic text."

REQUIREMENTS (must follow exactly):
1. Generate exactly the number of questions required.
2. Question types: give options before generating MCQ or Subjective
3. For each question produce a JSON array element with keys:
   {
     "question": "<text>",
     "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
     "answer": "A"|"B"|"C"|"D",
     "explanation": "<one-sentence explanation>"
   }
4. Difficulty level: honor backend "difficulty" (easy/medium/hard) by adjusting distractor plausibility:
   - easy: straightforward concept checks
   - medium: require 1–2 reasoning steps
   - hard: multi-step reasoning or applied problems
5. Explain in less than 25 words
6. If user provide file content base question on that context. Otherwise use domain knowledge of the topic.
7. If request ask for non educational or harmful material reply exactly: "I cannot reply with that. Please provide study-related topic"

End of instructions."""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    chapter_text = data.get('chapter_text', '')
    chapter_title = data.get('chapter_title', '')
    file_content = data.get('file_content', '')
    
    # Use file content or topic only
    if file_content:
        # File uploaded - summarize document
        combined_text = file_content
        chapter_title = chapter_title or "Uploaded Document"
    else:
        # Topic provided - use knowledge base
        combined_text = ""
    
    try:
        summary = assistant.summarize_chapter(combined_text, chapter_title, SUMMARIZATION_PROMPT)
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    data = request.json
    topic = data.get('topic', '')
    count = data.get('count', 5)
    difficulty = data.get('difficulty', 'medium')
    question_type = data.get('question_type', 'mcq')
    file_content = data.get('file_content', '')
    
    # Use file content as topic if no topic provided
    if not topic and file_content:
        topic = f"Generate questions based on this content:\n{file_content}"
    elif file_content:
        topic = f"{topic}\n\nContext: {file_content}"
    
    try:
        print(f"DEBUG - Generating questions: topic={topic}, count={count}, difficulty={difficulty}, type={question_type}")
        questions = assistant.generate_test_questions(topic, count, difficulty, QUESTION_GENERATOR_PROMPT, question_type)
        print(f"DEBUG - Generated {len(questions)} questions")
        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        print(f"DEBUG - Flask error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/ask_question', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question', '')
    
    try:
        answer = assistant.answer_question(question, QA_PROMPT)
        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type'})
    
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        if file_ext in ['jpg', 'jpeg', 'png']:
            content = assistant.process_image(file_path, SUMMARIZATION_PROMPT)
        else:
            content = assistant.extract_text_from_file(file_path, file_ext, SUMMARIZATION_PROMPT)
        
        os.remove(file_path)
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(debug=debug_mode, host=host, port=port)