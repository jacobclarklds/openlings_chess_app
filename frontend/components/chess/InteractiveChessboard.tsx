'use client';

import { useState, useEffect } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { BoardAnnotation } from '@/types/chess';

interface InteractiveChessboardProps {
  position: string;
  annotations?: BoardAnnotation[];
  width?: number;
  interactive?: boolean;
  onMove?: (from: string, to: string) => void;
  expectedMove?: { from: string; to: string } | null;
}

export default function InteractiveChessboard({
  position,
  annotations = [],
  width = 560,
  interactive = false,
  onMove,
  expectedMove
}: InteractiveChessboardProps) {
  const [game, setGame] = useState<Chess | null>(null);
  const [selectedSquare, setSelectedSquare] = useState<string | null>(null);
  const [customSquareStyles, setCustomSquareStyles] = useState({});
  const [customArrows, setCustomArrows] = useState<[string, string, string][]>([]);

  // Initialize game when position changes
  useEffect(() => {
    try {
      const newGame = new Chess(position);
      setGame(newGame);
      setSelectedSquare(null);
    } catch (error) {
      console.error('Invalid FEN position:', error);
    }
  }, [position]);

  // Convert annotations to react-chessboard format
  useEffect(() => {
    const arrows: [string, string, string][] = [];
    const squareStyles: Record<string, React.CSSProperties> = {};

    annotations.forEach((annotation) => {
      const colorMap: Record<string, string> = {
        red: 'rgba(220, 38, 38, 0.8)',
        green: 'rgba(34, 197, 94, 0.8)',
        blue: 'rgba(59, 130, 246, 0.8)',
        yellow: 'rgba(234, 179, 8, 0.8)',
        orange: 'rgba(249, 115, 22, 0.8)',
        purple: 'rgba(168, 85, 247, 0.8)',
        cyan: 'rgba(6, 182, 212, 0.8)'
      };

      const color = colorMap[annotation.color] || annotation.color;

      // Convert arrows
      if (annotation.type === 'arrow' && annotation.from && annotation.to) {
        arrows.push([annotation.from, annotation.to, color]);
      }

      // Convert highlights and circles to square styles
      if (annotation.type === 'highlight' && annotation.square) {
        squareStyles[annotation.square] = {
          backgroundColor: color.replace('0.8', '0.4')
        };
      }

      if (annotation.type === 'circle' && annotation.square) {
        squareStyles[annotation.square] = {
          boxShadow: `inset 0 0 0 4px ${color}`
        };
      }

      if (annotation.type === 'dot' && annotation.square) {
        squareStyles[annotation.square] = {
          background: `radial-gradient(circle, ${color} 25%, transparent 25%)`
        };
      }
    });

    // Add selected square highlight
    if (selectedSquare && interactive) {
      squareStyles[selectedSquare] = {
        backgroundColor: 'rgba(255, 255, 0, 0.4)'
      };
    }

    setCustomArrows(arrows);
    setCustomSquareStyles(squareStyles);
  }, [annotations, selectedSquare, interactive]);

  const handleSquareClick = (square: string) => {
    if (!interactive || !game) return;

    // If a square is already selected, try to move
    if (selectedSquare) {
      const move = game.move({
        from: selectedSquare,
        to: square,
        promotion: 'q' // Always promote to queen
      });

      if (move) {
        // Valid move made
        setSelectedSquare(null);
        if (onMove) {
          onMove(selectedSquare, square);
        }
      } else {
        // Invalid move, try selecting this square instead
        const piece = game.get(square);
        if (piece && piece.color === game.turn()) {
          setSelectedSquare(square);
        } else {
          setSelectedSquare(null);
        }
      }
    } else {
      // No square selected, try to select this one
      const piece = game.get(square);
      if (piece && piece.color === game.turn()) {
        setSelectedSquare(square);
      }
    }
  };

  const onPieceDrop = (sourceSquare: string, targetSquare: string) => {
    if (!interactive || !game) return false;

    const move = game.move({
      from: sourceSquare,
      to: targetSquare,
      promotion: 'q'
    });

    if (move) {
      setSelectedSquare(null);
      if (onMove) {
        onMove(sourceSquare, targetSquare);
      }
      return true;
    }

    return false;
  };

  // Get legal moves for selected piece to show as hints
  const getLegalMoveSquares = () => {
    if (!selectedSquare || !game) return [];
    const moves = game.moves({ square: selectedSquare as any, verbose: true });
    return moves.map((move: any) => move.to);
  };

  // Add legal move indicators to square styles
  const getFinalSquareStyles = () => {
    if (!interactive || !selectedSquare) return customSquareStyles;

    const legalMoves = getLegalMoveSquares();
    const styles = { ...customSquareStyles };

    legalMoves.forEach((square) => {
      const piece = game?.get(square);
      if (piece) {
        // Capture move - show bevel/ring
        styles[square] = {
          ...styles[square],
          boxShadow: 'inset 0 0 0 4px rgba(34, 197, 94, 0.6)'
        };
      } else {
        // Normal move - show dot
        styles[square] = {
          ...styles[square],
          background: 'radial-gradient(circle, rgba(0, 0, 0, 0.2) 20%, transparent 20%)'
        };
      }
    });

    return styles;
  };

  if (!game) {
    return <div style={{ width, height: width }}>Loading...</div>;
  }

  return (
    <div style={{ width: '100%', maxWidth: `${width}px` }}>
      <Chessboard
        position={game.fen()}
        onSquareClick={handleSquareClick}
        onPieceDrop={onPieceDrop}
        boardWidth={width}
        customArrows={customArrows}
        customSquareStyles={getFinalSquareStyles()}
        arePiecesDraggable={interactive}
        customBoardStyle={{
          borderRadius: '4px',
          boxShadow: '0 5px 15px rgba(0, 0, 0, 0.5)'
        }}
      />
    </div>
  );
}
