'use client';

import { useState, useEffect } from 'react';
import CMChessboard from '@/components/chess/CMChessboard';
import CoachCommentPanel from '@/components/chess/CoachCommentPanel';
import { CoachComment } from '@/types/chess';

export default function ChessDemoPage() {
  const [loading, setLoading] = useState(false);
  const [lesson, setLesson] = useState<any>(null);
  const [currentCommentIndex, setCurrentCommentIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const samplePGN = `[Event "Casual Game"]
[Site "Online"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0`;

  const generateLesson = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/demo/generate-lesson', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pgn: samplePGN,
          user_elo: 1200,
          focus_areas: ['tactics', 'opening']
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate lesson');
      }

      const data = await response.json();
      console.log('Lesson data received:', data);
      console.log('First comment:', data.comments?.[0]);
      setLesson(data);
      setCurrentCommentIndex(0);
    } catch (err: any) {
      setError(err.message || 'Failed to generate lesson');
    } finally {
      setLoading(false);
    }
  };

  const currentComment = lesson?.comments?.[currentCommentIndex];
  const position = currentComment?.position_fen || 'start';
  const annotations = currentComment?.annotations || [];

  // Debug logging whenever index changes
  useEffect(() => {
    if (lesson) {
      console.log('=== Chess Demo Debug ===');
      console.log('Current comment index:', currentCommentIndex);
      console.log('Current comment:', currentComment);
      console.log('Position FEN:', position);
      console.log('Annotations:', annotations);
      console.log('Total comments:', lesson?.comments?.length);
      console.log('=======================');
    }
  }, [currentCommentIndex, lesson, currentComment, position, annotations]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-3 tracking-tight">
            ♟️ Chess Training Demo
          </h1>
          <p className="text-blue-200 text-lg">
            AI-Powered Chess Lessons • No Login Required
          </p>
        </div>

        {/* Generate Lesson Button */}
        {!lesson && (
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl shadow-2xl p-8 text-center max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold mb-4 text-white">
              Ready to Learn Chess?
            </h2>
            <p className="text-blue-100 mb-8 text-lg leading-relaxed">
              Generate an AI-powered lesson analyzing Scholar's Mate.
              You'll get 5 educational steps with visual annotations and interactive questions.
            </p>

            <button
              onClick={generateLesson}
              disabled={loading}
              className="px-10 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl font-bold text-lg
                       hover:from-blue-600 hover:to-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all transform hover:scale-105 shadow-lg hover:shadow-xl"
            >
              {loading ? (
                <span className="flex items-center gap-3 justify-center">
                  <svg className="animate-spin h-6 w-6" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  AI is thinking... (30-60s)
                </span>
              ) : (
                <span className="flex items-center gap-2 justify-center">
                  <span>✨</span> Generate Chess Lesson
                </span>
              )}
            </button>

            {error && (
              <div className="mt-6 p-4 bg-red-500/20 border border-red-400/50 rounded-xl backdrop-blur">
                <p className="text-red-100 font-semibold">
                  ⚠️ {error}
                </p>
                <p className="text-sm text-red-200 mt-2">
                  Make sure the backend is running at http://localhost:8000
                </p>
              </div>
            )}

            {/* Sample PGN Display */}
            <div className="mt-8 text-left">
              <h3 className="font-semibold text-white mb-3 text-lg">📋 Sample Game:</h3>
              <pre className="bg-black/30 border border-white/10 p-4 rounded-xl text-sm overflow-x-auto text-blue-100 font-mono">
                {samplePGN}
              </pre>
            </div>
          </div>
        )}

        {/* Lesson Display */}
        {lesson && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chess Board */}
            <div className="flex justify-center items-start">
              <div className="w-full max-w-[600px]">
                <div className="bg-gradient-to-br from-amber-100 to-amber-50 p-6 rounded-2xl shadow-2xl border-4 border-amber-900/20">
                  <CMChessboard
                    position={position}
                    annotations={annotations}
                    width={560}
                  />
                </div>

                {/* Reset Button */}
                <button
                  onClick={() => setLesson(null)}
                  className="mt-4 w-full px-6 py-3 bg-white/10 backdrop-blur border border-white/20 text-white rounded-xl font-semibold
                           hover:bg-white/20 transition-all shadow-lg"
                >
                  ← Generate New Lesson
                </button>
              </div>
            </div>

            {/* Coach Comments */}
            <div>
              {currentComment && (
                <CoachCommentPanel
                  comment={currentComment}
                  currentIndex={currentCommentIndex}
                  totalComments={lesson.comments.length}
                  onNext={() => setCurrentCommentIndex(Math.min(currentCommentIndex + 1, lesson.comments.length - 1))}
                  onPrevious={() => setCurrentCommentIndex(Math.max(currentCommentIndex - 1, 0))}
                />
              )}

              {/* Lesson Info */}
              <div className="mt-4 bg-white/10 backdrop-blur border border-white/20 rounded-xl shadow-xl p-5">
                <h3 className="font-bold text-white mb-3 text-lg">📊 Lesson Info</h3>
                <ul className="text-sm text-blue-100 space-y-2">
                  <li className="flex items-center gap-2">
                    <span className="text-lg">📝</span> Total Steps: <span className="font-semibold text-white">{lesson.total_steps}</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-lg">🎯</span> Focus: <span className="font-semibold text-white">{lesson.focus_areas.join(', ') || 'General'}</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-lg">🤖</span> AI Model: <span className="font-semibold text-white">GPT-OSS:20B (Ollama)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-lg">💰</span> Cost: <span className="font-semibold text-green-300">$0.00 (Local AI)</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
