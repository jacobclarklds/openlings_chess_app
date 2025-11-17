/**
 * Chess-specific constants and configuration
 */

export const PIECE_VALUES: { [key: string]: number } = {
  p: 1, n: 3, b: 3, r: 5, q: 9,
  P: 1, N: 3, B: 3, R: 5, Q: 9,
};

export const PIECE_SYMBOLS: { [key: string]: string } = {
  p: '♟', n: '♞', b: '♝', r: '♜', q: '♛', k: '♚',
  P: '♙', N: '♘', B: '♗', R: '♖', Q: '♕', K: '♔',
};

export const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
export const RANKS = ['8', '7', '6', '5', '4', '3', '2', '1'];

export const ANIMATION_SPEEDS = {
  instant: 0,
  fast: 150,
  normal: 300,
  slow: 500,
};

export type PieceStyle = 'cburnett' | 'merida' | 'alpha' | 'cardinal' | 'staunty';

export const DEFAULT_BOARD_SETTINGS = {
  theme: 'brown',
  pieceStyle: 'cburnett' as PieceStyle,
  showCoordinates: true,
  highlightLastMove: true,
  highlightLegalMoves: true,
  animationSpeed: ANIMATION_SPEEDS.normal,
  autoQueen: true,
  soundEnabled: false,
};
