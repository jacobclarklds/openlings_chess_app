/**
 * API client for lesson endpoints
 */

import { CoachComment } from '@/types/chess';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface LessonCreateRequest {
    game_id?: number;
    pgn: string;
    title?: string;
    focus_areas?: string[];
}

export interface LessonResponse {
    id: number;
    user_id: number;
    game_id?: number;
    title: string;
    description?: string;
    focus_areas: string[];
    user_elo_at_creation: number;
    status: 'generating' | 'completed' | 'failed';
    error_message?: string;
    created_at: string;
    completed_at?: string;
    comments: CoachComment[];
}

export interface LessonListItem {
    id: number;
    title: string;
    description?: string;
    focus_areas: string[];
    status: 'generating' | 'completed' | 'failed';
    created_at: string;
    completed_at?: string;
    comment_count: number;
}

export interface UserLessonProgress {
    id: number;
    user_id: number;
    lesson_id: number;
    current_step: number;
    completed: boolean;
    answers: Record<string, any>;
    started_at: string;
    completed_at?: string;
    last_accessed: string;
}

export interface ProgressUpdate {
    current_step?: number;
    completed?: boolean;
    answer?: Record<string, any>;
}

/**
 * Get authentication token from localStorage
 */
function getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
}

/**
 * Create a new lesson from a game
 */
export async function createLesson(data: LessonCreateRequest): Promise<LessonResponse> {
    const token = getAuthToken();
    const response = await fetch(`${API_BASE}/lessons/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create lesson');
    }

    return response.json();
}

/**
 * Get all lessons for the current user
 */
export async function getLessons(
    skip: number = 0,
    limit: number = 20,
    statusFilter?: string
): Promise<LessonListItem[]> {
    const token = getAuthToken();
    const params = new URLSearchParams({
        skip: skip.toString(),
        limit: limit.toString(),
        ...(statusFilter ? { status_filter: statusFilter } : {})
    });

    const response = await fetch(`${API_BASE}/lessons/?${params}`, {
        headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch lessons');
    }

    return response.json();
}

/**
 * Get a specific lesson with all comments
 */
export async function getLesson(lessonId: number): Promise<LessonResponse> {
    const token = getAuthToken();
    const response = await fetch(`${API_BASE}/lessons/${lessonId}`, {
        headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch lesson');
    }

    return response.json();
}

/**
 * Delete a lesson
 */
export async function deleteLesson(lessonId: number): Promise<void> {
    const token = getAuthToken();
    const response = await fetch(`${API_BASE}/lessons/${lessonId}`, {
        method: 'DELETE',
        headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete lesson');
    }
}

/**
 * Get user's progress for a lesson
 */
export async function getLessonProgress(lessonId: number): Promise<UserLessonProgress> {
    const token = getAuthToken();
    const response = await fetch(`${API_BASE}/lessons/${lessonId}/progress`, {
        headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch lesson progress');
    }

    return response.json();
}

/**
 * Update user's progress for a lesson
 */
export async function updateLessonProgress(
    lessonId: number,
    update: ProgressUpdate
): Promise<UserLessonProgress> {
    const token = getAuthToken();
    const response = await fetch(`${API_BASE}/lessons/${lessonId}/progress`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(update)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update lesson progress');
    }

    return response.json();
}

/**
 * Poll for lesson completion
 * Returns true when lesson is completed, false if still generating
 * Throws error if lesson generation failed
 */
export async function pollLessonStatus(
    lessonId: number,
    maxAttempts: number = 60,
    intervalMs: number = 2000
): Promise<LessonResponse> {
    for (let i = 0; i < maxAttempts; i++) {
        const lesson = await getLesson(lessonId);
        
        if (lesson.status === 'completed') {
            return lesson;
        }
        
        if (lesson.status === 'failed') {
            throw new Error(lesson.error_message || 'Lesson generation failed');
        }
        
        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, intervalMs));
    }
    
    throw new Error('Lesson generation timed out');
}
