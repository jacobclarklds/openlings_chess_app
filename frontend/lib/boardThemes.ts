/**
 * Board theme definitions for professional chess appearance
 */

export interface BoardTheme {
  id: string;
  name: string;
  lightSquare: string;
  darkSquare: string;
  coordColor: string;
  borderColor: string;
}

export const BOARD_THEMES: BoardTheme[] = [
  {
    id: 'brown',
    name: 'Classic Brown',
    lightSquare: '#f0d9b5',
    darkSquare: '#b58863',
    coordColor: '#9c7f5f',
    borderColor: '#8b7355',
  },
  {
    id: 'green',
    name: 'Tournament Green',
    lightSquare: '#eeeed2',
    darkSquare: '#769656',
    coordColor: '#5d7a45',
    borderColor: '#5d7a45',
  },
  {
    id: 'blue',
    name: 'Modern Blue',
    lightSquare: '#dee3e6',
    darkSquare: '#8ca2ad',
    coordColor: '#6b828c',
    borderColor: '#6b828c',
  },
  {
    id: 'gray',
    name: 'Minimal Gray',
    lightSquare: '#e8e8e8',
    darkSquare: '#4f4f4f',
    coordColor: '#404040',
    borderColor: '#404040',
  }
];

export function getBoardTheme(id: string): BoardTheme {
  return BOARD_THEMES.find(theme => theme.id === id) || BOARD_THEMES[0];
}
