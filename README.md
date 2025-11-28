# Teacher AI Assistant

A simple AI assistant for teachers to summarize book chapters and generate test questions.

## Features

- **Chapter Summarization**: Convert lengthy chapter content into concise, educational summaries
- **Test Question Generation**: Create multiple-choice questions with explanations for any topic

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Get a Gemini API key from https://makersuite.google.com/app/apikey

3. Replace `"your-gemini-api-key-here"` in the code with your actual API key

## Usage

```python
from teacher_ai import TeacherAssistant

# Initialize
assistant = TeacherAssistant("your-api-key")

# Summarize chapter
summary = assistant.summarize_chapter(chapter_text, "Chapter Title")

# Generate questions
questions = assistant.generate_test_questions("Topic Name", 5, "medium")
```

## Run Example

```bash
python example_usage.py
```
