"""
Tests for chess board annotation generation.
Verifies that the OllamaChessCoachAgent correctly generates visual annotations.
"""

import pytest
import asyncio
from app.services.ollama_coach_agent import OllamaChessCoachAgent


class TestAnnotationGeneration:
    """Test that annotations are correctly generated for chess positions."""

    @pytest.fixture
    def sample_pgn(self):
        """Sample PGN for Scholar's Mate."""
        return """[Event "Casual Game"]
[Site "Online"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0"""

    @pytest.mark.asyncio
    async def test_annotation_structure(self):
        """Test that _create_default_annotations returns correct structure."""
        agent = OllamaChessCoachAgent()

        # Test opening position
        opening_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        annotations = agent._create_default_annotations(opening_fen, 0)

        # Verify we got annotations
        assert len(annotations) > 0, "Should generate annotations for opening position"

        # Check structure of each annotation
        for ann in annotations:
            assert 'id' in ann, "Annotation must have id"
            assert 'type' in ann, "Annotation must have type"
            assert 'color' in ann, "Annotation must have color"
            assert ann['type'] in ['arrow', 'circle', 'highlight'], f"Invalid type: {ann['type']}"

            # Verify required fields based on type
            if ann['type'] == 'arrow':
                assert 'from' in ann, "Arrow must have 'from' square"
                assert 'to' in ann, "Arrow must have 'to' square"
            elif ann['type'] in ['circle', 'highlight']:
                assert 'square' in ann, f"{ann['type']} must have 'square' field"

        print(f"\n✅ Opening position annotations: {len(annotations)} total")
        for ann in annotations:
            if ann['type'] == 'arrow':
                print(f"   → {ann['color']} arrow from {ann['from']} to {ann['to']}")
            else:
                print(f"   → {ann['color']} {ann['type']} on {ann['square']}")

    @pytest.mark.asyncio
    async def test_opening_position_annotations(self):
        """Test that opening position gets center highlights and development arrows."""
        agent = OllamaChessCoachAgent()
        opening_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        annotations = agent._create_default_annotations(opening_fen, 0)

        # Should have center square highlights
        center_squares = ['e4', 'd4', 'e5', 'd5']
        highlights = [a for a in annotations if a['type'] == 'highlight']
        highlight_squares = [a['square'] for a in highlights]

        for square in center_squares:
            assert square in highlight_squares, f"Should highlight center square {square}"

        # Should have development arrows
        arrows = [a for a in annotations if a['type'] == 'arrow']
        assert len(arrows) >= 2, "Should have at least 2 development arrows"

        print(f"\n✅ Found {len(highlights)} highlights on center squares")
        print(f"✅ Found {len(arrows)} development arrows")

    @pytest.mark.asyncio
    async def test_middlegame_position_annotations(self):
        """Test that non-opening positions get varied annotations."""
        agent = OllamaChessCoachAgent()

        # Position after 1.e4 e5 2.Bc4 Nc6
        middlegame_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3"

        annotations = agent._create_default_annotations(middlegame_fen, 1)

        assert len(annotations) > 0, "Should generate annotations for middlegame"

        # Should have a mix of annotation types
        types = set(a['type'] for a in annotations)
        print(f"\n✅ Middlegame annotation types: {types}")
        print(f"✅ Total annotations: {len(annotations)}")

        for ann in annotations:
            if ann['type'] == 'arrow':
                print(f"   → {ann['color']} arrow: {ann['from']}-{ann['to']}")
            else:
                print(f"   → {ann['color']} {ann['type']}: {ann['square']}")

    @pytest.mark.asyncio
    async def test_all_positions_get_annotations(self):
        """Test that ALL comment positions receive annotations."""
        agent = OllamaChessCoachAgent()

        # Test multiple positions
        test_positions = [
            ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 0),  # Opening
            ("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3", 1),  # After Bc4
            ("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", 2),  # After Qh5
        ]

        for fen, index in test_positions:
            annotations = agent._create_default_annotations(fen, index)
            assert len(annotations) > 0, f"Position {index} should have annotations"
            print(f"\n✅ Position {index}: {len(annotations)} annotations")

    @pytest.mark.asyncio
    async def test_lesson_generation_includes_annotations(self, sample_pgn):
        """Test that full lesson generation includes annotations in every comment."""
        agent = OllamaChessCoachAgent()

        try:
            # Generate a lesson
            result = await agent.generate_lesson(
                pgn=sample_pgn,
                user_elo=1200,
                focus_areas=['tactics', 'opening']
            )

            # Verify result structure
            assert 'comments' in result, "Result should have comments"
            assert 'total_steps' in result, "Result should have total_steps"

            comments = result['comments']
            assert len(comments) > 0, "Should generate at least one comment"

            print(f"\n✅ Generated {len(comments)} lesson comments")

            # Check EVERY comment has annotations
            for i, comment in enumerate(comments):
                assert 'annotations' in comment, f"Comment {i} missing annotations field"
                annotations = comment['annotations']

                print(f"\n📍 Comment {i+1}:")
                print(f"   Position: {comment.get('position_fen', 'N/A')[:50]}...")
                print(f"   Annotations: {len(annotations)}")

                # CRITICAL: Every comment should have annotations
                assert len(annotations) > 0, f"Comment {i} has NO annotations! This is a bug."

                # Print annotation details
                for ann in annotations:
                    if ann['type'] == 'arrow':
                        print(f"   → {ann['color']} arrow: {ann['from']} → {ann['to']}")
                    else:
                        print(f"   → {ann['color']} {ann['type']}: {ann['square']}")

            print(f"\n✅ ALL {len(comments)} comments have annotations!")

        finally:
            await agent.cleanup()

    @pytest.mark.asyncio
    async def test_annotation_colors_are_valid(self):
        """Test that all annotation colors are valid."""
        agent = OllamaChessCoachAgent()
        valid_colors = ['green', 'blue', 'red', 'yellow']

        test_fens = [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
        ]

        for i, fen in enumerate(test_fens):
            annotations = agent._create_default_annotations(fen, i)
            for ann in annotations:
                assert ann['color'] in valid_colors, f"Invalid color: {ann['color']}"

        print(f"\n✅ All annotation colors are valid")


if __name__ == "__main__":
    # Run tests directly
    print("🧪 Running annotation generation tests...\n")
    asyncio.run(pytest.main([__file__, "-v", "-s"]))
