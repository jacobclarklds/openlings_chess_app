'use client';

import { useState, useRef } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';

type Square = string;

interface Arrow {
  startSquare: Square;
  endSquare: Square;
  color: string;
}

interface Circle {
  square: Square;
  color: 'orange' | 'blue';
}

interface AnnotatedChessBoardProps {
  position?: string; // FEN string
  onPositionChange?: (fen: string) => void;
  allowMoves?: boolean;
}

interface DraggingPieceDataType {
  isSparePiece: boolean;
  position: string;
  pieceType: string;
}

interface PieceDataType {
  pieceType: string;
}

export default function AnnotatedChessBoard({
  position: initialPosition = 'start',
  onPositionChange,
  allowMoves = true,
}: AnnotatedChessBoardProps) {
  const [game] = useState(() => new Chess(initialPosition === 'start' ? undefined : initialPosition));
  const [position, setPosition] = useState(initialPosition);
  const [annotationMode, setAnnotationMode] = useState(false);
  const [selectedAnnotationType, setSelectedAnnotationType] = useState<'threat' | 'opportunity' | 'weak' | 'strong'>('threat');
  const [arrows, setArrows] = useState<Arrow[]>([]);
  const [circles, setCircles] = useState<Circle[]>([]);
  const [arrowStart, setArrowStart] = useState<Square | null>(null);

  const boardRef = useRef<HTMLDivElement>(null);

  // Handle piece moves (when not in annotation mode)
  function onDrop({ piece, sourceSquare, targetSquare }: { piece: DraggingPieceDataType; sourceSquare: Square; targetSquare: Square | null }) {
    if (annotationMode || !allowMoves || !targetSquare) return false;

    try {
      const move = game.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q', // Always promote to queen for simplicity
      });

      if (move === null) return false;

      const newPosition = game.fen();
      setPosition(newPosition);
      if (onPositionChange) {
        onPositionChange(newPosition);
      }
      return true;
    } catch (error) {
      return false;
    }
  }

  // Handle square clicks in annotation mode
  function handleSquareClick({ piece, square }: { piece: PieceDataType | null; square: Square }) {
    if (!annotationMode) return;

    // Handle arrow annotations
    if (selectedAnnotationType === 'threat' || selectedAnnotationType === 'opportunity') {
      if (!arrowStart) {
        // First click - start of arrow
        setArrowStart(square);
      } else {
        // Second click - end of arrow
        if (arrowStart !== square) {
          const color = selectedAnnotationType === 'threat' ? 'rgb(255, 0, 0)' : 'rgb(0, 255, 0)';
          const newArrow: Arrow = { startSquare: arrowStart, endSquare: square, color };

          // Check if this arrow already exists
          const existingIndex = arrows.findIndex(
            a => a.startSquare === newArrow.startSquare && a.endSquare === newArrow.endSquare
          );

          if (existingIndex >= 0) {
            // Remove existing arrow if it exists
            setArrows(arrows.filter((_, i) => i !== existingIndex));
          } else {
            // Add new arrow
            setArrows([...arrows, newArrow]);
          }
        }
        setArrowStart(null);
      }
    }

    // Handle circle annotations
    if (selectedAnnotationType === 'weak' || selectedAnnotationType === 'strong') {
      const color = selectedAnnotationType === 'weak' ? 'orange' : 'blue';
      const newCircle: Circle = { square, color };

      // Check if this square already has a circle
      const existingIndex = circles.findIndex(c => c.square === square);

      if (existingIndex >= 0) {
        // Remove existing circle if it's the same type, otherwise replace
        if (circles[existingIndex].color === color) {
          setCircles(circles.filter((_, i) => i !== existingIndex));
        } else {
          const updatedCircles = [...circles];
          updatedCircles[existingIndex] = newCircle;
          setCircles(updatedCircles);
        }
      } else {
        // Add new circle
        setCircles([...circles, newCircle]);
      }
    }
  }

  // Custom square styles for circles
  const customSquareStyles: Record<string, React.CSSProperties> = {};
  circles.forEach(circle => {
    customSquareStyles[circle.square] = {
      background: circle.color === 'orange'
        ? 'radial-gradient(circle, rgba(255, 165, 0, 0.5) 0%, rgba(255, 165, 0, 0.3) 50%, transparent 100%)'
        : 'radial-gradient(circle, rgba(30, 144, 255, 0.5) 0%, rgba(30, 144, 255, 0.3) 50%, transparent 100%)',
      borderRadius: '50%',
    };
  });

  // Clear all annotations
  const clearAnnotations = () => {
    setArrows([]);
    setCircles([]);
    setArrowStart(null);
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Control Panel */}
      <div className="bg-gray-100 p-4 rounded-lg shadow">
        <div className="flex flex-col gap-3">
          {/* Annotation Mode Toggle */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setAnnotationMode(!annotationMode);
                setArrowStart(null);
              }}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                annotationMode
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
              }`}
            >
              {annotationMode ? 'Annotation Mode: ON' : 'Annotation Mode: OFF'}
            </button>

            {annotationMode && (
              <button
                onClick={clearAnnotations}
                className="px-4 py-2 bg-red-500 text-white rounded font-medium hover:bg-red-600 transition-colors"
              >
                Clear Annotations
              </button>
            )}
          </div>

          {/* Annotation Type Selector */}
          {annotationMode && (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  setSelectedAnnotationType('threat');
                  setArrowStart(null);
                }}
                className={`px-4 py-2 rounded font-medium transition-colors ${
                  selectedAnnotationType === 'threat'
                    ? 'bg-red-600 text-white'
                    : 'bg-red-100 text-red-700 hover:bg-red-200'
                }`}
              >
                Red Arrow (Threat)
              </button>

              <button
                onClick={() => {
                  setSelectedAnnotationType('opportunity');
                  setArrowStart(null);
                }}
                className={`px-4 py-2 rounded font-medium transition-colors ${
                  selectedAnnotationType === 'opportunity'
                    ? 'bg-green-600 text-white'
                    : 'bg-green-100 text-green-700 hover:bg-green-200'
                }`}
              >
                Green Arrow (Opportunity)
              </button>

              <button
                onClick={() => {
                  setSelectedAnnotationType('weak');
                  setArrowStart(null);
                }}
                className={`px-4 py-2 rounded font-medium transition-colors ${
                  selectedAnnotationType === 'weak'
                    ? 'bg-orange-600 text-white'
                    : 'bg-orange-100 text-orange-700 hover:bg-orange-200'
                }`}
              >
                Orange Circle (Weak Piece)
              </button>

              <button
                onClick={() => {
                  setSelectedAnnotationType('strong');
                  setArrowStart(null);
                }}
                className={`px-4 py-2 rounded font-medium transition-colors ${
                  selectedAnnotationType === 'strong'
                    ? 'bg-blue-600 text-white'
                    : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }`}
              >
                Blue Circle (Strong Piece)
              </button>
            </div>
          )}

          {/* Instructions */}
          {annotationMode && (
            <div className="text-sm text-gray-600 bg-white p-3 rounded">
              <strong>Instructions:</strong>
              {(selectedAnnotationType === 'threat' || selectedAnnotationType === 'opportunity') && (
                <span> Click two squares to draw an arrow. Click the same arrow again to remove it.</span>
              )}
              {(selectedAnnotationType === 'weak' || selectedAnnotationType === 'strong') && (
                <span> Click a square to add/remove a circle. Click again to toggle or remove.</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Chessboard */}
      <div ref={boardRef} className="w-full max-w-2xl mx-auto">
        <Chessboard
          options={{
            position: position,
            onPieceDrop: onDrop,
            onSquareClick: handleSquareClick,
            arrows: arrows,
            squareStyles: customSquareStyles,
            allowDragging: !annotationMode && allowMoves,
          }}
        />
      </div>
    </div>
  );
}
