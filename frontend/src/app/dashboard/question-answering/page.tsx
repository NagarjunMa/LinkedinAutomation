'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Loader2, Copy, RefreshCw, Sparkles, FileText, MessageSquare, Clock, CheckCircle2 } from 'lucide-react';

interface GeneratedAnswer {
  question: string;
  answer: string;
  word_count: number;
  char_count: number;
}

interface AnswerResponse {
  answers: GeneratedAnswer[];
  total_generated: number;
}

export default function QuestionAnsweringPage() {
  const [jobId, setJobId] = useState('sample-job-id');
  const [jobDescription, setJobDescription] = useState('');
  const [questionsText, setQuestionsText] = useState('');
  const [answers, setAnswers] = useState<GeneratedAnswer[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [regeneratingIndex, setRegeneratingIndex] = useState<number | null>(null);

  const generateAnswers = async () => {
    if (!questionsText.trim()) {
      alert('Please enter some questions');
      return;
    }

    const questions = questionsText.split('\n').filter(q => q.trim());
    if (questions.length === 0) {
      alert('Please enter at least one question');
      return;
    }

    if (questions.length > 10) {
      alert('Maximum 10 questions per batch');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await fetch('/api/v1/application-questions/generate-answers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: jobId,
          questions_text: questionsText,
          job_description: jobDescription.trim() || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate answers');
      }

      const data: AnswerResponse = await response.json();
      setAnswers(data.answers);
      alert(`Generated ${data.total_generated} answers successfully!`);
    } catch (error) {
      console.error('Error generating answers:', error);
      alert(error instanceof Error ? error.message : 'Failed to generate answers');
    } finally {
      setIsGenerating(false);
    }
  };

  const regenerateAnswer = async (index: number) => {
    const question = answers[index].question;
    setRegeneratingIndex(index);

    try {
      const response = await fetch('/api/v1/application-questions/generate-answers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: jobId,
          questions_text: question,
          job_description: jobDescription.trim() || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to regenerate answer');
      }

      const data: AnswerResponse = await response.json();
      if (data.answers.length > 0) {
        const newAnswers = [...answers];
        newAnswers[index] = data.answers[0];
        setAnswers(newAnswers);
        alert('Answer regenerated successfully!');
      }
    } catch (error) {
      console.error('Error regenerating answer:', error);
      alert(error instanceof Error ? error.message : 'Failed to regenerate answer');
    } finally {
      setRegeneratingIndex(null);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      alert('Copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy:', error);
      alert('Failed to copy to clipboard');
    }
  };

  const copyAllAnswers = async () => {
    const allAnswersText = answers
      .map((answer) => `Q: ${answer.question}\n\nA: ${answer.answer}`)
      .join('\n\n---\n\n');

    await copyToClipboard(allAnswersText);
  };

  const questionCount = questionsText.split('\n').filter(q => q.trim()).length;

  return (
    <div className="min-h-screen bg-primary-950">
      <div className="max-w-7xl mx-auto p-3 sm:p-4 lg:p-6 space-y-4 sm:space-y-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-accent-500/20 rounded-lg">
              <MessageSquare className="h-6 w-6 text-accent-500" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl xl:text-4xl 2xl:text-4xl font-bold text-cream-50">
                Application Question Generator
              </h1>
              <p className="text-cream-300 text-sm sm:text-base lg:text-lg xl:text-lg 2xl:text-lg mt-1">
                Generate authentic answers based on your actual experience
              </p>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4 mb-6">
            <Card className="premium-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-accent-500" />
                  <div>
                    <p className="text-sm text-cream-300">Questions Ready</p>
                    <p className="text-2xl font-bold text-cream-50">
                      {questionCount}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="premium-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Sparkles className="h-5 w-5 text-gold-500" />
                  <div>
                    <p className="text-sm text-cream-300">Answers Generated</p>
                    <p className="text-2xl font-bold text-cream-50">
                      {answers.length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="premium-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Clock className="h-5 w-5 text-accent-400" />
                  <div>
                    <p className="text-sm text-cream-300">Avg Word Count</p>
                    <p className="text-2xl font-bold text-cream-50">
                      {answers.length > 0
                        ? Math.round(answers.reduce((sum, a) => sum + a.word_count, 0) / answers.length)
                        : 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
          {/* Left Column - Input */}
          <div className="space-y-4 sm:space-y-6">
            <Card className="premium-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-cream-50">
                  <FileText className="h-5 w-5 text-accent-500" />
                  Question Input
                </CardTitle>
                <CardDescription className="text-cream-300">
                  Enter your application questions (one per line, max 10)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="job-id">Job Reference (Optional)</Label>
                  <Input
                    id="job-id"
                    value={jobId}
                    onChange={(e) => setJobId(e.target.value)}
                    placeholder="Enter job ID or reference"
                  />
                </div>

                <div>
                  <Label htmlFor="job-description">Job Description (Optional)</Label>
                  <Textarea
                    id="job-description"
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="Paste the job description here to get more tailored answers...

Requirements:
- 3+ years of React experience
- Knowledge of TypeScript
- Experience with REST APIs
- Strong problem-solving skills"
                    className="min-h-[120px] resize-y"
                  />
                  <p className="text-sm text-cream-300 mt-1">
                    Adding job details helps generate more targeted answers
                  </p>
                </div>

                <div>
                  <Label htmlFor="questions">
                    Application Questions
                    <Badge variant="secondary" className="ml-2">
                      {questionCount}/10
                    </Badge>
                  </Label>
                  <Textarea
                    id="questions"
                    value={questionsText}
                    onChange={(e) => setQuestionsText(e.target.value)}
                    placeholder="Why do you want to work at our company?
Tell us about a challenging project you worked on.
How do you handle tight deadlines?
What interests you most about this role?"
                    className="min-h-[200px] resize-y"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Enter each question on a new line
                  </p>
                </div>

                <Button
                  onClick={generateAnswers}
                  disabled={isGenerating || questionCount === 0 || questionCount > 10}
                  className="w-full"
                  size="lg"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Generating Answers...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 mr-2" />
                      Generate {questionCount} Answer{questionCount !== 1 ? 's' : ''}
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Usage Tips */}
            <Card className="premium-card">
              <CardHeader>
                <CardTitle className="text-lg text-cream-50">Tips for Best Results</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-cream-300">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 text-gold-500 mt-0.5 flex-shrink-0" />
                    Keep questions specific and clear
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 text-gold-500 mt-0.5 flex-shrink-0" />
                    Upload your resume first for better personalization
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 text-gold-500 mt-0.5 flex-shrink-0" />
                    Generated answers are based on your actual experience
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 text-gold-500 mt-0.5 flex-shrink-0" />
                    Review and customize answers before submitting
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Generated Answers */}
          <div className="space-y-4 sm:space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-cream-50">
                Generated Answers
              </h2>
              {answers.length > 0 && (
                <Button onClick={copyAllAnswers} variant="outline" size="sm">
                  <Copy className="h-4 w-4 mr-2" />
                  Copy All
                </Button>
              )}
            </div>

            {answers.length === 0 && !isGenerating && (
              <Card className="premium-card">
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <MessageSquare className="h-12 w-12 text-cream-400 mb-4" />
                  <h3 className="text-lg font-medium text-cream-50 mb-2">
                    No answers generated yet
                  </h3>
                  <p className="text-cream-300">
                    Enter your questions and click &quot;Generate Answers&quot; to get started
                  </p>
                </CardContent>
              </Card>
            )}

            {isGenerating && (
              <Card className="premium-card">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 text-accent-500 animate-spin mb-4" />
                  <p className="text-cream-300">
                    Generating personalized answers based on your experience...
                  </p>
                </CardContent>
              </Card>
            )}

            {answers.map((answer, index) => (
              <Card key={index} className="premium-card border-l-4 border-l-accent-500">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-4">
                    <CardTitle className="text-lg leading-relaxed text-cream-50">
                      {answer.question}
                    </CardTitle>
                    <div className="flex gap-2 flex-shrink-0">
                      <Button
                        onClick={() => regenerateAnswer(index)}
                        disabled={regeneratingIndex === index}
                        variant="outline"
                        size="sm"
                      >
                        {regeneratingIndex === index ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <RefreshCw className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        onClick={() => copyToClipboard(answer.answer)}
                        variant="outline"
                        size="sm"
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="prose dark:prose-invert max-w-none">
                    <p className="text-cream-200 leading-relaxed whitespace-pre-wrap">
                      {answer.answer}
                    </p>
                  </div>
                  <div className="flex gap-4 mt-4 pt-4 border-t border-primary-600">
                    <Badge variant="secondary">
                      {answer.word_count} words
                    </Badge>
                    <Badge variant="secondary">
                      {answer.char_count} characters
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}