import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Loader2 } from "lucide-react";

type IPrivateRoute = {
   children?: ReactNode;
};

export const PrivateRoute: React.FC<IPrivateRoute> = ({ children }) => {
   const { isAuthenticated, isLoading, hasJazonAccess } = useAuth();
   const location = useLocation();

   if (isLoading) {
      return (
        <div className="flex flex-col justify-center m-auto text-center items-center h-screen">
           <Loader2 className="text-purple-600 animate-spin h-6 w-6 mb-4" />
           <p className="text-gray-600">Authenticating...</p>
        </div>
      );
   }

   if (!isAuthenticated) {
      // Save the attempted URL for redirect after login
      return <Navigate to="/auth/login" state={{ from: location }} replace />;
   }

   return <>{children}</>;
};