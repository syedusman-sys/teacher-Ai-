from teacher_ai import TeacherAssistant

def test_assistant():
    # Replace with your actual Gemini API key
    api_key = input("Enter your Gemini API key: ")
    
    assistant = TeacherAssistant(api_key)
    
    # Test chapter summarization
    print("Testing Chapter Summarization...")
    chapter_text = """
    Photosynthesis is the biological process by which plants, algae, and certain bacteria convert light energy, 
    usually from the sun, into chemical energy stored in glucose. This process occurs primarily in the leaves 
    of plants, specifically in organelles called chloroplasts. The process can be divided into two main stages: 
    the light-dependent reactions (photo reactions) and the light-independent reactions (Calvin cycle). 
    During the light reactions, chlorophyll absorbs light energy and converts it to chemical energy in the 
    form of ATP and NADPH. The Calvin cycle uses this energy to convert carbon dioxide from the atmosphere 
    into glucose through a series of chemical reactions.
    """
    
    try:
        summary = assistant.summarize_chapter(chapter_text, "Chapter 5: Photosynthesis")
        print("\n--- CHAPTER SUMMARY ---")
        print(summary)
        print("\n" + "="*60 + "\n")
    except Exception as e:
        print(f"Error in summarization: {e}")
        return
    
    # Test question generation
    print("Testing Question Generation...")
    try:
        questions = assistant.generate_test_questions("Photosynthesis", 2, "medium")
        print("--- GENERATED QUESTIONS ---")
        for i, q in enumerate(questions, 1):
            print(f"Question {i}: {q.get('question', 'N/A')}")
            for option in q.get('options', []):
                print(f"  {option}")
            print(f"Answer: {q.get('answer', 'N/A')}")
            print(f"Explanation: {q.get('explanation', 'N/A')}")
            print()
    except Exception as e:
        print(f"Error in question generation: {e}")

if __name__ == "__main__":
    test_assistant()