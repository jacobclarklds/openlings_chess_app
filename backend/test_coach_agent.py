"""
Test the Chess Coach Agent with a sample game.
This is a standalone test that doesn't require database.
"""

import asyncio
import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.coach_agent import ChessCoachAgent


async def test_agent():
    """Test the agent with a simple Scholar's Mate game."""
    
    print("🧪 Testing Chess Coach Agent...\n")
    
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
    print("=" * 60)
    
    try:
        # Initialize agent
        print("\n🤖 Initializing Chess Coach Agent...")
        agent = ChessCoachAgent()
        
        # Generate lesson
        print("📚 Generating lesson (this may take 30-60 seconds)...\n")
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
                        print(f"  - {ann['color'].upper()} arrow: {ann['from']} → {ann['to']}")
                    else:
                        print(f"  - {ann['color'].upper()} {ann['type']}: {ann['square']}")
            
            if comment['question']:
                print(f"\n❓ Question:")
                print(f"  Type: {comment['question']['type']}")
                print(f"  Q: {comment['question']['question']}")
                if 'options' in comment['question']:
                    print(f"  Options: {comment['question']['options']}")
                print(f"  Answer: {comment['question']['correct_answer']}")
            
            print("-" * 60)
        
        print("\n✅ Agent test completed successfully!\n")
        
        # Cleanup
        await agent.cleanup()
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_agent())
