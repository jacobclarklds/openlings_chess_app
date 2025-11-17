#!/usr/bin/env python3
"""
End-to-end test script to verify the demo API returns annotations.
This script calls the actual API endpoint and verifies the response.
"""

import requests
import json
import sys


def test_demo_api():
    """Test the demo API endpoint and verify annotations are present."""

    print("🧪 Testing Demo API Annotation Generation\n")
    print("=" * 60)

    # Sample PGN
    sample_pgn = """[Event "Casual Game"]
[Site "Online"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0"""

    url = "http://localhost:8000/api/demo/generate-lesson"

    payload = {
        "pgn": sample_pgn,
        "user_elo": 1200,
        "focus_areas": ["tactics", "opening"]
    }

    print(f"📡 Calling API: {url}")
    print(f"📝 Request payload:")
    print(f"   - PGN length: {len(sample_pgn)} characters")
    print(f"   - User ELO: 1200")
    print(f"   - Focus areas: tactics, opening\n")

    try:
        print("⏳ Generating lesson (this takes 30-60 seconds)...")
        response = requests.post(url, json=payload, timeout=120)

        if response.status_code != 200:
            print(f"❌ API returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        data = response.json()

        print(f"\n✅ API Response received!")
        print(f"=" * 60)

        # Verify response structure
        if 'comments' not in data:
            print("❌ Response missing 'comments' field")
            return False

        comments = data['comments']
        total_steps = data.get('total_steps', 0)

        print(f"\n📊 Lesson Summary:")
        print(f"   - Total steps: {total_steps}")
        print(f"   - Total comments: {len(comments)}")
        print(f"   - Focus areas: {data.get('focus_areas', [])}")

        # Check each comment for annotations
        print(f"\n📍 Checking annotations for each comment:")
        print("=" * 60)

        all_have_annotations = True
        total_annotations = 0

        for i, comment in enumerate(comments):
            print(f"\n📌 Comment {i + 1}/{len(comments)}:")

            # Check required fields
            if 'position_fen' not in comment:
                print(f"   ❌ Missing 'position_fen' field")
                all_have_annotations = False
                continue

            if 'annotations' not in comment:
                print(f"   ❌ Missing 'annotations' field")
                all_have_annotations = False
                continue

            annotations = comment['annotations']
            position_fen = comment['position_fen']
            text = comment.get('text', '')

            print(f"   Position: {position_fen[:50]}...")
            print(f"   Text length: {len(text)} characters")
            print(f"   Annotations: {len(annotations)}")

            if len(annotations) == 0:
                print(f"   ❌ NO ANNOTATIONS! This is a bug!")
                all_have_annotations = False
            else:
                print(f"   ✅ Has annotations:")
                total_annotations += len(annotations)

                # Print each annotation
                for ann in annotations:
                    ann_type = ann.get('type', 'unknown')
                    color = ann.get('color', 'unknown')

                    if ann_type == 'arrow':
                        from_sq = ann.get('from', '?')
                        to_sq = ann.get('to', '?')
                        print(f"      → {color} arrow: {from_sq} → {to_sq}")
                    elif ann_type in ['circle', 'highlight']:
                        square = ann.get('square', '?')
                        print(f"      → {color} {ann_type}: {square}")
                    else:
                        print(f"      → {color} {ann_type}")

        print(f"\n" + "=" * 60)
        print(f"📊 Final Results:")
        print(f"   - Comments with annotations: {sum(1 for c in comments if len(c.get('annotations', [])) > 0)}/{len(comments)}")
        print(f"   - Total annotations: {total_annotations}")
        print(f"   - Average per comment: {total_annotations / len(comments):.1f}")

        if all_have_annotations:
            print(f"\n✅ SUCCESS! All comments have annotations!")
            print(f"\n🎉 The API is correctly generating visual annotations for the chess board!")
            return True
        else:
            print(f"\n❌ FAILURE! Some comments are missing annotations!")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ Request timeout (>120s)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error - is the backend running?")
        print(f"   Make sure the server is running at http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_demo_api()
    sys.exit(0 if success else 1)
