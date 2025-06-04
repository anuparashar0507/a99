import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/use-toast";
import {
  topicService,
  ApiTopic,
  UpdateTopicRequest,
} from "@/services/topicService"; // Adjust path
import { Loader2 } from "lucide-react";

interface EditTopicDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  topic: ApiTopic | null; // Topic to edit
  onSuccess: () => void; // Callback on successful update
}

const EditTopicDialog: React.FC<EditTopicDialogProps> = ({
  open,
  onOpenChange,
  topic,
  onSuccess,
}) => {
  const [editedTopicName, setEditedTopicName] = useState("");
  const [editedContext, setEditedContext] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  // Initialize form when topic data is available or modal opens
  useEffect(() => {
    if (topic && open) {
      setEditedTopicName(topic.topic || "");
      setEditedContext(topic.context || "");
      setError(null); // Reset error on open/topic change
    }
    // Reset saving state when dialog closes
    if (!open) {
      setIsSaving(false);
      setError(null);
    }
  }, [topic, open]);

  const handleSaveChanges = async () => {
    if (!topic) return;

    // Basic validation (can add more checks)
    if (!editedTopicName.trim() || editedTopicName.length < 3) {
      setError("Topic name must be at least 3 characters.");
      return;
    }
    if (!editedContext.trim() || editedContext.length < 10) {
      setError("Context must be at least 10 characters.");
      return;
    }

    setIsSaving(true);
    setError(null);

    // Prepare only changed data
    const updateData: UpdateTopicRequest = {};
    if (editedTopicName !== topic.topic) {
      updateData.topic = editedTopicName;
    }
    if (editedContext !== topic.context) {
      updateData.context = editedContext;
    }

    if (Object.keys(updateData).length === 0) {
      toast({
        title: "No changes detected",
        description: "No fields were modified.",
      });
      setIsSaving(false);
      onOpenChange(false); // Close if no changes
      return;
    }

    try {
      await topicService.updateTopic(topic._id, updateData);
      toast({
        title: "Success",
        description: "Topic updated successfully.",
      });
      onSuccess(); // Trigger refetch in parent
      onOpenChange(false); // Close dialog
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || err.message || "Failed to update topic.";
      console.error("Error updating topic:", err);
      setError(errorMsg); // Display API error
      toast({
        title: "Error",
        description: errorMsg,
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Edit Topic</DialogTitle>
          <DialogDescription>
            Update the name and context for topic:{" "}
            <span className="font-medium">{topic?.topic}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="p-1 overflow-y-auto space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="topic-name" className="text-sm font-medium">
              Topic
            </Label>
            <Input
              id="topic-name"
              value={editedTopicName}
              onChange={(e) => setEditedTopicName(e.target.value)}
              placeholder="Enter the updated topic name"
              disabled={isSaving}
              aria-describedby="topic-error" // Link error message if using aria
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="topic-context" className="text-sm font-medium">
              Context
            </Label>
            <Textarea
              id="topic-context"
              value={editedContext}
              onChange={(e) => setEditedContext(e.target.value)}
              placeholder="Enter the updated context or description..."
              rows={6} // Adjust rows
              className="resize-y min-h-[100px]" // Allow vertical resize, set min height
              disabled={isSaving}
              aria-describedby="context-error"
            />
          </div>

          {error && (
            <p className="text-sm font-medium text-destructive text-center pt-1">
              {error}
            </p>
          )}
        </div>

        <DialogFooter className="pt-4 sm:justify-between">
          <DialogClose asChild>
            <Button type="button" variant="outline" disabled={isSaving}>
              Cancel
            </Button>
          </DialogClose>
          <Button className="bg-purple-600 hover:bg-purple-700" type="button" onClick={handleSaveChanges} disabled={isSaving}>
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default EditTopicDialog;
