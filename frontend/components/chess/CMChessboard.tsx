'use client';

import { useEffect, useRef, useState } from 'react';
import { Chessboard } from 'cm-chessboard';
import 'cm-chessboard/assets/chessboard.css';
import { BoardAnnotation } from '@/types/chess';
import ChessAnnotations from './ChessAnnotations';

interface CMChessboardProps {
  position: string;
  annotations?: BoardAnnotation[];
  width?: number;
}

export default function CMChessboard({ position, annotations = [], width = 560 }: CMChessboardProps) {
  const boardRef = useRef<HTMLDivElement>(null);
  const chessboardRef = useRef<Chessboard | null>(null);
  const [squareSize, setSquareSize] = useState(70);

  useEffect(() => {
    if (!boardRef.current) return;

    // Initialize the chessboard
    if (!chessboardRef.current) {
      chessboardRef.current = new Chessboard(boardRef.current, {
        position: position,
        sprite: {
          url: '/chessboard/pieces.svg'
        }
      });

      // Calculate square size after board is rendered
      setTimeout(() => {
        if (boardRef.current) {
          const boardElement = boardRef.current.querySelector('.cm-chessboard');
          if (boardElement) {
            const actualWidth = boardElement.clientWidth;
            setSquareSize(actualWidth / 8);
          }
        }
      }, 100);
    }

    return () => {
      if (chessboardRef.current) {
        chessboardRef.current.destroy();
        chessboardRef.current = null;
      }
    };
  }, []);

  // Update position when it changes
  useEffect(() => {
    if (chessboardRef.current) {
      chessboardRef.current.setPosition(position, true);
    }
  }, [position]);

  // Recalculate square size when width changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (boardRef.current) {
        const boardElement = boardRef.current.querySelector('.cm-chessboard');
        if (boardElement) {
          const actualWidth = boardElement.clientWidth;
          setSquareSize(actualWidth / 8);
        }
      }
    }, 100);
    return () => clearTimeout(timer);
  }, [width]);

  return (
    <>
      <style jsx global>{`
        .cm-chessboard {
          width: 100% !important;
          max-width: ${width}px;
        }
      `}</style>
      <div style={{ position: 'relative', width: '100%', maxWidth: `${width}px` }}>
        <div ref={boardRef} style={{ width: '100%', maxWidth: `${width}px` }} />
        <ChessAnnotations
          annotations={annotations}
          squareSize={squareSize}
          boardWidth={squareSize * 8}
          orientation="white"
        />
      </div>
    </>
  );
}
