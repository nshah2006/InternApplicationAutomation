/**
 * AI text generation page.
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { generateAIText, approveAIGeneration, getAIGenerations } from '../lib/api';

export default function AIGeneratePage() {
  const router = useRouter();
  const { resume_id } = router.query;
  
  const [resumeId, setResumeId] = useState(resume_id || '');
  const [jobDescription, setJobDescription] = useState('');
  const [fieldType, setFieldType] = useState('cover_letter');
  const [maxLength, setMaxLength] = useState(500);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [currentGeneration, setCurrentGeneration] = useState(null);
  const [approvedText, setApprovedText] = useState('');
  const [isApproving, setIsApproving] = useState(false);
  const [generationHistory, setGenerationHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  
  // Load generation history if resume_id is provided
  useEffect(() => {
    if (resume_id) {
      loadGenerationHistory();
    }
  }, [resume_id]);
  
  const loadGenerationHistory = async () => {
    try {
      const response = await getAIGenerations(resume_id);
      if (response.success && response.generations) {
        setGenerationHistory(response.generations);
      }
    } catch (err) {
      console.error('Failed to load generation history:', err);
    }
  };
  
  const handleGenerate = async (e) => {
    e.preventDefault();
    
    if (!resumeId) {
      setError('Please enter a resume ID');
      return;
    }
    
    if (!jobDescription.trim()) {
      setError('Please enter a job description');
      return;
    }
    
    setIsGenerating(true);
    setError(null);
    setCurrentGeneration(null);
    setApprovedText('');
    
    try {
      const response = await generateAIText(
        parseInt(resumeId),
        jobDescription,
        fieldType,
        maxLength
      );
      
      if (response.success) {
        setCurrentGeneration(response);
        setApprovedText(response.suggested_text || '');
        // Reload history
        if (resume_id) {
          loadGenerationHistory();
        }
      } else {
        setError(response.message || 'Failed to generate text');
      }
    } catch (err) {
      setError(err.message || 'Failed to generate AI text');
    } finally {
      setIsGenerating(false);
    }
  };
  
  const handleApprove = async () => {
    if (!currentGeneration || !currentGeneration.generation_id) {
      setError('No generation to approve');
      return;
    }
    
    setIsApproving(true);
    setError(null);
    
    try {
      const response = await approveAIGeneration(
        currentGeneration.generation_id,
        approvedText || currentGeneration.suggested_text
      );
      
      if (response.success) {
        setCurrentGeneration({ ...currentGeneration, is_approved: true });
        // Reload history
        if (resume_id) {
          loadGenerationHistory();
        }
        alert('Text approved successfully!');
      } else {
        setError(response.message || 'Failed to approve text');
      }
    } catch (err) {
      setError(err.message || 'Failed to approve text');
    } finally {
      setIsApproving(false);
    }
  };
  
  const fieldTypes = [
    { value: 'cover_letter', label: 'Cover Letter' },
    { value: 'personal_statement', label: 'Personal Statement' },
    { value: 'why_this_role', label: 'Why This Role' },
    { value: 'additional_info', label: 'Additional Information' },
  ];
  
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-4">AI Text Generation</h1>
        <p className="text-gray-600 mb-6">
          Generate personalized text fields based on your resume and job description.
          All prompts and outputs are stored for review.
        </p>
      </div>
      
      {/* Generation Form */}
      <div className="card mb-6">
        <form onSubmit={handleGenerate}>
          <div className="space-y-4">
            {/* Resume ID */}
            <div>
              <label htmlFor="resume_id" className="block text-sm font-medium text-gray-700 mb-1">
                Resume ID *
              </label>
              <input
                type="number"
                id="resume_id"
                value={resumeId}
                onChange={(e) => setResumeId(e.target.value)}
                placeholder="Enter resume profile ID"
                className="input-field w-full"
                required
                disabled={!!resume_id}
              />
              {resume_id && (
                <p className="mt-1 text-sm text-gray-500">Using resume ID from URL: {resume_id}</p>
              )}
            </div>
            
            {/* Field Type */}
            <div>
              <label htmlFor="field_type" className="block text-sm font-medium text-gray-700 mb-1">
                Field Type *
              </label>
              <select
                id="field_type"
                value={fieldType}
                onChange={(e) => setFieldType(e.target.value)}
                className="input-field w-full"
                required
              >
                {fieldTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            
            {/* Job Description */}
            <div>
              <label htmlFor="job_description" className="block text-sm font-medium text-gray-700 mb-1">
                Job Description *
              </label>
              <textarea
                id="job_description"
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the job description here..."
                rows={8}
                className="input-field w-full"
                required
              />
              <p className="mt-1 text-sm text-gray-500">
                Only the job description and your normalized resume are sent to the AI.
              </p>
            </div>
            
            {/* Max Length */}
            <div>
              <label htmlFor="max_length" className="block text-sm font-medium text-gray-700 mb-1">
                Maximum Length (characters)
              </label>
              <input
                type="number"
                id="max_length"
                value={maxLength}
                onChange={(e) => setMaxLength(parseInt(e.target.value) || 500)}
                min={100}
                max={2000}
                className="input-field w-full"
              />
            </div>
            
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}
            
            <button
              type="submit"
              className="btn-primary w-full"
              disabled={isGenerating || !resumeId || !jobDescription.trim()}
            >
              {isGenerating ? 'Generating...' : 'Generate Text'}
            </button>
          </div>
        </form>
      </div>
      
      {/* Current Generation */}
      {currentGeneration && (
        <div className="card mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">AI Suggestion</h2>
            {currentGeneration.is_approved && (
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                Approved
              </span>
            )}
          </div>
          
          <div className="mb-4">
            <label htmlFor="approved_text" className="block text-sm font-medium text-gray-700 mb-2">
              Generated Text (you can edit before approving)
            </label>
            <textarea
              id="approved_text"
              value={approvedText}
              onChange={(e) => setApprovedText(e.target.value)}
              rows={12}
              className="input-field w-full font-mono text-sm"
              disabled={currentGeneration.is_approved}
            />
            <p className="mt-2 text-sm text-gray-500">
              Character count: {approvedText.length} / {maxLength}
            </p>
          </div>
          
          {!currentGeneration.is_approved && (
            <div className="flex gap-4">
              <button
                onClick={handleApprove}
                className="btn-primary"
                disabled={isApproving || !approvedText.trim()}
              >
                {isApproving ? 'Approving...' : 'Approve Text'}
              </button>
              <button
                onClick={() => {
                  setCurrentGeneration(null);
                  setApprovedText('');
                }}
                className="btn-secondary"
              >
                Discard
              </button>
            </div>
          )}
          
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Generation ID: {currentGeneration.generation_id} | 
              Field Type: {fieldType} | 
              Created: {new Date().toLocaleString()}
            </p>
          </div>
        </div>
      )}
      
      {/* Generation History */}
      {resume_id && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Generation History</h2>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              {showHistory ? 'Hide' : 'Show'} History
            </button>
          </div>
          
          {showHistory && (
            <div className="space-y-4">
              {generationHistory.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No generation history yet.</p>
              ) : (
                generationHistory.map((gen) => (
                  <div
                    key={gen.id}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <span className="font-medium">{gen.field_type}</span>
                        {gen.is_approved && (
                          <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                            Approved
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(gen.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-3">
                      {gen.suggested_text || gen.approved_text || 'No text available'}
                    </p>
                    <p className="text-xs text-gray-500 mt-2">
                      Generation ID: {gen.id}
                    </p>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

