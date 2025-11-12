'use client';

import { useState, useEffect } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { BoardAnnotation, CoachComment } from '@/types/chess';
import { convertAnnotationsToArrows, getSquareStyles } from '@/lib/chessUtils';
import CoachCommentPanel from './CoachCommentPanel';

interface InteractiveCoachBoardProps {
    initialPosition: string;
    comments: CoachComment[];
    onUserMove?: (move: string) => void;
    onUserAnnotation?: (annotation: BoardAnnotation) => void;
    interactive?: boolean;
}

export default function InteractiveCoachBoard({
    initialPosition,
    comments,
    onUserMove,
    onUserAnnotation,
    interactive = false
}: InteractiveCoachBoardProps) {
    const [currentCommentIndex, setCurrentCommentIndex] = useState(0);
    const [position, setPosition] = useState(initialPosition);
    const [game, setGame] = useState(new Chess(initialPosition));
    const [annotations, setAnnotations] = useState<BoardAnnotation[]>([]);
    const [animatingMove, setAnimatingMove] = useState(false);

    const currentComment = comments[currentCommentIndex];

    // Update board when comment changes
    useEffect(() => {
        if (currentComment) {
            setPosition(currentComment.position_fen);
            setGame(new Chess(currentComment.position_fen));
            setAnnotations(currentComment.annotations);

            // Animate AI demonstration move
            if (currentComment.move_to_make) {
                setTimeout(() => {
                    animateMove(currentComment.move_to_make!);
                }, 500);
            }
        }
    }, [currentCommentIndex, currentComment]);

    function handlePieceDrop(sourceSquare: string, targetSquare: string): boolean {
        if (!interactive || animatingMove) return false;

        try {
            const move = game.move({
                from: sourceSquare,
                to: targetSquare,
                promotion: 'q'
            });

            if (move === null) return false;

            setPosition(game.fen());

            if (onUserMove) {
                onUserMove(move.san);
            }

            return true;
        } catch (e) {
            return false;
        }
    }

    function animateMove(uciMove: string) {
        setAnimatingMove(true);

        const from = uciMove.substring(0, 2);
        const to = uciMove.substring(2, 4);
        const promotion = uciMove.length > 4 ? uciMove[4] : undefined;

        try {
            const move = game.move({
                from,
                to,
                promotion
            });

            if (move) {
                setPosition(game.fen());
            }
        } catch (e) {
            console.error('Failed to animate move:', e);
        }

        setTimeout(() => {
            setAnimatingMove(false);
        }, 500);
    }

    function handleNext() {
        if (currentCommentIndex < comments.length - 1) {
            setCurrentCommentIndex(currentCommentIndex + 1);
        }
    }

    function handlePrevious() {
        if (currentCommentIndex > 0) {
            setCurrentCommentIndex(currentCommentIndex - 1);
        }
    }

    return (
        <div className="flex flex-col lg:flex-row gap-6 p-6">
            {/* Chess Board */}
            <div className="flex-1">
                <div className="max-w-[600px]">
                    <Chessboard
                        id="interactive-coach-board"
                        position={position}
                        onPieceDrop={interactive ? handlePieceDrop : undefined}
                        customArrows={convertAnnotationsToArrows(annotations)}
                        customSquareStyles={getSquareStyles(annotations)}
                        boardWidth={600}
                        arePiecesDraggable={interactive && !animatingMove}
                    />
                </div>
            </div>

            {/* Coach Comments Panel */}
            <div className="flex-1">
                <CoachCommentPanel
                    comment={currentComment}
                    currentIndex={currentCommentIndex}
                    totalComments={comments.length}
                    onNext={handleNext}
                    onPrevious={handlePrevious}
                />
            </div>
        </div>
    );
}
