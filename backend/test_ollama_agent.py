"""
Test the Ollama Chess Coach Agent with a sample game.
"""

import asyncio
import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ollama_coach_agent import OllamaChessCoachAgent


async def test_agent():
    """Test the Ollama agent with a simple game."""
    
    print("🧪 Testing Ollama Chess Coach Agent...\n")
    
    # Sample PGN - Scholar's Mate (common beginner trap)
    sample_pgn = """[Event "Test Game"]
[Site "Online"]
[Date "2024.01.15"]
[White "Beginner1"]
[Black "Beginner2"]
[Result "1-0"]

1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0"""

    user_elo = 1200  # Beginner player
    
    print(f"📊 Game PGN:\n{sample_pgn}\n")
    print(f"👤 User ELO: {user_elo}\n")
    print(f"🤖 Using Model: gpt-oss:20b via Ollama")
    print("=" * 60)
    
    try:
        # Initialize agent
        print("\n🤖 Initializing Ollama Chess Coach Agent...")
        agent = OllamaChessCoachAgent()
        
        # Generate lesson
        print("📚 Generating lesson (this may take 30-90 seconds)...\n")
        lesson = await agent.generate_lesson(
            pgn=sample_pgn,
            user_elo=user_elo,
            focus_areas=["tactics", "opening principles"]
        )
        
        print("=" * 60)
        print(f"\n✅ Lesson Generated Successfully!")
        print(f"📝 Total Comments: {lesson['total_steps']}")
        print(f"🎯 Focus Areas: {', '.join(lesson['focus_areas'])}")
        print("\n" + "=" * 60)
        
        # Display each comment
        for idx, comment in enumerate(lesson['comments'], 1):
            print(f"\n📍 STEP {idx}/{lesson['total_steps']}")
            print("-" * 60)
            print(f"Position FEN: {comment['position_fen']}")
            print(f"\n{comment['text']}\n")
            
            if comment['annotations']:
                print(f"🎨 Annotations ({len(comment['annotations'])}):")
                for ann in comment['annotations']:
                    if ann['type'] == 'arrow':
                        print(f"  - {ann['color'].upper()} arrow: {ann.get('from', 'N/A')} → {ann.get('to', 'N/A')}")
                    else:
                        print(f"  - {ann['color'].upper()} {ann['type']}: {ann.get('square', 'N/A')}")
            
            if comment.get('question'):
                print(f"\n❓ Question:")
                print(f"  Type: {comment['question']['type']}")
                print(f"  Q: {comment['question']['question']}")
                if 'options' in comment['question']:
                    print(f"  Options: {comment['question']['options']}")
                print(f"  Answer: {comment['question']['correct_answer']}")
            
            print("-" * 60)
        
        print("\n✅ Ollama agent test completed successfully!\n")
        
        # Cleanup
        await agent.cleanup()
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n🔍 Checking Ollama connection...")
    import ollama
    try:
        # Test Ollama connection
        models = ollama.list()
        print(f"✅ Connected to Ollama. Available models: {len(models.get('models', []))}")
        
        # Check if gpt-oss:20b is available
        has_model = any('gpt-oss:20b' in str(m.get('name', '')) for m in models.get('models', []))
        if not has_model:
            print("⚠️  Warning: gpt-oss:20b not found. Run: ollama pull gpt-oss:20b")
        else:
            print("✅ gpt-oss:20b model is available")
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("Make sure Ollama is running: brew services start ollama")
        sys.exit(1)
    
    print("\n" + "=" * 60 + "\n")
    asyncio.run(test_agent())
