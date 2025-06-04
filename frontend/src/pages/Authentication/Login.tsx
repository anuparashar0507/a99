import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export const Login = () => {
   const { isAuthenticated, isLoading } = useAuth();
   const navigate = useNavigate();
   const location = useLocation();

   useEffect(() => {
      if (!isLoading && isAuthenticated) {
         navigate("/");
      }
   }, [isAuthenticated, isLoading, navigate, location]);

   return (
     <div className="relative mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[400px] bg-white">
        {/* The Lyzr auth modal is triggered by the AuthContext, so we only show a minimal UI or a backdrop here. */}
        <p className="text-center text-gray-600">
           {isLoading ? "Please wait, authenticating..." : "Redirecting..."}
        </p>
     </div>
   );
};