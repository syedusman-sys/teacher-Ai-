from flask import Flask, render_template, request, jsonify
from teacher_ai import TeacherAssistant
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs('uploads', exist_ok=True)

assistant = TeacherAssistant()

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}

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
        summary = assistant.summarize_chapter(combined_text, chapter_title)
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    data = request.json
    topic = data.get('topic', '')
    count = data.get('count', 5)
    difficulty = data.get('difficulty', 'medium')
    file_content = data.get('file_content', '')
    
    # Use file content as topic if no topic provided
    if not topic and file_content:
        topic = f"Generate questions based on this content:\n{file_content}"
    elif file_content:
        topic = f"{topic}\n\nContext: {file_content}"
    
    try:
        questions = assistant.generate_test_questions(topic, count, difficulty)
        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/ask_question', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question', '')
    
    try:
        answer = assistant.answer_question(question)
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
            content = assistant.process_image(file_path)
        else:
            content = assistant.extract_text_from_file(file_path, file_ext)
        
        os.remove(file_path)
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)