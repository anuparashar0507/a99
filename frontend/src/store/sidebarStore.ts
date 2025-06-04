import { create } from 'zustand';

interface SidebarState {
   isExpanded: boolean;
   toggleSidebar: () => void;
   setExpanded: (expanded: boolean) => void;
}

export const useSidebarStore = create<SidebarState>((set) => ({
   isExpanded: true,
   toggleSidebar: () => set((state) => ({ isExpanded: !state.isExpanded })),
   setExpanded: (expanded) => set({ isExpanded: expanded }),
}));