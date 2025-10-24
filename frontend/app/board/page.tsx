'use client';

import dynamic from 'next/dynamic';

const AnnotatedChessBoard = dynamic(() => import('@/components/AnnotatedChessBoard'), {
  ssr: false,
  loading: () => <div className="text-center py-8">Loading chessboard...</div>,
});

export default function BoardPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Annotated Chess Board
        </h1>
        <p className="text-gray-600 mb-8">
          Analyze chess positions with visual annotations
        </p>

        <AnnotatedChessBoard />

        {/* Usage Instructions */}
        <div className="mt-8 bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">How to Use</h2>
          <div className="space-y-3 text-gray-700">
            <div>
              <strong className="text-blue-600">Normal Mode:</strong>
              <p>Click and drag pieces to make moves on the board.</p>
            </div>
            <div>
              <strong className="text-blue-600">Annotation Mode:</strong>
              <p>Click "Annotation Mode: OFF" to enable annotations.</p>
            </div>
            <div className="ml-4 space-y-2">
              <div>
                <strong className="text-red-600">Red Arrows (Threats):</strong>
                <p>Click two squares to draw an arrow showing a threat.</p>
              </div>
              <div>
                <strong className="text-green-600">Green Arrows (Opportunities):</strong>
                <p>Click two squares to draw an arrow showing your plan.</p>
              </div>
              <div>
                <strong className="text-orange-600">Orange Circles (Weak Pieces):</strong>
                <p>Click a square to highlight a vulnerable piece.</p>
              </div>
              <div>
                <strong className="text-blue-600">Blue Circles (Strong Pieces):</strong>
                <p>Click a square to highlight a well-positioned piece.</p>
              </div>
            </div>
            <div className="pt-2">
              <strong>Tip:</strong> Click an existing annotation to remove it.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
