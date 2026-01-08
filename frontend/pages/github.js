/**
 * GitHub integration page.
 */

import { useState, useEffect } from 'react';
import { linkGitHub, getGitHubRepos, selectGitHubRepos, getSelectedRepos, unlinkGitHub } from '../lib/api';

export default function GitHubPage() {
  const [isLinked, setIsLinked] = useState(false);
  const [githubUsername, setGithubUsername] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [isLinking, setIsLinking] = useState(false);
  const [repos, setRepos] = useState([]);
  const [selectedRepos, setSelectedRepos] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showTokenInput, setShowTokenInput] = useState(false);
  
  useEffect(() => {
    checkConnection();
    loadSelectedRepos();
  }, []);
  
  const checkConnection = async () => {
    try {
      // Try to fetch repos - if successful, account is linked
      const reposData = await getGitHubRepos();
      setIsLinked(true);
      setRepos(reposData);
    } catch (err) {
      setIsLinked(false);
    }
  };
  
  const loadSelectedRepos = async () => {
    try {
      const selected = await getSelectedRepos();
      setSelectedRepos(selected.map(r => r.repo_id));
    } catch (err) {
      console.error('Failed to load selected repos:', err);
    }
  };
  
  const handleLinkGitHub = async (e) => {
    e.preventDefault();
    
    if (!accessToken.trim()) {
      setError('Please enter a GitHub access token');
      return;
    }
    
    setIsLinking(true);
    setError(null);
    
    try {
      const response = await linkGitHub(accessToken);
      if (response.success) {
        setIsLinked(true);
        setGithubUsername(response.github_username);
        setAccessToken('');
        setShowTokenInput(false);
        // Load repos
        await loadRepos();
      }
    } catch (err) {
      setError(err.message || 'Failed to link GitHub account');
    } finally {
      setIsLinking(false);
    }
  };
  
  const loadRepos = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const reposData = await getGitHubRepos();
      setRepos(reposData);
      // Update selected repos
      await loadSelectedRepos();
    } catch (err) {
      setError(err.message || 'Failed to load repositories');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSelectRepos = async (repoIds) => {
    try {
      await selectGitHubRepos(repoIds);
      setSelectedRepos(repoIds);
    } catch (err) {
      setError(err.message || 'Failed to select repositories');
    }
  };
  
  const handleUnlink = async () => {
    if (!confirm('Are you sure you want to unlink your GitHub account?')) {
      return;
    }
    
    try {
      await unlinkGitHub();
      setIsLinked(false);
      setRepos([]);
      setSelectedRepos([]);
      setGithubUsername('');
    } catch (err) {
      setError(err.message || 'Failed to unlink GitHub account');
    }
  };
  
  const toggleRepoSelection = (repoId) => {
    const newSelected = selectedRepos.includes(repoId)
      ? selectedRepos.filter(id => id !== repoId)
      : [...selectedRepos, repoId];
    
    handleSelectRepos(newSelected);
  };
  
  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold mb-6">GitHub Integration</h1>
      
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}
      
      {/* Link GitHub Section */}
      {!isLinked ? (
        <div className="card mb-6">
          <h2 className="text-xl font-semibold mb-4">Link GitHub Account</h2>
          <p className="text-gray-600 mb-4">
            Connect your GitHub account to import repositories as projects. We only request read-only access.
          </p>
          
          {!showTokenInput ? (
            <div>
              <button
                onClick={() => setShowTokenInput(true)}
                className="btn-primary"
              >
                Link GitHub Account
              </button>
              <p className="text-sm text-gray-500 mt-4">
                You'll need a GitHub Personal Access Token with <code className="bg-gray-100 px-1 rounded">public_repo</code> and <code className="bg-gray-100 px-1 rounded">read:user</code> scopes.
              </p>
            </div>
          ) : (
            <form onSubmit={handleLinkGitHub} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  GitHub Personal Access Token
                </label>
                <input
                  type="password"
                  value={accessToken}
                  onChange={(e) => setAccessToken(e.target.value)}
                  placeholder="ghp_xxxxxxxxxxxx"
                  className="input-field w-full"
                  disabled={isLinking}
                />
                <p className="text-xs text-gray-500 mt-2">
                  Create a token at{' '}
                  <a
                    href="https://github.com/settings/tokens"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:underline"
                  >
                    github.com/settings/tokens
                  </a>
                  {' '}with <code className="bg-gray-100 px-1 rounded">public_repo</code> and <code className="bg-gray-100 px-1 rounded">read:user</code> scopes.
                </p>
              </div>
              <div className="flex gap-4">
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={isLinking || !accessToken.trim()}
                >
                  {isLinking ? 'Linking...' : 'Link Account'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowTokenInput(false);
                    setAccessToken('');
                  }}
                  className="btn-secondary"
                  disabled={isLinking}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      ) : (
        <div className="card mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold">GitHub Account Linked</h2>
              {githubUsername && (
                <p className="text-sm text-gray-600">@{githubUsername}</p>
              )}
            </div>
            <div className="flex gap-4">
              <button
                onClick={loadRepos}
                className="btn-secondary"
                disabled={isLoading}
              >
                {isLoading ? 'Loading...' : 'Refresh Repos'}
              </button>
              <button
                onClick={handleUnlink}
                className="btn-secondary text-red-600 hover:text-red-700"
              >
                Unlink Account
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Repositories List */}
      {isLinked && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">
            Your Repositories ({repos.length})
          </h2>
          
          {repos.length === 0 ? (
            <p className="text-gray-600">No repositories found. Click "Refresh Repos" to load them.</p>
          ) : (
            <div className="space-y-4">
              {repos.map((repo) => (
                <div
                  key={repo.repo_id}
                  className={`border rounded-lg p-4 transition-colors ${
                    selectedRepos.includes(repo.repo_id)
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-lg">
                          <a
                            href={repo.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 hover:underline"
                          >
                            {repo.full_name}
                          </a>
                        </h3>
                        {repo.language && (
                          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                            {repo.language}
                          </span>
                        )}
                        <span className="text-xs text-gray-500">
                          ⭐ {repo.stars_count} | 🍴 {repo.forks_count}
                        </span>
                      </div>
                      
                      {repo.description && (
                        <p className="text-sm text-gray-600 mb-2">{repo.description}</p>
                      )}
                      
                      {repo.readme_summary && (
                        <div className="mt-3 p-3 bg-gray-50 rounded border border-gray-200">
                          <p className="text-xs font-medium text-gray-700 mb-1">README Summary:</p>
                          <p className="text-xs text-gray-600 line-clamp-3">
                            {repo.readme_summary}
                          </p>
                          {repo.readme_url && (
                            <a
                              href={repo.readme_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-primary-600 hover:underline mt-1 inline-block"
                            >
                              View full README →
                            </a>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <label className="flex items-center ml-4 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedRepos.includes(repo.repo_id)}
                        onChange={() => toggleRepoSelection(repo.repo_id)}
                        className="w-5 h-5 text-primary-600 rounded focus:ring-primary-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Select</span>
                    </label>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {selectedRepos.length > 0 && (
            <div className="mt-6 p-4 bg-primary-50 border border-primary-200 rounded-lg">
              <p className="text-sm font-medium text-primary-800">
                {selectedRepos.length} repository{selectedRepos.length !== 1 ? 'ies' : 'y'} selected as projects
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

