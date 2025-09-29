// Define Auth0 configuration in a separate file for better visibility and maintenance
export const authConfig = {
  domain: "dev-b8bhw7u6rgyyv5rb.us.auth0.com",
  clientId: "oU348HVxTDfMS321Z95F16PpPy4aUpCR",
  audience: "https://sme-reconciliation-api",
  redirectUri: "http://localhost:3002",
  scope: "openid profile email"
};