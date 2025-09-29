import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  user_id: string;
  email: string;
  name: string;
  email_verified: boolean;
}

interface AuthContextType {
  isLoading: boolean;
  isAuthenticated: boolean;
  user?: User;
  loginWithRedirect: () => Promise<void>;
  logout: (options?: { returnTo?: string }) => void;
  getAccessTokenSilently: () => Promise<string>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | undefined>();

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => {
      setIsLoading(false);
      
      // Check if user was previously "logged in" (stored in localStorage)
      const storedAuth = localStorage.getItem('mockAuth');
      if (storedAuth === 'true') {
        setIsAuthenticated(true);
        setUser({
          user_id: 'mock-user-123',
          email: 'demo@example.com',
          name: 'Demo User',
          email_verified: true
        });
      }
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  const loginWithRedirect = async () => {
    setIsLoading(true);
    
    // Simulate login process
    setTimeout(() => {
      setIsAuthenticated(true);
      setUser({
        user_id: 'mock-user-123',
        email: 'demo@example.com',
        name: 'Demo User',
        email_verified: true
      });
      localStorage.setItem('mockAuth', 'true');
      setIsLoading(false);
    }, 1000);
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(undefined);
    localStorage.removeItem('mockAuth');
  };

  const getAccessTokenSilently = async (): Promise<string> => {
    // Return a mock JWT token for development
    return 'mock-jwt-token-for-development';
  };

  const value: AuthContextType = {
    isLoading,
    isAuthenticated,
    user,
    loginWithRedirect,
    logout,
    getAccessTokenSilently
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};