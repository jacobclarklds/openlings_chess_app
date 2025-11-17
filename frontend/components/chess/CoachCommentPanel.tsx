'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CoachComment } from '@/types/chess';
import AIQuestion from './AIQuestion';

interface CoachCommentPanelProps {
    comment: CoachComment | null | undefined;
    currentIndex: number;
    totalComments: number;
    onNext: () => void;
    onPrevious: () => void;
    canProceed?: boolean;
}

export default function CoachCommentPanel({
    comment,
    currentIndex,
    totalComments,
    onNext,
    onPrevious,
    canProceed = true
}: CoachCommentPanelProps) {
    if (!comment) {
        return <div className="bg-white/10 backdrop-blur border border-white/20 rounded-xl shadow-xl p-6 text-white">No comment available</div>;
    }

    return (
        <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl shadow-2xl p-6 max-w-2xl">
            {/* Progress Bar */}
            <div className="mb-5">
                <div className="w-full bg-white/20 rounded-full h-3 overflow-hidden">
                    <div
                        className="bg-gradient-to-r from-blue-400 to-cyan-400 h-3 rounded-full transition-all duration-500 shadow-lg"
                        style={{ width: `${((currentIndex + 1) / totalComments) * 100}%` }}
                    />
                </div>
            </div>

            {/* Navigation Header */}
            <div className="flex justify-between items-center mb-6">
                <span className="text-sm font-bold text-white bg-white/10 px-3 py-1 rounded-lg">
                    Step {currentIndex + 1} of {totalComments}
                </span>

                <div className="flex gap-2">
                    <button
                        onClick={onPrevious}
                        disabled={currentIndex === 0}
                        className="px-5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold
                                 disabled:opacity-30 disabled:cursor-not-allowed
                                 transition-all border border-white/20"
                    >
                        ← Previous
                    </button>

                    <button
                        onClick={onNext}
                        disabled={currentIndex === totalComments - 1 || !canProceed}
                        className="px-5 py-2 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold
                                 hover:from-blue-600 hover:to-cyan-600 disabled:opacity-30
                                 disabled:cursor-not-allowed transition-all shadow-lg"
                        title={!canProceed ? 'Make your move first!' : ''}
                    >
                        Next →
                    </button>
                </div>
            </div>

            {/* Markdown Content */}
            <div className="mb-6 text-white prose-invert">
                <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                        h1: ({ node, ...props }) => (
                            <h1 className="text-2xl font-bold text-white mb-4 mt-6 first:mt-0" {...props} />
                        ),
                        h2: ({ node, ...props }) => (
                            <h2 className="text-xl font-bold text-cyan-300 mb-3 mt-5 first:mt-0" {...props} />
                        ),
                        h3: ({ node, ...props }) => (
                            <h3 className="text-lg font-semibold text-cyan-200 mb-2 mt-4 first:mt-0" {...props} />
                        ),
                        strong: ({ node, ...props }) => (
                            <strong className="text-cyan-300 font-bold" {...props} />
                        ),
                        em: ({ node, ...props }) => (
                            <em className="text-blue-300 italic" {...props} />
                        ),
                        code: ({ node, ...props }) => (
                            <code className="bg-black/30 px-2 py-1 rounded font-mono text-sm text-cyan-200" {...props} />
                        ),
                        p: ({ node, ...props }) => (
                            <p className="mb-4 text-blue-100 leading-relaxed text-base last:mb-0" {...props} />
                        ),
                        ul: ({ node, ...props }) => (
                            <ul className="list-disc list-inside mb-4 space-y-2 ml-2" {...props} />
                        ),
                        ol: ({ node, ...props }) => (
                            <ol className="list-decimal list-inside mb-4 space-y-2 ml-2" {...props} />
                        ),
                        li: ({ node, ...props }) => (
                            <li className="text-blue-100" {...props} />
                        ),
                        blockquote: ({ node, ...props }) => (
                            <blockquote className="border-l-4 border-cyan-400 pl-4 my-4 italic text-blue-200" {...props} />
                        ),
                        hr: ({ node, ...props }) => (
                            <hr className="my-6 border-white/20" {...props} />
                        )
                    }}
                >
                    {comment?.text || ''}
                </ReactMarkdown>
            </div>

            {/* Interactive Question */}
            {comment?.question && (
                <AIQuestion question={comment.question} />
            )}
        </div>
    );
}
