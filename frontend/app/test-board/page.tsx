'use client';

import { useState, useEffect } from 'react';
import CMChessboard from '@/components/chess/CMChessboard';

export default function TestBoardPage() {
  const [step, setStep] = useState(0);

  // Hardcoded positions for Scholar's Mate
  const positions = [
    {
      fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
      description: 'Starting position',
      annotations: [
        { id: 'ann1', type: 'highlight', color: 'green', square: 'e4' },
        { id: 'ann2', type: 'highlight', color: 'green', square: 'd4' },
        { id: 'ann3', type: 'arrow', color: 'blue', from: 'e2', to: 'e4' }
      ]
    },
    {
      fen: 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1',
      description: 'After 1.e4',
      annotations: [
        { id: 'ann4', type: 'circle', color: 'yellow', square: 'e4' },
        { id: 'ann5', type: 'arrow', color: 'green', from: 'e7', to: 'e5' }
      ]
    },
    {
      fen: 'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2',
      description: 'After 1...e5'
    },
    {
      fen: 'rnbqkbnr/pppp1ppp/8/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR b KQkq - 1 2',
      description: 'After 2.Bc4'
    },
    {
      fen: 'r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3',
      description: 'After 2...Nc6'
    },
    {
      fen: 'r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 3 3',
      description: 'After 3.Qh5'
    },
    {
      fen: 'r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4',
      description: 'After 3...Nf6'
    },
    {
      fen: 'r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4',
      description: 'After 4.Qxf7# - Checkmate!'
    }
  ];

  const currentPosition = positions[step];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8 text-center">
          Chess Board Update Test
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Chess Board */}
          <div>
            <div className="bg-gradient-to-br from-amber-100 to-amber-50 p-6 rounded-2xl shadow-2xl">
              <CMChessboard
                position={currentPosition.fen}
                annotations={currentPosition.annotations || []}
                width={500}
              />
            </div>
          </div>

          {/* Controls */}
          <div className="bg-white/10 backdrop-blur border border-white/20 rounded-2xl p-6">
            <h2 className="text-2xl font-bold text-white mb-4">
              Step {step + 1} of {positions.length}
            </h2>

            <p className="text-lg text-blue-100 mb-6">
              {currentPosition.description}
            </p>

            <div className="mb-6">
              <div className="w-full bg-white/20 rounded-full h-2 mb-2">
                <div
                  className="bg-cyan-400 h-2 rounded-full transition-all"
                  style={{ width: `${((step + 1) / positions.length) * 100}%` }}
                />
              </div>
            </div>

            <div className="flex gap-3 mb-6">
              <button
                onClick={() => setStep(Math.max(0, step - 1))}
                disabled={step === 0}
                className="flex-1 px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl font-semibold disabled:opacity-30 disabled:cursor-not-allowed transition-all border border-white/20"
              >
                ← Previous
              </button>
              <button
                onClick={() => setStep(Math.min(positions.length - 1, step + 1))}
                disabled={step === positions.length - 1}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-xl font-semibold disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                Next →
              </button>
            </div>

            <div className="bg-black/20 rounded-xl p-4">
              <h3 className="text-sm font-bold text-white mb-2">Debug Info:</h3>
              <div className="text-xs text-blue-200 font-mono space-y-1">
                <div>Current Step: {step}</div>
                <div>FEN: {currentPosition.fen.substring(0, 30)}...</div>
                <div>Key: test-board-{step}</div>
              </div>
            </div>

            <button
              onClick={() => setStep(0)}
              className="w-full mt-4 px-6 py-3 bg-red-500/20 hover:bg-red-500/30 text-white rounded-xl font-semibold transition-all border border-red-500/50"
            >
              Reset to Start
            </button>
          </div>
        </div>

        <div className="mt-8 bg-yellow-500/10 border border-yellow-500/50 rounded-xl p-6">
          <h3 className="text-yellow-300 font-bold mb-2">Test Instructions:</h3>
          <ol className="text-yellow-100 space-y-2 list-decimal list-inside">
            <li>Click "Next" to advance through the moves</li>
            <li>Watch if the chess pieces move on the board</li>
            <li>Click "Previous" to go back</li>
            <li>If pieces move correctly, the test PASSES ✅</li>
            <li>If pieces don't move, the test FAILS ❌</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
