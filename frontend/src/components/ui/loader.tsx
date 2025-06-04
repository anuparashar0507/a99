import { cn } from "@/lib/utils";
import React from "react";

interface ILoader {
   size?: number;
   className?: string;
}

const Loader: React.FC<ILoader> = ({ size = 4, className }) => {
   return (
     <div role="status">
        <svg
          width={size}
          height={size}
          viewBox="-7.5 -7.5 75 75"
          version="1.1"
          xmlns="http://www.w3.org/2000/svg"
          className={`animate-spin text-primary`}
        >
           <circle
             r="20"
             cx="30"
             cy="30"
             fill="transparent"
             className="stroke-slate-50"
             strokeWidth="8"
             strokeDasharray="125.60000000000001px"
             strokeDashoffset="0"
           ></circle>
           <circle
             r="20"
             cx="30"
             cy="30"
             className={cn(`stroke-primary`, className)}
             strokeWidth="8"
             strokeLinecap="round"
             strokeDashoffset="100px"
             fill="transparent"
             strokeDasharray="125.60000000000001px"
           ></circle>
        </svg>

        <span className="sr-only">Loading...</span>
     </div>
   );
};

export { Loader };
