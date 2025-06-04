import { useState, useEffect } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import MarkdownDisplay from "@/components/content_desk/MarkdownDisplay";
import JsonDisplay from "@/components/content_desk/JsonDisplay";
import { ScrollArea } from "@/components/ui/scroll-area";
import { showErrorToast, showSuccessToast } from "@/components/ui/toast.tsx";
import { Loader2, CircleCheck } from "lucide-react";
import { deskService, GenerationPhase } from "@/services/deskService";
interface DeskPhaseProps {
  phase: string;
  data: string;
  currentFeedback: string;
  onSaveFeedback: any;
  status: GenerationPhase;
  handleRun: any;
  addContentForReview?: any;
  isAddingContent?: boolean;
}

export default function DeskPhase<DeskPhaseProps>({
  phase,
  data,
  currentFeedback,
  onSaveFeedback,
  status,
  handleRun,
  addContentForReview,
  isAddingContent,
}) {
  const [feedback, setFeedback] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    console.log("here");
    setIsSaving(true);
    console.debug(`Saving feedback for ${phase}:`, feedback);
    try {
      await onSaveFeedback(feedback);
      showSuccessToast(`${phase} feedback saved.`);
    } catch (error) {
      console.error(`Error saving feedback for ${phase}:`, error);
      showErrorToast(`Failed to save ${phase} feedback.`); // Provide feedback on error
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    setFeedback(currentFeedback || "");
  }, [currentFeedback]);

  const myStatus = phase.toLowerCase() === status.phase;
  const isRunning = myStatus && status.status_text === "processing";
  const completedRun = myStatus && status.status_text === "success";
  return (
    <>
      <div className="flex justify-between items-center w-full">
        <span className="text-lg font-semibold no-underline">{phase}</span>
        <Button
          size="sm"
          className="mr-2"
          variant="outline"
          disabled={isRunning}
          onClick={(e) => {
            e.stopPropagation();
            handleRun();
          }}
        >
          {isRunning ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          {completedRun ? <CircleCheck className="mr-2 h-4 w-4" /> : null}
          Run
        </Button>
      </div>
      <div className="p-6 space-y-4">
        <ScrollArea className="h-[300px] w-full border rounded-md p-4">
          {data ? (
            phase === "Ideation" ? (
              <JsonDisplay jsonString={data} />
            ) : (
              <MarkdownDisplay content={data} />
            )
          ) : (
            <p className="w-full text-center">{`Press the Run button to generate content for the ${phase} phase.`}</p>
          )}
        </ScrollArea>
        <div className="space-y-2">
          <Textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder={`Provide feedback for ${phase}... (optional)`}
            rows={3}
            className="mt-2"
          />
          <div className="flex justify-end">
            {addContentForReview && completedRun ? (
              <Button
                size="sm"
                className="bg-purple-600 hover:bg-purple-700 mr-3"
                onClick={addContentForReview}
                disabled={isSaving || isAddingContent}
              >
                {isAddingContent ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                Add Content For Review
              </Button>
            ) : null}
            <Button
              size="sm"
              className="bg-purple-600 hover:bg-purple-700"
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Save Feedback
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
