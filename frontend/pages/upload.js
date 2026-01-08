/**
 * Resume upload page.
 */

import { useState } from 'react';
import { useRouter } from 'next/router';
import { uploadResume } from '../lib/api';

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      // Validate file type
      const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!validTypes.includes(selectedFile.type)) {
        setError('Please upload a PDF or DOCX file');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError(null);
      setResult(null);
    }
  };
  
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }
    
    setIsUploading(true);
    setError(null);
    
    try {
      const response = await uploadResume(file);
      setResult(response);
      // TODO: Navigate to review page or show success message
    } catch (err) {
      setError(err.message || 'Failed to upload resume');
    } finally {
      setIsUploading(false);
    }
  };
  
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="card">
        <h1 className="text-3xl font-bold mb-6">Upload Resume</h1>
        
        <form onSubmit={handleUpload} className="space-y-6">
          {/* File input */}
          <div>
            <label htmlFor="file" className="block text-sm font-medium text-gray-700 mb-2">
              Select Resume File
            </label>
            <input
              id="file"
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
              disabled={isUploading}
            />
            {file && (
              <p className="mt-2 text-sm text-gray-600">
                Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </p>
            )}
          </div>
          
          {/* Error message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
          
          {/* Success message */}
          {result && result.success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800">
                {result.message || 'Resume uploaded successfully!'}
              </p>
              {result.resume_id && (
                <p className="text-sm text-green-700 mt-1">
                  Resume ID: {result.resume_id}
                </p>
              )}
            </div>
          )}
          
          {/* Submit button */}
          <div className="flex gap-4">
            <button
              type="submit"
              className="btn-primary"
              disabled={!file || isUploading}
            >
              {isUploading ? 'Uploading...' : 'Upload Resume'}
            </button>
            <button
              type="button"
              onClick={() => router.push('/')}
              className="btn-secondary"
              disabled={isUploading}
            >
              Cancel
            </button>
          </div>
        </form>
        
        {/* Instructions */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <h2 className="text-lg font-semibold mb-4">Instructions</h2>
          <ul className="list-disc list-inside space-y-2 text-sm text-gray-600">
            <li>Supported formats: PDF and DOCX</li>
            <li>Maximum file size: 10MB (recommended)</li>
            <li>The resume will be parsed to extract structured information</li>
            <li>You can review and edit the extracted data before mapping</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

