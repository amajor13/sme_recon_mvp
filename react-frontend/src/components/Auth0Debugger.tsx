import { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export default function Auth0Debugger() {
  const { 
    isLoading, 
    isAuthenticated, 
    error, 
    user, 
    getAccessTokenSilently, 
    loginWithRedirect,
    logout
  } = useAuth0();
  const [token, setToken] = useState<string | null>(null);
  const [configTestResult, setConfigTestResult] = useState<{status?: number, error?: string}>({});
  const [expanded, setExpanded] = useState(false);

  const fetchToken = async () => {
    try {
      const accessToken = await getAccessTokenSilently();
      setToken(accessToken);
    } catch (e: any) {
      console.error('Error getting token:', e);
      setToken(`Error: ${e.message}`);
    }
  };

  const testAuth0Config = async () => {
    try {
      // Get Auth0 domain from the page
      const domain = (document.querySelector('meta[name="auth0-domain"]')?.getAttribute('content') || 
                     import.meta.env.VITE_AUTH0_DOMAIN || 
                     'Unknown');
      
      // Test if the OIDC configuration endpoint is reachable
      const response = await fetch(`https://${domain}/.well-known/openid-configuration`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      
      setConfigTestResult({
        status: response.status,
        error: response.status !== 200 ? await response.text() : undefined
      });
    } catch (e: any) {
      setConfigTestResult({ error: e.message });
    }
  };

  // Run tests on component mount
  useEffect(() => {
    testAuth0Config();
    // Add domain meta tag for debugging
    const meta = document.createElement('meta');
    meta.name = 'auth0-domain';
    meta.content = import.meta.env.VITE_AUTH0_DOMAIN || 'Unknown';
    document.head.appendChild(meta);
  }, []);

  // If there's an Auth0 error, automatically expand the debugger
  useEffect(() => {
    if (error) {
      setExpanded(true);
    }
  }, [error]);

  return (
    <Card className="mb-4 border-yellow-500 shadow-md bg-yellow-50">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              Auth0 Debugger
              {isAuthenticated ? 
                <Badge variant="outline" className="bg-green-100 text-green-800 border-green-300">Authenticated</Badge> :
                <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-300">Not Authenticated</Badge>
              }
            </CardTitle>
            <CardDescription>
              {isLoading ? 'Loading auth state...' : error ? 
                <span className="text-red-500">Error: {error.message}</span> : 
                `Status: ${isAuthenticated ? 'Logged in' : 'Not logged in'}`}
            </CardDescription>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setExpanded(!expanded)}
            className="text-xs"
          >
            {expanded ? 'Hide Details' : 'Show Details'}
          </Button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0 text-sm">
          <div className="space-y-4">
            <div>
              <h3 className="font-medium mb-1">Configuration</h3>
              <div className="bg-white p-3 rounded border text-xs space-y-1 font-mono">
                <div><span className="text-gray-500">Domain:</span> {import.meta.env.VITE_AUTH0_DOMAIN || 'Not set'}</div>
                <div><span className="text-gray-500">Client ID:</span> {import.meta.env.VITE_AUTH0_CLIENT_ID || 'Not set'}</div>
                <div><span className="text-gray-500">Audience:</span> {import.meta.env.VITE_AUTH0_AUDIENCE || 'Not set'}</div>
                <div><span className="text-gray-500">Redirect URI:</span> {import.meta.env.VITE_AUTH0_REDIRECT_URI || window.location.origin}</div>
                <div>
                  <span className="text-gray-500">OIDC Config Test:</span> {
                    configTestResult.status === 200 ? 
                      <span className="text-green-600">Success</span> : 
                      <span className="text-red-600">
                        Failed {configTestResult.status ? `(${configTestResult.status})` : ''} 
                        {configTestResult.error ? ` - ${configTestResult.error}` : ''}
                      </span>
                  }
                </div>
              </div>
            </div>

            {user && (
              <div>
                <h3 className="font-medium mb-1">User Info</h3>
                <div className="bg-white p-3 rounded border text-xs space-y-1 font-mono">
                  <div><span className="text-gray-500">Email:</span> {user.email}</div>
                  <div><span className="text-gray-500">Name:</span> {user.name}</div>
                  <div><span className="text-gray-500">Sub:</span> {user.sub}</div>
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              {!isAuthenticated && (
                <Button 
                  size="sm"
                  onClick={() => loginWithRedirect()}
                  className="text-xs"
                >
                  Login
                </Button>
              )}
              
              {isAuthenticated && (
                <>
                  <Button 
                    size="sm" 
                    onClick={fetchToken}
                    className="text-xs"
                  >
                    Get Access Token
                  </Button>
                  
                  <Button 
                    variant="destructive" 
                    size="sm"
                    onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                    className="text-xs"
                  >
                    Logout
                  </Button>
                </>
              )}
            </div>

            {token && (
              <div>
                <h3 className="font-medium mb-1">Access Token</h3>
                <div className="bg-white p-3 rounded border text-xs overflow-auto max-h-24">
                  <pre className="whitespace-pre-wrap break-all">{token}</pre>
                </div>
              </div>
            )}

            {error && (
              <div>
                <h3 className="font-medium text-red-600 mb-1">Error Details</h3>
                <div className="bg-red-50 p-3 rounded border border-red-200 text-xs">
                  <div><span className="text-gray-500">Message:</span> {error.message}</div>
                  {error.stack && (
                    <div className="mt-2">
                      <span className="text-gray-500">Stack:</span>
                      <pre className="whitespace-pre-wrap text-xs mt-1 overflow-auto max-h-32">{error.stack}</pre>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}