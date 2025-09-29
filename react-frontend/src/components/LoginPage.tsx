import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LogIn, Shield, CheckCircle, FileText, BarChart3 } from 'lucide-react';
import GSTLogo from './GSTLogo';

export default function LoginPage() {
  const { loginWithRedirect, isLoading } = useAuth();

  const features = [
    {
      icon: FileText,
      title: 'File Processing',
      description: 'Upload and process GSTR2B and Tally files seamlessly',
    },
    {
      icon: BarChart3,
      title: 'Smart Analytics',
      description: 'Get detailed insights and financial metrics instantly',
    },
    {
      icon: CheckCircle,
      title: 'Auto Reconciliation',
      description: 'Automated matching with confidence scoring',
    },
    {
      icon: Shield,
      title: 'Secure & Private',
      description: 'Your data is encrypted and securely processed',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        {/* Left Side - Branding and Features */}
        <div className="space-y-8">
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <GSTLogo size="xl" className="drop-shadow-md" />
              <div className="border-l border-gray-300 pl-4">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  GST Reconciliation
                </h1>
                <p className="text-lg text-gray-600">Intelligent tax data reconciliation</p>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-800">Why choose our platform?</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {features.map((feature, index) => {
                const IconComponent = feature.icon;
                return (
                  <div key={index} className="flex items-start space-x-3 p-4 rounded-lg bg-white/50 backdrop-blur-sm border border-gray-200">
                    <div className="p-2 bg-blue-100 rounded-lg flex-shrink-0">
                      <IconComponent className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{feature.title}</h3>
                      <p className="text-sm text-gray-600">{feature.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Side - Login Card */}
        <div className="flex justify-center">
          <Card className="w-full max-w-md shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader className="text-center space-y-2">
              <div className="mx-auto p-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full w-fit">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <CardTitle className="text-2xl font-bold">Welcome Back</CardTitle>
              <CardDescription className="text-gray-600">
                Sign in to access your reconciliation dashboard
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <Button
                  onClick={() => loginWithRedirect()}
                  disabled={isLoading}
                  size="lg"
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Connecting...
                    </>
                  ) : (
                    <>
                      <LogIn className="w-5 h-5 mr-2" />
                      Sign In with Auth0
                    </>
                  )}
                </Button>
              </div>
              
              <div className="text-center">
                <p className="text-xs text-gray-500">
                  Secure authentication powered by Auth0
                </p>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <div className="text-center space-y-2">
                  <p className="text-sm font-medium text-gray-700">New to GST Reconciliation?</p>
                  <p className="text-xs text-gray-500">
                    Your account will be created automatically upon first login
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}