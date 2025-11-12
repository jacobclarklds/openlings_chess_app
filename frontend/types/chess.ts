export interface BoardAnnotation {
    type: 'arrow' | 'circle' | 'highlight';
    color: 'red' | 'green' | 'blue' | 'yellow' | 'orange';
    from?: string;
    to?: string;
    square?: string;
    id: string;
}

export interface AIQuestion {
    id: string;
    type: 'multiple_choice' | 'move_selection' | 'text';
    question: string;
    options?: string[];
    correct_answer?: string;
    explanation?: string;
}

export interface CoachComment {
    id: string;
    text: string;
    position_fen: string;
    annotations: BoardAnnotation[];
    move_to_make?: string;
    timestamp: number;
    question?: AIQuestion;
}

export interface Lesson {
    id: number;
    user_id: number;
    game_id?: number;
    title: string;
    comments: CoachComment[];
    focus_areas?: string[];
    created_at: string;
}

export interface LessonSummary {
    id: number;
    title: string;
    game_id?: number;
    created_at: string;
    comment_count: number;
}
