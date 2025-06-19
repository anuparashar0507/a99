import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  PlusIcon,
  Search,
  Eye,
  Loader2,
  Copy,
  Pencil,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
// Added topicService.deleteTopic
import { topicService, ApiTopic } from "@/services/topicService";
import { useToast } from "@/components/ui/use-toast";
import CreateTopicDialog from "./CreateTopicDialog";
import EditTopicDialog from "@/components/topic/EditTopicDialog";
import ConfirmDeleteDialog from "@/components/topic/ConfirmDeleteDialog"; // Import confirmation dialog
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui/tooltip";

const TopicPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingTopic, setEditingTopic] = useState<ApiTopic | null>(null);
  const [topics, setTopics] = useState<ApiTopic[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();
  const navigate = useNavigate();

  // --- State for Delete Confirmation ---
  const [isConfirmDeleteDialogOpen, setIsConfirmDeleteDialogOpen] =
    useState(false);
  const [topicToDelete, setTopicToDelete] = useState<ApiTopic | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  // --- End Delete State ---

  useEffect(() => {
    fetchTopics();
  }, []);

  const fetchTopics = async () => {
    console.log("Fetching topics...");
    try {
      setIsLoading(true);
      setError(null);
      const data = await topicService.getTopics();
      setTopics(data);
      console.log("Fetched topics:", data);
    } catch (err) {
      const errorMsg = "Failed to fetch topics. Please try again.";
      setError(errorMsg);
      console.error("Error fetching topics:", err);
      toast({ title: "Error", description: errorMsg, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const filteredTopics = topics.filter(
    (topic) =>
      topic.topic.toLowerCase().includes(searchQuery.toLowerCase()) ||
      topic.context.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const openCreateModal = () => setIsCreateModalOpen(true);

  const handleEditClick = (topic: ApiTopic, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setEditingTopic(topic);
    setIsEditModalOpen(true);
  };

  // --- Delete Handlers ---
  const handleDeleteClick = (topic: ApiTopic, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setTopicToDelete(topic);
    setIsConfirmDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!topicToDelete) return;

    setIsDeleting(true);
    try {
      await topicService.deleteTopic(topicToDelete._id);
      toast({
        title: "Success",
        description: `Topic "${topicToDelete.topic}" deleted successfully.`,
      });
      fetchTopics(); // Refetch the list after deletion
      setIsConfirmDeleteDialogOpen(false); // Close dialog on success
      setTopicToDelete(null);
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || err.message || "Failed to delete topic.";
      console.error(`Error deleting topic ${topicToDelete._id}:`, err);
      toast({
        title: "Error",
        description: errorMsg,
        variant: "destructive",
      });
      // Keep dialog open on error? Or close? Closing for simplicity.
      setIsConfirmDeleteDialogOpen(false);
      setTopicToDelete(null);
    } finally {
      setIsDeleting(false);
    }
  };
  // --- End Delete Handlers ---

  const handleViewTopic = (topicId: string) => {
    console.log(`Navigating to topic: ${topicId}`);
    navigate(`/topic/${topicId}`);
  };

  const handleEditSuccess = () => {
    console.log("Edit successful, refetching topics...");
    fetchTopics();
    setIsEditModalOpen(false);
  };

  const toLocaleDate = (createdAt: string) => {
    if (!createdAt) return "-";

    try {
      // Fix microseconds to milliseconds (keep only 3 digits after decimal)
      const normalizedDateStr = createdAt.includes(".")
        ? createdAt.replace(/\.(\d{3})\d*/, ".$1") + "Z"
        : createdAt + "Z";

      const date = new Date(normalizedDateStr);

      const formatter = new Intl.DateTimeFormat("en-US", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      });

      return formatter.format(date);
    } catch {
      return createdAt;
    }
  };

  return (
    <TooltipProvider>
      <div className="h-full flex flex-col">
        <header className="border-b p-4 md:p-5 flex justify-between items-center">
          {/* ... Header content ... */}
          <div>
            <h1 className="text-2xl font-semibold">Topics</h1>
          </div>
          <Button
            onClick={openCreateModal}
            className="bg-purple-600 hover:bg-purple-700"
            size="sm"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create New Topic
          </Button>
        </header>

        <div className="p-4 md:p-6 flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">
                Loading topics...
              </span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <p className="text-destructive mb-4">{error}</p>
              <Button onClick={fetchTopics} variant="outline">
                Retry Fetch
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                {/* ... Search Input ... */}
                <div className="relative w-full max-w-sm">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    className="pl-10"
                    placeholder="Search topics..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>

              {filteredTopics.length > 0 ? (
                <div className="bg-card rounded-lg border overflow-hidden">
                  <table className="w-full text-sm">
                    {/* ... Table Header ... */}
                    <thead className="bg-muted/50">
                      <tr className="border-b">
                        <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                          Topic Name
                        </th>
                        <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                          Context
                        </th>
                        <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                          Creation Date
                        </th>
                        <th className="px-4 py-3 text-right font-medium text-muted-foreground w-[150px]">
                          Actions
                        </th>{" "}
                        {/* Increased width slightly for 3 icons */}
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTopics.map((topic) => (
                        <tr
                          key={topic._id}
                          className="border-b hover:bg-muted/50 cursor-pointer"
                          onClick={() => handleViewTopic(topic._id)}
                        >
                          {/* ... Table Cells for data ... */}
                          <td className="px-4 py-3 font-medium">
                            {topic.topic}
                          </td>
                          <td
                            className="px-4 py-3 text-muted-foreground max-w-md truncate"
                            title={topic.context}
                          >
                            {topic.context}
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {topic.created_at
                              ? toLocaleDate(topic.created_at)
                              : "-"}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {/* Action Buttons */}
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8 text-muted-foreground hover:text-primary"
                                  onClick={(e) => handleEditClick(topic, e)}
                                >
                                  <Pencil className="h-4 w-4" />
                                  <span className="sr-only">Edit Topic</span>
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Edit Topic</TooltipContent>
                            </Tooltip>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8 text-muted-foreground hover:text-primary"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleViewTopic(topic._id);
                                  }}
                                >
                                  <Eye className="h-4 w-4" />
                                  <span className="sr-only">
                                    View Topic Details
                                  </span>
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                View Topic Details
                              </TooltipContent>
                            </Tooltip>
                            {/* --- Delete Button --- */}
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8 text-destructive/70 hover:text-destructive hover:bg-destructive/10" // Destructive styling
                                  onClick={(e) => handleDeleteClick(topic, e)}
                                >
                                  <Trash2 className="h-4 w-4" />
                                  <span className="sr-only">Delete Topic</span>
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Delete Topic</TooltipContent>
                            </Tooltip>
                            {/* --- End Delete Button --- */}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-10 text-muted-foreground">
                  No topics found matching your search criteria.
                </div>
              )}
            </div>
          )}
          {/* Display "No Topics" message only if not loading, no error, and topics array is empty */}
          {!isLoading && !error && topics.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              {/* ... No topics SVG and text ... */}
              <div className="mb-5">
                <img
                  src="/nocampaigns.svg"
                  alt="No Topics"
                  className="w-60 h-60 object-contain"
                />
              </div>
              <h2 className="text-2xl font-semibold mb-2">
                No Topics here yet!
              </h2>
              <p className="text-muted-foreground mb-6">
                Create a new topic to get started.
              </p>
              <div className="space-y-2">
                <Button
                  onClick={openCreateModal}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Create new
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Dialogs */}
        <CreateTopicDialog
          open={isCreateModalOpen}
          onOpenChange={setIsCreateModalOpen}
          onSuccess={fetchTopics}
        />
        {editingTopic && (
          <EditTopicDialog
            open={isEditModalOpen}
            onOpenChange={setIsEditModalOpen}
            topic={editingTopic}
            onSuccess={handleEditSuccess}
          />
        )}
        <ConfirmDeleteDialog
          open={isConfirmDeleteDialogOpen}
          onOpenChange={setIsConfirmDeleteDialogOpen}
          onConfirm={handleConfirmDelete}
          title="Delete Topic?"
          description={`Are you sure you want to delete the topic "${topicToDelete?.topic}"? This action cannot be undone.`}
          isDeleting={isDeleting}
        />
      </div>
    </TooltipProvider>
  );
};

export default TopicPage;
