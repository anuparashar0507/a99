import { useState } from "react";

import "react-quill/dist/quill.snow.css";
import MarkdownDisplay from "@/components/content_desk/MarkdownDisplay.tsx";

interface Props {
  value: string;
  onChange: (markdown: string) => void;
}

const Editor: React.FC<Props> = ({ value, onChange }) => {
  const [activeTab, setActiveTab] = useState<"edit" | "preview">("edit");

  return (
    <div className="w-full mx-auto bg-muted/50 rounded-2xl shadow-lg border border-border">
      <div className="flex items-center border-b border-border px-4 pt-2">
        <button
          onClick={() => setActiveTab("edit")}
          className={`px-4 py-2 text-sm font-medium transition-colors duration-200 rounded-t-md ${
            activeTab === "edit"
              ? "bg-background text-primary border-b-2 border-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          ✏️ Edit
        </button>
        <button
          onClick={() => setActiveTab("preview")}
          className={`ml-2 px-4 py-2 text-sm font-medium transition-colors duration-200 rounded-t-md ${
            activeTab === "preview"
              ? "bg-background text-primary border-b-2 border-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          👁️ Preview
        </button>
      </div>

      <div className="px-6 py-4">
        {activeTab === "edit" ? (
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Start writing markdown..."
            className="w-full h-[28rem] p-4 bg-background border border-border rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary text-foreground placeholder:text-muted-foreground"
          />
        ) : (
          <div className="prose dark:prose-invert max-w-none">
            <MarkdownDisplay content={value}/>
          </div>
        )}
      </div>
    </div>

  );
};

export default Editor;