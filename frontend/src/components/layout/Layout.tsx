import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useSidebarStore } from '@/store/sidebarStore.ts';
import { cn } from '@/lib/utils.ts';

const Layout: React.FC = () => {
   const { isExpanded } = useSidebarStore();

   return (
     <div className="flex h-screen w-full overflow-hidden">
        <Sidebar />
        <main className={cn(
          "flex-1 overflow-auto transition-all duration-300",
          isExpanded ? "w-[calc(100%-220px)]" : "w-[calc(100%-60px)]"
        )}>
           <Outlet />
        </main>
     </div>
   );
};

export default Layout;