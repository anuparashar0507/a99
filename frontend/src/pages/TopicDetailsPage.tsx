import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Link,
  Outlet,
  useParams,
  useNavigate,
  useLocation,
} from "react-router-dom";
import { ChevronLeft, PlusIcon, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import TopicTabs from "@/components/topic/TopicTabs";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { topicService, ApiTopic } from "@/services/topicService";
// import { campaignSettingsService, CampaignSettings } from '@/services/campaignSettingsService';
import CreateTopicDialog from "@/pages/CreateTopicDialog";
import { useToast } from "@/components/ui/use-toast";

const TopicDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [topic, setTopic] = useState<ApiTopic | null>(null);
  const [settings, setSettings] = useState<null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Use a ref to track if data has been loaded
  const dataLoadedRef = useRef(false);

  // Function to update settings and topic data after a save operation
  const updateSettings = useCallback(async () => {
    if (!id) return;

    try {
      // Fetch updated settings
      const updatedSettings = null;
      setSettings(updatedSettings);
      console.log("Settings updated after save:", updatedSettings);

      // Also update the topic data to reflect changes like is_active status
      const topics = await topicService.getTopics();
      const updatedTopic = topics.find((top) => top._id === id);

      if (updatedTopic) {
        setTopic(updatedTopic);
        console.log("Topic data updated after settings change:", updatedTopic);
      }
    } catch (error) {
      console.error("Error updating data after save:", error);
    }
  }, [id]);

  const fetchTopics = async () => {
    navigate(`/topic`);
  };

  const openCreateModal = () => setIsCreateModalOpen(true);

  useEffect(() => {
    // Only fetch data if it hasn't been loaded yet or if the ID changes
    if (!dataLoadedRef.current || !topic) {
      const fetchTopicData = async () => {
        if (!id) {
          navigate("/topic");
          return;
        }

        try {
          setIsLoading(true);
          setError(null);

          // Fetch topic details
          const topics = await topicService.getTopics();
          const topicData = topics.find((top) => top._id === id);

          if (!topicData) {
            setError("Topic not found");
            navigate("/topic");
            return;
          }

          setTopic(topicData);

          // Fetch topic settings
          try {
            // const settingsData = await campaignSettingsService.getSettingsByCampaignId(id);
            // setSettings(settingsData);
            // console.log('Campaign settings loaded:', settingsData);

            // Mark data as loaded
            dataLoadedRef.current = true;
          } catch (settingsError) {
            console.error("Error fetching topic settings:", settingsError);
            toast({
              title: "Warning",
              description:
                "Could not load topic settings. Some features may be limited.",
              variant: "destructive",
            });
          }
        } catch (err) {
          console.error("Error fetching topic data:", err);
          setError("Failed to load topic data. Please try again.");
          toast({
            title: "Error",
            description: "Failed to load topic data",
            variant: "destructive",
          });
        } finally {
          setIsLoading(false);
        }
      };

      fetchTopicData();
    }
  }, [id, navigate, toast, topic]);

  // Reset the dataLoaded ref when the ID changes
  useEffect(() => {
    return () => {
      dataLoadedRef.current = false;
    };
  }, [id]);

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
        <span className="ml-2 text-gray-500">Loading topic details...</span>
      </div>
    );
  }

  if (error || !topic) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <p className="text-red-500 mb-4">{error || "Topic not found"}</p>
        <Button onClick={() => navigate("/topic")} variant="outline">
          Return to Topics
        </Button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <header className="border-b bg-white">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center">
            <Link
              to="/topic"
              className="mr-2 text-gray-500 hover:text-gray-700"
            >
              <ChevronLeft className="h-5 w-5" />
            </Link>
            <h1 className="text-2xl font-semibold">
              {topic.topic}
              {/*<Badge
                      className={cn(
                        "ml-3 rounded-full px-2 py-0.5 text-xs font-medium",
                        topic.is_active
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      )}
                    >
                       {topic.is_active ? 'Active' : 'Inactive'}
                    </Badge>*/}
            </h1>
          </div>
          <Button
            onClick={openCreateModal}
            className="bg-purple-600 hover:bg-purple-700"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create New
          </Button>
        </div>
        <TopicTabs topicId={topic._id} isActive={true} />
      </header>

      <div className="flex-1 overflow-auto">
        <Outlet
          context={{
            topic,
            settings,
            updateSettings,
            isActive: topic.is_active,
          }}
        />
      </div>
      <CreateTopicDialog
        open={isCreateModalOpen}
        onOpenChange={setIsCreateModalOpen}
        onSuccess={fetchTopics}
      />
    </div>
  );
};

export default TopicDetailsPage;
