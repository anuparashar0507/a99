import { IAgentProject } from "@/lib/types";
import { createContext, useContext } from "react";

export const ProjectContext = createContext<{
   project?: Partial<IAgentProject>;
   getProject?: () => void;
   setProject?: (input: Partial<IAgentProject>) => void;
   updateProject?: (input: any) => void;
   isUpdatingProject?: boolean;
   changeTab?: (id: number) => void;
}>({
   project: {},
});

export const useProject = () => useContext(ProjectContext);
