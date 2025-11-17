import { BoardAnnotation } from '@/types/chess';

export interface HighlightOptions {
  lastMove?: { from: string; to: string };
  selected?: string;
  legalMoves?: string[];
  check?: string;
  premoves?: Array<{ from: string; to: string }>;
}

export function convertAnnotationsToArrows(
    annotations: BoardAnnotation[]
): Array<[string, string, string]> {
    return annotations
        .filter(ann => ann.type === 'arrow' && ann.from && ann.to)
        .map(ann => [
            ann.from!,
            ann.to!,
            getArrowColor(ann.color)
        ]);
}

export function getSquareStyles(
    annotations: BoardAnnotation[]
): { [square: string]: React.CSSProperties } {
    const styles: { [square: string]: React.CSSProperties } = {};

    annotations.forEach(ann => {
        if (ann.type === 'circle' && ann.square) {
            styles[ann.square] = {
                background: `radial-gradient(circle, transparent 65%, ${getColorHex(ann.color)} 70%, ${getColorHex(ann.color)} 80%, transparent 80%)`,
                borderRadius: '50%'
            };
        }

        if (ann.type === 'highlight' && ann.square) {
            styles[ann.square] = {
                backgroundColor: `${getColorHex(ann.color)}60`
            };
        }
    });

    return styles;
}

export function getEnhancedSquareStyles(
    annotations: BoardAnnotation[],
    highlights: HighlightOptions
): { [square: string]: React.CSSProperties } {
    const styles: { [square: string]: React.CSSProperties } = {};

    // Last move highlight
    if (highlights.lastMove) {
        styles[highlights.lastMove.from] = {
            backgroundColor: 'rgba(205, 210, 106, 0.4)',
        };
        styles[highlights.lastMove.to] = {
            backgroundColor: 'rgba(205, 210, 106, 0.4)',
        };
    }

    // Selected square
    if (highlights.selected) {
        styles[highlights.selected] = {
            ...styles[highlights.selected],
            backgroundColor: 'rgba(20, 85, 30, 0.4)',
        };
    }

    // Legal moves (small circles)
    highlights.legalMoves?.forEach(square => {
        styles[square] = {
            ...styles[square],
            background: `radial-gradient(circle, rgba(0, 0, 0, 0.15) 19%, transparent 20%)`,
        };
    });

    // Check highlight (with pulse animation)
    if (highlights.check) {
        styles[highlights.check] = {
            ...styles[highlights.check],
            backgroundColor: 'rgba(255, 64, 64, 0.4)',
            boxShadow: '0 0 10px rgba(255, 64, 64, 0.6)',
        };
    }

    // Premoves
    highlights.premoves?.forEach(({ from, to }) => {
        styles[from] = {
            ...styles[from],
            backgroundColor: 'rgba(62, 56, 48, 0.4)',
        };
        styles[to] = {
            ...styles[to],
            backgroundColor: 'rgba(62, 56, 48, 0.4)',
        };
    });

    // User annotations (arrows, circles, highlights) - overlay on top
    annotations.forEach(ann => {
        if (ann.type === 'circle' && ann.square) {
            const existingBg = styles[ann.square]?.background || 'transparent';
            styles[ann.square] = {
                ...styles[ann.square],
                background: `
                    radial-gradient(circle, transparent 65%, ${getColorHex(ann.color)} 70%, ${getColorHex(ann.color)} 80%, transparent 80%),
                    ${existingBg}
                `,
            };
        }

        if (ann.type === 'highlight' && ann.square) {
            styles[ann.square] = {
                ...styles[ann.square],
                backgroundColor: `${getColorHex(ann.color)}60`,
            };
        }
    });

    return styles;
}

function getColorHex(color: string): string {
    const colorMap: { [key: string]: string } = {
        'red': '#ef4444',
        'green': '#22c55e',
        'blue': '#3b82f6',
        'yellow': '#eab308',
        'orange': '#f97316'
    };
    return colorMap[color] || '#000000';
}

function getArrowColor(color: string): string {
    const rgbMap: { [key: string]: string } = {
        'red': 'rgb(239, 68, 68)',
        'green': 'rgb(34, 197, 94)',
        'blue': 'rgb(59, 130, 246)',
        'yellow': 'rgb(234, 179, 8)',
        'orange': 'rgb(249, 115, 22)'
    };
    return rgbMap[color] || 'rgb(0, 0, 0)';
}
