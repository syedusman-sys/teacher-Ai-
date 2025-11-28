import google.generativeai as genai
import json
import os
from typing import List, Dict
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

class TeacherAssistant:
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("API key not found. Set GEMINI_API_KEY in .env file or pass it directly.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.5,
            top_p=0.8,
            top_k=40
        )
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        if file_type == 'pdf':
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        elif file_type == 'docx':
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        return ""
    
    def process_image(self, image_path: str) -> str:
        image = Image.open(image_path)
        prompt = "Extract all text, diagrams, charts, and educational content from this image. Provide a detailed description of everything visible that could be used for educational purposes."
        response = self.model.generate_content([prompt, image], generation_config=self.generation_config)
        return response.text
    
    def summarize_chapter(self, chapter_text: str, chapter_title: str = "") -> str:
        if chapter_text.strip():
            prompt = f"""Summarize this content in a clear, educational format suitable for teachers:
        
Title: {chapter_title}
Content: {chapter_text}

Provide a concise summary highlighting key concepts, main ideas, and important details."""
        else:
            prompt = f"""Create a comprehensive educational summary for the topic: {chapter_title}

Using your knowledge base, provide a detailed summary covering:
- Key concepts and definitions
- Main ideas and principles
- Important details and examples
- Educational insights for teachers

Make it suitable for classroom use."""
        
        response = self.model.generate_content(prompt, generation_config=self.generation_config)
        return response.text
    
    def answer_question(self, question: str) -> str:
        prompt = f"""As an educational assistant, provide a comprehensive answer to this question:

Question: {question}

Provide a clear, educational response that includes:
- Direct answer to the question
- Key concepts and explanations
- Examples if relevant
- Additional context for better understanding

Make it suitable for educational purposes."""
        
        response = self.model.generate_content(prompt, generation_config=self.generation_config)
        return response.text
    
    def generate_test_questions(self, topic: str, question_count: int = 5, difficulty: str = "medium") -> List[Dict]:
        prompt = f"""Generate exactly {question_count} {difficulty} difficulty multiple choice questions about: {topic}

Format EXACTLY as shown:

Question 1: [Question text here]
A) [Option A]
B) [Option B] 
C) [Option C]
D) [Option D]
Answer: [Correct letter]
Explanation: [Brief explanation]

Question 2: [Question text here]
A) [Option A]
B) [Option B]
C) [Option C] 
D) [Option D]
Answer: [Correct letter]
Explanation: [Brief explanation]

Generate exactly {question_count} questions following this format."""
        
        response = self.model.generate_content(prompt, generation_config=self.generation_config)
        return self._parse_questions(response.text, question_count)
    
    def _parse_questions(self, response_text: str, expected_count: int) -> List[Dict]:
        questions = []
        lines = response_text.split('\n')
        current_q = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('Question '):
                if current_q and len(current_q.get('options', [])) == 4:
                    questions.append(current_q)
                current_q = {'question': line.split(':', 1)[1].strip() if ':' in line else line, 'options': [], 'answer': '', 'explanation': ''}
            elif line.startswith(('A)', 'B)', 'C)', 'D)')) and current_q:
                current_q['options'].append(line)
            elif line.startswith('Answer:') and current_q:
                current_q['answer'] = line[7:].strip()
            elif line.startswith('Explanation:') and current_q:
                current_q['explanation'] = line[12:].strip()
        
        if current_q and len(current_q.get('options', [])) == 4:
            questions.append(current_q)
        
        return questions[:expected_count]

# Usage example
if __name__ == "__main__":
    # Initialize assistant
    assistant = TeacherAssistant()
    
    # Example usage
    sample_chapter = """
    Photosynthesis is the process by which plants convert light energy into chemical energy.
    This process occurs in chloroplasts and involves two main stages: light reactions and Calvin cycle.
    """
    
    # Summarize chapter
    summary = assistant.summarize_chapter(sample_chapter, "Chapter 8: Photosynthesis")
    print("Summary:", summary)
    
    # Generate test questions
    questions = assistant.generate_test_questions("Photosynthesis", 3, "medium")
    for i, q in enumerate(questions, 1):
        print(f"\nQuestion {i}: {q['question']}")
        for option in q['options']:
            print(option)
        print(f"Answer: {q['answer']}")