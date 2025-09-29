import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Auth0Provider } from '@auth0/auth0-react'
import App from './App.tsx'
import './index.css'
import { authConfig } from './auth0-config'

// Resolve Auth0 settings with env overrides; keep redirectUri dynamic for localhost/LAN
const domain: string = import.meta.env.VITE_AUTH0_DOMAIN || authConfig.domain
const clientId: string = import.meta.env.VITE_AUTH0_CLIENT_ID || authConfig.clientId
const audience: string = import.meta.env.VITE_AUTH0_AUDIENCE || authConfig.audience
// Normalize with a trailing slash to avoid callback mismatch when Auth0 entry includes '/'
const redirectUri: string = `${window.location.origin}/`

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