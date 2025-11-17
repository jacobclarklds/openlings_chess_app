'use client';

import { BoardAnnotation } from '@/types/chess';

interface ChessAnnotationsProps {
  annotations: BoardAnnotation[];
  squareSize: number;
  boardWidth: number;
  orientation?: 'white' | 'black';
}

export default function ChessAnnotations({
  annotations,
  squareSize,
  boardWidth,
  orientation = 'white'
}: ChessAnnotationsProps) {
  // Convert chess square notation (e.g., 'e4') to pixel coordinates
  const squareToCoords = (square: string): { x: number; y: number } => {
    const file = square.charCodeAt(0) - 'a'.charCodeAt(0); // 0-7 for a-h
    const rank = parseInt(square[1]) - 1; // 0-7 for 1-8

    // Adjust for board orientation
    const x = orientation === 'white' ? file : 7 - file;
    const y = orientation === 'white' ? 7 - rank : rank;

    return {
      x: x * squareSize + squareSize / 2,
      y: y * squareSize + squareSize / 2
    };
  };

  // Color mapping for annotations
  const colorMap: Record<string, string> = {
    red: '#ef4444',
    green: '#22c55e',
    blue: '#3b82f6',
    yellow: '#eab308',
    orange: '#f97316',
    purple: '#a855f7',
    cyan: '#06b6d4'
  };

  const getColor = (color: string) => colorMap[color] || color;

  return (
    <svg
      className="absolute top-0 left-0 pointer-events-none"
      style={{ width: boardWidth, height: boardWidth }}
      viewBox={`0 0 ${boardWidth} ${boardWidth}`}
    >
      <defs>
        {/* Arrow markers for each color */}
        {Object.entries(colorMap).map(([name, color]) => (
          <marker
            key={`arrow-${name}`}
            id={`arrow-head-${name}`}
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L9,3 z" fill={color} />
          </marker>
        ))}
      </defs>

      {annotations.map((annotation) => {
        const color = getColor(annotation.color);

        // Draw arrows
        if (annotation.type === 'arrow' && annotation.from && annotation.to) {
          const from = squareToCoords(annotation.from);
          const to = squareToCoords(annotation.to);

          // Calculate arrow direction for offsetting endpoints
          const dx = to.x - from.x;
          const dy = to.y - from.y;
          const length = Math.sqrt(dx * dx + dy * dy);
          const ux = dx / length;
          const uy = dy / length;

          // Offset start and end points to avoid covering pieces
          const offset = squareSize * 0.25;
          const x1 = from.x + ux * offset;
          const y1 = from.y + uy * offset;
          const x2 = to.x - ux * offset;
          const y2 = to.y - uy * offset;

          return (
            <line
              key={annotation.id}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={color}
              strokeWidth={squareSize * 0.15}
              strokeLinecap="round"
              markerEnd={`url(#arrow-head-${annotation.color})`}
              opacity={0.8}
            />
          );
        }

        // Draw circles
        if (annotation.type === 'circle' && annotation.square) {
          const center = squareToCoords(annotation.square);
          const radius = squareSize * 0.4;

          return (
            <circle
              key={annotation.id}
              cx={center.x}
              cy={center.y}
              r={radius}
              fill="none"
              stroke={color}
              strokeWidth={squareSize * 0.1}
              opacity={0.7}
            />
          );
        }

        // Draw highlights (filled squares with transparency)
        if (annotation.type === 'highlight' && annotation.square) {
          const coords = squareToCoords(annotation.square);
          const x = coords.x - squareSize / 2;
          const y = coords.y - squareSize / 2;

          return (
            <rect
              key={annotation.id}
              x={x}
              y={y}
              width={squareSize}
              height={squareSize}
              fill={color}
              opacity={0.3}
            />
          );
        }

        // Draw dots (small filled circles)
        if (annotation.type === 'dot' && annotation.square) {
          const center = squareToCoords(annotation.square);
          const radius = squareSize * 0.15;

          return (
            <circle
              key={annotation.id}
              cx={center.x}
              cy={center.y}
              r={radius}
              fill={color}
              opacity={0.8}
            />
          );
        }

        return null;
      })}
    </svg>
  );
}
