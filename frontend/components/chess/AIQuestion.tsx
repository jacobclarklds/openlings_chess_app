'use client';

import { useState } from 'react';
import { AIQuestion as AIQuestionType } from '@/types/chess';

interface AIQuestionProps {
    question: AIQuestionType;
}

export default function AIQuestion({ question }: AIQuestionProps) {
    const [userAnswer, setUserAnswer] = useState<string | null>(null);
    const [showExplanation, setShowExplanation] = useState(false);

    if (question.type === 'multiple_choice') {
        return (
            <div className="mt-6 p-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border-2 border-blue-200">
                <div className="flex items-start gap-3 mb-4">
                    <span className="text-2xl">🤔</span>
                    <p className="font-semibold text-gray-900 text-lg">{question.question}</p>
                </div>

                <div className="space-y-3">
                    {question.options?.map((option, idx) => {
                        const isSelected = userAnswer === option;
                        const isCorrect = option === question.correct_answer;
                        const showResult = isSelected && showExplanation;

                        return (
                            <button
                                key={idx}
                                onClick={() => {
                                    setUserAnswer(option);
                                    setShowExplanation(true);
                                }}
                                disabled={showExplanation}
                                className={`
                                    w-full text-left p-4 rounded-lg border-2
                                    transition-all duration-200
                                    ${showResult
                                        ? isCorrect
                                            ? 'border-green-500 bg-green-50 text-green-900'
                                            : 'border-red-500 bg-red-50 text-red-900'
                                        : isSelected
                                            ? 'border-indigo-500 bg-indigo-50'
                                            : 'border-gray-300 bg-white hover:border-indigo-400 hover:bg-indigo-50'
                                    }
                                    ${showExplanation ? 'cursor-not-allowed' : 'cursor-pointer'}
                                `}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="font-medium">{option}</span>
                                    {showResult && (
                                        <span className="text-xl">
                                            {isCorrect ? '✅' : '❌'}
                                        </span>
                                    )}
                                </div>
                            </button>
                        );
                    })}
                </div>

                {showExplanation && question.explanation && (
                    <div className="mt-6 p-4 bg-white rounded-lg border-l-4 border-indigo-500">
                        <p className="text-sm font-semibold text-indigo-900 mb-2">
                            Explanation:
                        </p>
                        <p className="text-sm text-gray-700">
                            {question.explanation}
                        </p>
                    </div>
                )}
            </div>
        );
    }

    if (question.type === 'move_selection') {
        return (
            <div className="mt-6 p-6 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border-2 border-green-200">
                <div className="flex items-start gap-3">
                    <span className="text-2xl">🎯</span>
                    <div>
                        <p className="font-semibold text-gray-900 text-lg mb-2">
                            {question.question}
                        </p>
                        <p className="text-sm text-gray-600">
                            Make your move on the board above!
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    return null;
}
