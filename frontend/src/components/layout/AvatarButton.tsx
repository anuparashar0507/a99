import { useNavigate } from "react-router-dom";

import {
   DropdownMenu,
   DropdownMenuContent,
   DropdownMenuItem,
   DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { ChevronsUpDown } from "lucide-react";
import React from "react";

interface UserProps {
   name: string;
   avatar?: string;
   isExpanded: boolean;
   onDropdownOpenChange: (isOpen: boolean) => void
}

const AvatarButton: React.FC<UserProps> = ({name, avatar, isExpanded, onDropdownOpenChange }) => {
   const navigate = useNavigate();
   const { user, logout } = useAuth();

   return (
     <DropdownMenu onOpenChange={onDropdownOpenChange}>
        <DropdownMenuTrigger asChild>
           <div className="flex items-center justify-between bg-white p-5 cursor-pointer rounded-lg">
          <span className="flex items-center space-x-2">
            {avatar ? (
              <img src={avatar} alt={name} className="h-full w-full object-cover" />
            ) : (
              <span className="text-purple-600 font-semibold text-sm">{user?.email.charAt(0)}</span>
            )}
             {isExpanded && <p className="font-semibold text-gray-800 truncate transition-all duration-300 text-sm">{user?.email ?? ""}</p>}
          </span>
              {isExpanded && <ChevronsUpDown className="size-3 opacity-50"/>}
           </div>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-48 p-1 translate-x-56 translate-y-10">
           <DropdownMenuItem
             onClick={logout}
             className="flex items-center space-x-2 py-2 text-red-500 mb-1 focus:text-red-500"
           >
              <LogOut className="size-4"/>
              <span>Sign Out</span>
           </DropdownMenuItem>
        </DropdownMenuContent>
     </DropdownMenu>
   );
}

export default AvatarButton;