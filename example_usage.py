from teacher_ai import TeacherAssistant

def main():
    # API key will be loaded from .env file
    assistant = TeacherAssistant()
    
    # Example 1: Summarize a chapter
    chapter_text = """
    The water cycle is a continuous process that describes the movement of water on, above, and below Earth's surface.
    Water evaporates from oceans, lakes, and rivers, rises into the atmosphere as water vapor, condenses into clouds,
    and falls back to Earth as precipitation. This cycle is driven by solar energy and gravity.
    """
    
    summary = assistant.summarize_chapter(chapter_text, "Chapter 3: The Water Cycle")
    print("Chapter Summary:")
    print(summary)
    print("\n" + "="*50 + "\n")
    
    # Example 2: Generate test questions
    questions = assistant.generate_test_questions("Water Cycle", 3, "easy")
    print("Generated Test Questions:")
    for i, q in enumerate(questions, 1):
        print(f"Question {i}: {q.get('question', 'N/A')}")
        for option in q.get('options', []):
            print(f"  {option}")
        print(f"Answer: {q.get('answer', 'N/A')}")
        print(f"Explanation: {q.get('explanation', 'N/A')}")
        print()

if __name__ == "__main__":
    main()