import { useToast } from "@/components/ui/use-toast.ts"
import {
   Toast,
   ToastClose,
   ToastDescription,
   ToastProvider,
   ToastTitle,
   ToastViewport,
} from "@/components/ui/toast"
import { CheckCircle2, AlertCircle, Info, X, XCircle } from "lucide-react";

export function Toaster() {
   const {toasts} = useToast();

   // Extracted function to determine the icon based on variant
   const getToastIcon = (variant: string) => {
      switch (variant) {
         case "destructive":
            return <XCircle className="h-5 w-5 text-red-500"/>;
         case "success":
            return <CheckCircle2 className="h-5 w-5 text-green-500"/>;
         case "warning":
            return <AlertCircle className="h-5 w-5 text-yellow-500"/>;
         default:
            return <Info className="h-5 w-5 text-blue-500"/>;
      }
   };

   // Extracted function to manage toast's className logic
   const getToastClassName = (variant: string) =>
     `group relative flex items-start gap-1 p-4 shadow-lg transition-all ${
       variant === "destructive" ? "bg-red-50 border-red-200" : "bg-white border-gray-200"
     } ${variant === "success" ? "border-green-200" : ""} border rounded-lg`;

   return (
     <ToastProvider duration={4000}>
        {toasts.map(({id, title, description, action, variant, ...props}) => (
          <Toast key={id} {...props} className={getToastClassName(variant)}>
             <div className="mt-0.5">{getToastIcon(variant)}</div>
             <div className="grid gap-1 flex-1">
                {title && (
                  <ToastTitle className={`font-medium ${variant === "destructive" ? "text-red-800" : "text-gray-900"}`}>
                     {title}
                  </ToastTitle>
                )}
                {description && (
                  <ToastDescription className={`${variant === "destructive" ? "text-red-600" : "text-gray-600"}`}>
                     {description}
                  </ToastDescription>
                )}
             </div>
             {action}
             <ToastClose
               className="absolute top-2 right-2 p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-gray-100">
                <X className="h-4 w-4 text-gray-500"/>
             </ToastClose>
          </Toast>
        ))}
        <ToastViewport
          style={{
             position: 'fixed',
             top: 0,
             right: 0,
             padding: '16px',
             display: 'flex',
             flexDirection: 'column',
             gap: '8px',
             width: '360px',
             maxWidth: '100vw',
             zIndex: 2147483647,
             margin: 0,
             listStyle: 'none',
          }}
        />
     </ToastProvider>
   );
}