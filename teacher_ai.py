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
            temperature=0.2,
            top_p=0.8,
            top_k=40
        )
    
    def extract_text_from_file(self, file_path: str, file_type: str, system_prompt: str = "") -> str:
        if file_type == 'pdf':
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        elif file_type == 'docx':
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        else:
            text = ""
        
        if system_prompt and text.strip():
            user_prompt = f"Extract and summarize the educational content from this text: {text}"
            final_prompt = f"{system_prompt}\n\nUSER REQUEST:\n{user_prompt}"
            response = self.model.generate_content(final_prompt, generation_config=self.generation_config)
            return response.text
        return text
    
    def process_image(self, image_path: str, system_prompt: str = "") -> str:
        image = Image.open(image_path)
        user_prompt = "Extract all text, diagrams, charts, and educational content from this image. Provide a detailed description of everything visible that could be used for educational purposes."
        
        if system_prompt:
            final_prompt = f"{system_prompt}\n\nUSER REQUEST:\n{user_prompt}"
            response = self.model.generate_content(final_prompt, generation_config=self.generation_config)
        else:
            response = self.model.generate_content([user_prompt, image], generation_config=self.generation_config)
        return response.text
    
    def summarize_chapter(self, chapter_text: str, chapter_title: str = "", system_prompt: str = "") -> str:
        if chapter_text.strip():
            user_prompt = f"""Title: {chapter_title}
Content: {chapter_text}"""
        else:
            user_prompt = f"""Topic: {chapter_title}"""
        
        if system_prompt:
            final_prompt = f"{system_prompt}\n\nUSER REQUEST: {user_prompt}\n\nREMEMBER: If this is not study-related, reply exactly as instructed in the SYSTEM prompt above."
        else:
            final_prompt = user_prompt
        
        response = self.model.generate_content(final_prompt, generation_config=self.generation_config)
        return response.text
    
    def answer_question(self, question: str, system_prompt: str = "") -> str:
        user_prompt = f"""Question: {question}"""
        
        if system_prompt:
            final_prompt = f"{system_prompt}\n\nUSER REQUEST: {user_prompt}\n\nREMEMBER: If this is not study-related, reply exactly as instructed in the SYSTEM prompt above."
        else:
            final_prompt = user_prompt
        
        response = self.model.generate_content(final_prompt, generation_config=self.generation_config)
        return response.text
    
    def generate_test_questions(self, topic: str, question_count: int = 5, difficulty: str = "medium", system_prompt: str = "", question_type: str = "mcq") -> List[Dict]:
        if question_type.lower() == "mcq":
            user_prompt = f"""Generate exactly {question_count} {difficulty} difficulty multiple choice questions about: {topic}

Format EXACTLY as shown:

Question 1: [Question text here]
A) [Option A]
B) [Option B] 
C) [Option C]
D) [Option D]
Answer: [Correct letter]
Explanation: [Brief explanation]

Generate exactly {question_count} questions following this format."""
        else:
            user_prompt = f"""Generate exactly {question_count} {difficulty} difficulty subjective questions about: {topic}

Format EXACTLY as shown:

Question 1: [Question text here]
Answer: [Expected answer/key points]
Explanation: [Brief explanation]

Generate exactly {question_count} questions following this format."""
        
        if system_prompt:
            final_prompt = f"{system_prompt}\n\nUSER REQUEST:\n{user_prompt}"
        else:
            final_prompt = user_prompt
        
        if system_prompt:
            final_prompt = f"{system_prompt}\n\nUSER REQUEST: {user_prompt}\n\nREMEMBER: If this is not study-related, reply exactly as instructed in the SYSTEM prompt above."
        else:
            final_prompt = user_prompt
        
        try:
            response = self.model.generate_content(final_prompt, generation_config=self.generation_config)
            print(f"DEBUG - Raw response: {response.text}")  # Debug output
            
            # Check if AI refused to generate questions
            if "I can help with study-related questions" in response.text or "I cannot reply with that" in response.text:
                return [{'question': response.text, 'options': [], 'answer': '', 'explanation': ''}]
            
            if question_type.lower() == "mcq":
                parsed = self._parse_questions(response.text, question_count)
            else:
                parsed = self._parse_subjective_questions(response.text, question_count)
            
            print(f"DEBUG - Parsed questions count: {len(parsed)}")  # Debug output
            return parsed
        except Exception as e:
            print(f"DEBUG - Error in generate_test_questions: {str(e)}")
            raise RuntimeError(f"Error generating questions: {str(e)}")
    
    def _parse_questions(self, response_text: str, expected_count: int) -> List[Dict]:
        questions = []
        lines = response_text.split('\n')
        current_q = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('Question ') and ':' in line:
                if current_q and current_q.get('question'):
                    questions.append(current_q)
                question_text = line.split(':', 1)[1].strip()
                current_q = {'question': question_text, 'options': [], 'answer': '', 'explanation': ''}
                print(f"DEBUG - Found question: {question_text}")
            elif line.startswith(('A)', 'B)', 'C)', 'D)', 'E)')) and current_q:
                current_q['options'].append(line)
                print(f"DEBUG - Added option: {line}")
            elif line.startswith('Answer:') and current_q:
                current_q['answer'] = line[7:].strip()
                print(f"DEBUG - Found answer: {current_q['answer']}")
            elif line.startswith('Explanation:') and current_q:
                current_q['explanation'] = line[12:].strip()
                print(f"DEBUG - Found explanation: {current_q['explanation']}")
        
        # Add the last question if it exists
        if current_q and current_q.get('question'):
            # For MCQ, don't require exactly 4 options - accept any number
            questions.append(current_q)
        
        # Debug: Print parsing results
        print(f"DEBUG - MCQ Parser found {len(questions)} questions")
        if not questions:
            print(f"DEBUG - Parser failed. Raw response: {response_text}")
        
        return questions[:expected_count]
    
    def _parse_subjective_questions(self, response_text: str, expected_count: int) -> List[Dict]:
        questions = []
        lines = response_text.split('\n')
        current_q = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('Question ') and ':' in line:
                if current_q and current_q.get('question'):
                    questions.append(current_q)
                question_text = line.split(':', 1)[1].strip()
                current_q = {'question': question_text, 'answer': '', 'explanation': ''}
                print(f"DEBUG - Found subjective question: {question_text}")
            elif line.startswith('Answer:') and current_q:
                current_q['answer'] = line[7:].strip()
            elif line.startswith('Explanation:') and current_q:
                current_q['explanation'] = line[12:].strip()
        
        # Add the last question if it exists
        if current_q and current_q.get('question'):
            questions.append(current_q)
        
        # Debug: Print parsing results
        print(f"DEBUG - Subjective Parser found {len(questions)} questions")
        if not questions:
            print(f"DEBUG - Parser failed. Raw response: {response_text}")
        
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