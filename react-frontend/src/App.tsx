import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './components/Dashboard';
import { Toaster } from '@/components/ui/toaster';

// Import the Auth0Debugger component
import Auth0Debugger from './components/Auth0Debugger';

function App() {
  return (
    <AuthProvider>
      {/* Auth0 Debug Panel */}
      <div className="fixed top-2 right-2 left-2 z-50 max-w-2xl mx-auto">
        <Auth0Debugger />
      </div>
      
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
      <Toaster />
    </AuthProvider>
  );
}

export default App;