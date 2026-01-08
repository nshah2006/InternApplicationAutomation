/**
 * Landing page.
 */

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState(null);
  
  const handleExtractSchema = async (e) => {
    e.preventDefault();
    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }
    
    setIsExtracting(true);
    setError(null);
    
    try {
      // TODO: Call API and navigate to review page
      router.push(`/review?url=${encodeURIComponent(url)}`);
    } catch (err) {
      setError(err.message || 'Failed to extract form schema');
      setIsExtracting(false);
    }
  };
  
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Hero section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Resume Application Automation
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Automate your job applications by parsing resumes and mapping form fields
        </p>
      </div>
      
      {/* Quick actions */}
      <div className="grid md:grid-cols-2 gap-6 mb-12">
        {/* Upload Resume Card */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Upload Resume</h2>
          <p className="text-gray-600 mb-6">
            Upload your resume (PDF or DOCX) to extract structured information
            and prepare it for automatic form filling.
          </p>
          <Link href="/upload" className="btn-primary inline-block">
            Upload Resume
          </Link>
        </div>
        
        {/* Extract Form Schema Card */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Extract Form Schema</h2>
          <p className="text-gray-600 mb-6">
            Extract form fields from a job application page and get suggested
            mappings to your resume data.
          </p>
          <form onSubmit={handleExtractSchema} className="space-y-4">
            <div>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/job-application"
                className="input-field"
                disabled={isExtracting}
              />
              {error && (
                <p className="mt-2 text-sm text-red-600">{error}</p>
              )}
            </div>
            <button
              type="submit"
              className="btn-primary w-full"
              disabled={isExtracting}
            >
              {isExtracting ? 'Extracting...' : 'Extract Schema'}
            </button>
          </form>
        </div>
      </div>
      
      {/* Features */}
      <div className="card">
        <h2 className="text-2xl font-semibold mb-6">Features</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div>
            <h3 className="font-semibold mb-2">Resume Parsing</h3>
            <p className="text-gray-600 text-sm">
              Extract structured data from PDF and DOCX resume files
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Form Schema Extraction</h3>
            <p className="text-gray-600 text-sm">
              Automatically detect and extract form fields from job application pages
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Smart Mapping</h3>
            <p className="text-gray-600 text-sm">
              Intelligent field mapping with confidence scoring and review
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

