import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Auth0Provider } from '@auth0/auth0-react'
import App from './App.tsx'
import './index.css'
// Import for debugging
import * as auth0 from '@auth0/auth0-react'

// Use correct domain name with explicit typing for Auth0
const domain: string = "dev-b8bhw7u6rgyyv5rb.us.auth0.com";
const clientId: string = import.meta.env.VITE_AUTH0_CLIENT_ID || "oU348HVxTDfMS321Z95Fl6PpPy4aUpCR";
const audience: string = import.meta.env.VITE_AUTH0_AUDIENCE || "https://sme-reconciliation-api";
// Use the current window location for redirect to support different dev ports
const redirectUri: string = window.location.origin;

if (!domain || !clientId) {
  // eslint-disable-next-line no-console
  console.warn('Auth0 env vars missing: VITE_AUTH0_DOMAIN or VITE_AUTH0_CLIENT_ID');
}

// Helpful log to verify runtime values during local dev
// eslint-disable-next-line no-console
console.info('[Auth0] init', { domain, audience, redirectUri });

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: redirectUri,
        audience: audience,
        scope: "openid profile email"
      }}
      cacheLocation="localstorage"
      useRefreshTokens={true}
    >
      <App />
    </Auth0Provider>
  </StrictMode>,
)