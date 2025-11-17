'use client';

import { useState } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import AIThinkingIndicator from '@/components/chess/AIThinkingIndicator';
// import AnnotationToolbar, {
//   AnnotationTool,
//   AnnotationColor
// } from '@/components/chess/AnnotationToolbar';
import CoachCommentPanel from '@/components/chess/CoachCommentPanel';

type AnnotationTool = 'arrow' | 'circle' | 'highlight' | null;
type AnnotationColor = 'green' | 'blue' | 'red' | 'yellow';
import { BoardAnnotation, CoachComment } from '@/types/chess';
import { convertAnnotationsToArrows, getEnhancedSquareStyles } from '@/lib/chessUtils';

export default function DemoPage() {
  const [game] = useState(new Chess());
  const [position, setPosition] = useState(game.fen());
  const [annotations, setAnnotations] = useState<BoardAnnotation[]>([]);
  const [activeTool, setActiveTool] = useState<AnnotationTool>(null);
  const [activeColor, setActiveColor] = useState<AnnotationColor>('green');
  const [drawStart, setDrawStart] = useState<string | null>(null);
  const [showAIThinking, setShowAIThinking] = useState(false);

  // Sample coach comments for demo
  const demoComments: CoachComment[] = [
    {
      id: '1',
      text: '## Opening Principles\n\nWelcome to your personalized chess lesson! Let\'s start by looking at the initial position.\n\nThe key opening principles are:\n- **Control the center** with pawns and pieces\n- **Develop your pieces** quickly\n- **Castle early** to keep your king safe\n- **Connect your rooks**\n\nLet\'s see how these principles apply to your game!',
      position_fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
      annotations: [
        { id: '1', type: 'highlight', color: 'green', square: 'e4' },
        { id: '2', type: 'highlight', color: 'green', square: 'd4' },
        { id: '3', type: 'circle', color: 'blue', square: 'e2' },
        { id: '4', type: 'circle', color: 'blue', square: 'd2' }
      ],
      timestamp: Date.now()
    }
  ];

  const [currentCommentIndex, setCurrentCommentIndex] = useState(0);
  const currentComment = demoComments[currentCommentIndex];

  const handleSquareClick = (square: string) => {
    if (!activeTool) return;

    if (activeTool === 'arrow') {
      if (!drawStart) {
        setDrawStart(square);
      } else {
        if (square !== drawStart) {
          const newAnnotation: BoardAnnotation = {
            id: crypto.randomUUID(),
            type: 'arrow',
            color: activeColor,
            from: drawStart,
            to: square,
          };
          setAnnotations([...annotations, newAnnotation]);
        }
        setDrawStart(null);
      }
    } else if (activeTool === 'circle' || activeTool === 'highlight') {
      const newAnnotation: BoardAnnotation = {
        id: crypto.randomUUID(),
        type: activeTool,
        color: activeColor,
        square,
      };
      setAnnotations([...annotations, newAnnotation]);
    }
  };

  const handleToolChange = (tool: AnnotationTool, color: AnnotationColor) => {
    setActiveTool(tool);
    setActiveColor(color);
    setDrawStart(null);
  };

  const handleClearAnnotations = () => {
    setAnnotations([]);
    setDrawStart(null);
  };

  const allAnnotations = [...(currentComment.annotations || []), ...annotations];
  const squareStyles = getEnhancedSquareStyles(allAnnotations, {});
  const arrows = convertAnnotationsToArrows(allAnnotations);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-4xl font-bold text-white mb-2">Enhanced Chess UI Demo</h1>
          <p className="text-lg text-gray-300">
            Try the annotation tools below! Click the arrow, circle, or highlight buttons, then click on the board.
          </p>
        </div>

        {/* AI Thinking Demo Toggle */}
        <div className="mb-4">
          <button
            onClick={() => setShowAIThinking(!showAIThinking)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
          >
            {showAIThinking ? 'Hide' : 'Show'} AI Thinking Indicator
          </button>
        </div>

        {/* AI Thinking Indicator */}
        <div className="mb-4">
          <AIThinkingIndicator
            visible={showAIThinking}
            message="Analyzing your position"
            variant="analyzing"
          />
        </div>

        {/* Annotation Toolbar */}
        {/* <div className="mb-4">
          <AnnotationToolbar
            onToolChange={handleToolChange}
            onClear={handleClearAnnotations}
            annotationCount={annotations.length}
            activeTool={activeTool}
            activeColor={activeColor}
          />
        </div> */}

        {/* Main Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Chess Board */}
          <div className="flex justify-center items-start">
            <div className="w-full max-w-[600px]">
              <div className="bg-white p-4 rounded-lg shadow-board border-2 border-gray-200">
                <Chessboard
                  id="demo-board"
                  position={position}
                  onSquareClick={handleSquareClick}
                  customArrows={arrows}
                  customSquareStyles={squareStyles}
                  boardWidth={560}
                  arePiecesDraggable={false}
                  customBoardStyle={{
                    borderRadius: '4px',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                  }}
                  customDarkSquareStyle={{ backgroundColor: '#b58863' }}
                  customLightSquareStyle={{ backgroundColor: '#f0d9b5' }}
                />
              </div>

              {/* Instructions */}
              <div className="mt-4 p-4 bg-white/10 backdrop-blur border border-white/20 rounded-lg">
                <h3 className="text-lg font-semibold text-white mb-2">How to use:</h3>
                <ul className="text-gray-300 space-y-1 text-sm">
                  <li>• Click <strong className="text-white">Arrow (→)</strong> then click two squares to draw an arrow</li>
                  <li>• Click <strong className="text-white">Circle (○)</strong> then click squares to add circles</li>
                  <li>• Click <strong className="text-white">Highlight (■)</strong> to highlight squares</li>
                  <li>• Use the color picker to change annotation colors</li>
                  <li>• Click <strong className="text-white">Clear All</strong> to remove your annotations</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Right: Coach Comments Panel */}
          <div className="space-y-4">
            <CoachCommentPanel
              comment={currentComment}
              currentIndex={currentCommentIndex}
              totalComments={demoComments.length}
              onNext={() => setCurrentCommentIndex(Math.min(currentCommentIndex + 1, demoComments.length - 1))}
              onPrevious={() => setCurrentCommentIndex(Math.max(currentCommentIndex - 1, 0))}
            />

            {/* Feature showcase */}
            <div className="bg-white/10 backdrop-blur border border-white/20 p-6 rounded-lg shadow-2xl">
              <h3 className="text-xl font-semibold text-white mb-4">✨ New Features</h3>
              <div className="space-y-3 text-gray-300">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">🎨</span>
                  <div>
                    <strong className="text-white">Professional Design System</strong>
                    <p className="text-gray-400">Cool colors, clean typography, smooth animations</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-2xl">✏️</span>
                  <div>
                    <strong className="text-white">Drawing Tools</strong>
                    <p className="text-gray-400">Intuitive annotation toolbar with arrows, circles, and highlights</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-2xl">🤖</span>
                  <div>
                    <strong className="text-white">AI Thinking Indicators</strong>
                    <p className="text-gray-400">Beautiful loading states and progress feedback</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-2xl">♟️</span>
                  <div>
                    <strong className="text-white">Chess.com/Lichess Style</strong>
                    <p className="text-gray-400">Familiar UX patterns from popular chess platforms</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
