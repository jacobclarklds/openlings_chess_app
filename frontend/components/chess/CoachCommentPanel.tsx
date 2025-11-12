'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CoachComment } from '@/types/chess';
import AIQuestion from './AIQuestion';

interface CoachCommentPanelProps {
    comment: CoachComment;
    currentIndex: number;
    totalComments: number;
    onNext: () => void;
    onPrevious: () => void;
}

export default function CoachCommentPanel({
    comment,
    currentIndex,
    totalComments,
    onNext,
    onPrevious
}: CoachCommentPanelProps) {
    if (!comment) {
        return <div className="bg-white rounded-lg shadow-lg p-6">No comment available</div>;
    }

    return (
        <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl">
            {/* Progress Bar */}
            <div className="mb-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                        className="bg-indigo-600 h-2 rounded-full transition-all"
                        style={{ width: `${((currentIndex + 1) / totalComments) * 100}%` }}
                    />
                </div>
            </div>

            {/* Navigation Header */}
            <div className="flex justify-between items-center mb-6">
                <span className="text-sm font-medium text-gray-600">
                    Step {currentIndex + 1} of {totalComments}
                </span>

                <div className="flex gap-2">
                    <button
                        onClick={onPrevious}
                        disabled={currentIndex === 0}
                        className="px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200
                                 disabled:opacity-50 disabled:cursor-not-allowed
                                 transition-colors"
                    >
                        ← Previous
                    </button>

                    <button
                        onClick={onNext}
                        disabled={currentIndex === totalComments - 1}
                        className="px-4 py-2 rounded-lg bg-indigo-600 text-white
                                 hover:bg-indigo-700 disabled:opacity-50
                                 disabled:cursor-not-allowed transition-colors"
                    >
                        Next →
                    </button>
                </div>
            </div>

            {/* Markdown Content */}
            <div className="prose prose-sm max-w-none mb-6">
                <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                        h1: ({ node, ...props }) => (
                            <h1 className="text-2xl font-bold text-gray-900 mb-4" {...props} />
                        ),
                        h2: ({ node, ...props }) => (
                            <h2 className="text-xl font-semibold text-gray-800 mb-3" {...props} />
                        ),
                        strong: ({ node, ...props }) => (
                            <strong className="text-indigo-700 font-bold" {...props} />
                        ),
                        em: ({ node, ...props }) => (
                            <em className="text-purple-600" {...props} />
                        ),
                        code: ({ node, ...props }) => (
                            <code className="bg-gray-100 px-2 py-1 rounded font-mono text-sm" {...props} />
                        ),
                        p: ({ node, ...props }) => (
                            <p className="mb-4 text-gray-700 leading-relaxed" {...props} />
                        ),
                        ul: ({ node, ...props }) => (
                            <ul className="list-disc list-inside mb-4 space-y-2" {...props} />
                        ),
                        li: ({ node, ...props }) => (
                            <li className="text-gray-700" {...props} />
                        )
                    }}
                >
                    {comment.text}
                </ReactMarkdown>
            </div>

            {/* Interactive Question */}
            {comment.question && (
                <AIQuestion question={comment.question} />
            )}
        </div>
    );
}
