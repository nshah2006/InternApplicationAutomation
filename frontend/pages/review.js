/**
 * Form schema review and mapping page.
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { extractFormSchema, getMappingReview, previewAutofill } from '../lib/api';
import PreviewToggle from '../components/PreviewToggle';
import PreviewBanner from '../components/PreviewBanner';

export default function ReviewPage() {
  const router = useRouter();
  const { url: urlParam, resume_id, schema_id } = router.query;
  
  const [url, setUrl] = useState(urlParam || '');
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState(null);
  const [schema, setSchema] = useState(null);
  const [mappings, setMappings] = useState(null);
  const [isLoadingMappings, setIsLoadingMappings] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [isActivatingPreview, setIsActivatingPreview] = useState(false);
  const [previewError, setPreviewError] = useState(null);
  const [resumeData, setResumeData] = useState(null);
  
  // Extract schema if URL is provided
  useEffect(() => {
    if (urlParam && !schema) {
      handleExtractSchema(urlParam);
    }
  }, [urlParam]);
  
  // Load mappings if IDs are provided
  useEffect(() => {
    if ((resume_id || schema_id) && schema) {
      loadMappings();
    }
  }, [resume_id, schema_id, schema]);
  
  const handleExtractSchema = async (targetUrl = url) => {
    if (!targetUrl.trim()) {
      setError('Please enter a URL');
      return;
    }
    
    setIsExtracting(true);
    setError(null);
    
    try {
      const response = await extractFormSchema(targetUrl, true);
      if (response.success && response.schema_data) {
        // Handle both schema_data.schema and direct schema
        const schemaData = response.schema_data.schema || response.schema_data;
        setSchema(schemaData);
      } else {
        setError(response.message || 'Failed to extract form schema');
      }
    } catch (err) {
      setError(err.message || 'Failed to extract form schema');
    } finally {
      setIsExtracting(false);
    }
  };
  
  const loadMappings = async () => {
    setIsLoadingMappings(true);
    try {
      const response = await getMappingReview(resume_id, schema_id);
      if (response.success) {
        if (response.mappings) {
          setMappings(response.mappings);
        }
        if (response.resume_data) {
          setResumeData(response.resume_data);
        }
      }
    } catch (err) {
      console.error('Failed to load mappings:', err);
    } finally {
      setIsLoadingMappings(false);
    }
  };
  
  const handlePreviewToggle = async (enabled) => {
    if (!enabled) {
      setPreviewMode(false);
      setPreviewError(null);
      return;
    }
    
    // Need resume_id, schema_id, and url to activate preview
    if (!resume_id || !schema_id || !url) {
      setPreviewError('Resume, schema, and URL are required for preview mode');
      return;
    }
    
    setIsActivatingPreview(true);
    setPreviewError(null);
    
    try {
      const response = await previewAutofill(
        parseInt(resume_id),
        parseInt(schema_id),
        url
      );
      
      if (response.success) {
        setPreviewMode(true);
        // Browser window should open automatically via Playwright
      } else {
        setPreviewError(response.message || 'Failed to activate preview mode');
      }
    } catch (err) {
      setPreviewError(err.message || 'Failed to activate preview mode');
      setPreviewMode(false);
    } finally {
      setIsActivatingPreview(false);
    }
  };
  
  const getMatchTypeColor = (matchType) => {
    switch (matchType) {
      case 'exact':
        return 'bg-green-100 text-green-800';
      case 'fuzzy':
        return 'bg-yellow-100 text-yellow-800';
      case 'ignored':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-red-100 text-red-800';
    }
  };
  
  return (
    <div className="min-h-screen">
      {/* Preview banner */}
      <PreviewBanner 
        isVisible={previewMode} 
        onClose={() => setPreviewMode(false)}
      />
      
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl font-bold">Form Schema Review</h1>
            {schema && resume_id && schema_id && (
              <PreviewToggle
                isActive={previewMode}
                onToggle={handlePreviewToggle}
                disabled={isActivatingPreview || !url}
              />
            )}
          </div>
          
          {/* Preview error */}
          {previewError && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800">{previewError}</p>
            </div>
          )}
          
          {/* URL input */}
          <div className="card mb-6">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleExtractSchema();
            }}
            className="flex gap-4"
          >
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/job-application"
              className="input-field flex-1"
              disabled={isExtracting}
            />
            <button
              type="submit"
              className="btn-primary"
              disabled={isExtracting || !url.trim()}
            >
              {isExtracting ? 'Extracting...' : 'Extract Schema'}
            </button>
          </form>
          
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
        </div>
      </div>
      
      {/* Schema display */}
      {schema && (
        <div className="space-y-6">
          {/* Schema info */}
          <div className="card">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-2xl font-semibold mb-2">{schema.title || 'Form Schema'}</h2>
                <p className="text-sm text-gray-600">{schema.url}</p>
              </div>
              {schema.platform && (
                <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
                  {schema.platform}
                </span>
              )}
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Total Fields:</span>
                <span className="ml-2 font-semibold">{schema.total_fields || 0}</span>
              </div>
              {schema.mapped_fields !== undefined && (
                <div>
                  <span className="text-gray-600">Mapped:</span>
                  <span className="ml-2 font-semibold text-green-600">{schema.mapped_fields}</span>
                </div>
              )}
              {schema.unmapped_fields !== undefined && (
                <div>
                  <span className="text-gray-600">Unmapped:</span>
                  <span className="ml-2 font-semibold text-red-600">{schema.unmapped_fields}</span>
                </div>
              )}
            </div>
          </div>
          
          {/* Fields list */}
          {schema.fields && schema.fields.length > 0 && (
            <div className="card">
              <h3 className="text-xl font-semibold mb-4">Form Fields</h3>
              <div className="space-y-4">
                {schema.fields.map((field, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium">
                            {field.label_text || field.placeholder || field.aria_label || field.name || 'Unnamed Field'}
                          </span>
                          {field.required && (
                            <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                              Required
                            </span>
                          )}
                          {field.mapping_match_type && (
                            <span className={`text-xs px-2 py-1 rounded ${getMatchTypeColor(field.mapping_match_type)}`}>
                              {field.mapping_match_type}
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-600 space-y-1">
                          {field.field_type && (
                            <span>Type: {field.input_type || field.field_type}</span>
                          )}
                          {field.suggested_canonical_field && (
                            <span className="ml-4">
                              → {field.suggested_canonical_field}
                              {field.mapping_confidence !== null && field.mapping_confidence !== undefined && (
                                <span className="text-gray-500">
                                  {' '}({(field.mapping_confidence * 100).toFixed(0)}%)
                                </span>
                              )}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    {field.normalized_field_name && (
                      <p className="text-xs text-gray-500 mt-2">
                        Normalized: {field.normalized_field_name}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Mappings review */}
          {isLoadingMappings && (
            <div className="card">
              <p className="text-gray-600">Loading mappings...</p>
            </div>
          )}
          
          {mappings && mappings.length > 0 && (
            <div className="card">
              <h3 className="text-xl font-semibold mb-4">Field Mappings</h3>
              <div className="space-y-3">
                {mappings.map((mapping, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{mapping.field_name}</span>
                      <span className={`text-xs px-2 py-1 rounded ${getMatchTypeColor(mapping.match_type)}`}>
                        {mapping.match_type}
                      </span>
                    </div>
                    {mapping.canonical_field && (
                      <p className="text-sm text-gray-600 mt-1">
                        → {mapping.canonical_field}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Empty state */}
      {!schema && !isExtracting && (
        <div className="card text-center py-12">
          <p className="text-gray-600 mb-4">
            Enter a URL above to extract form schema
          </p>
        </div>
      )}
      </div>
    </div>
  );
}

