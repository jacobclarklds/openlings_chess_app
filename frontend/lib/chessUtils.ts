import { BoardAnnotation } from '@/types/chess';

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
                background: `radial-gradient(circle, transparent 65%, ${getColorHex(ann.color)} 70%)`,
                borderRadius: '50%'
            };
        }

        if (ann.type === 'highlight' && ann.square) {
            styles[ann.square] = {
                backgroundColor: `${getColorHex(ann.color)}40`
            };
        }
    });

    return styles;
}

function getColorHex(color: string): string {
    const colorMap: { [key: string]: string } = {
        'red': '#FF0000',
        'green': '#00FF00',
        'blue': '#0066FF',
        'yellow': '#FFFF00',
        'orange': '#FF8800'
    };
    return colorMap[color] || '#000000';
}

function getArrowColor(color: string): string {
    const rgbMap: { [key: string]: string } = {
        'red': 'rgb(255, 0, 0)',
        'green': 'rgb(0, 255, 0)',
        'blue': 'rgb(0, 102, 255)',
        'yellow': 'rgb(255, 255, 0)',
        'orange': 'rgb(255, 136, 0)'
    };
    return rgbMap[color] || 'rgb(0, 0, 0)';
}
