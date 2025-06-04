import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { topicService, CreateTopicRequest } from "@/services/topicService";

interface CreateTopicDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

const CreateTopicDialog: React.FC<CreateTopicDialogProps> = ({
  open,
  onOpenChange,
  onSuccess,
}) => {
  const [newTopicName, setNewTopicName] = useState("");
  const [topicDescription, setTopicDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const closeModal = () => {
    setNewTopicName("");
    setTopicDescription("");
    onOpenChange(false);
  };

  const handleCreateTopic = async () => {
    if (!newTopicName.trim()) {
      toast({
        title: "Error",
        description: "Please enter a topic name",
        variant: "destructive",
      });
      return;
    }

    const topicData: CreateTopicRequest = {
      topic: newTopicName,
      context: topicDescription,
    };

    try {
      setIsSubmitting(true);
      await topicService.createTopic(topicData);
      toast({
        title: "Success",
        description: "Topic created successfully",
      });
      closeModal();
      onSuccess(); // Tell parent to refresh topics
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to create topic",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex flex-col max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Create New Topic</DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto space-y-4 py-4">
          <div className="space-y-2 p-1">
            <Label htmlFor="name">Topic</Label>
            <Input
              id="name"
              value={newTopicName}
              onChange={(e) => setNewTopicName(e.target.value)}
              placeholder="Enter your main keyword"
            />
          </div>
          <div className="space-y-2 p-1">
            <Label htmlFor="name">Context</Label>
            <Textarea
              value={topicDescription}
              onChange={(e) => setTopicDescription(e.target.value)}
              placeholder="Enter more context around your topic"
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={closeModal}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreateTopic}
            className="bg-purple-600 hover:bg-purple-700"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              "Create"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CreateTopicDialog;
