import { useState, useEffect, useCallback } from "react";
import DeskPhase from "@/components/content_desk/DeskPhase";
import DeskDetails from "@/components/content_desk/DeskDetails";
import { useParams } from "react-router-dom";
import {
  showErrorToast,
  showSuccessToast,
  showInfoToast,
} from "@/components/ui/toast.tsx";
import {
  deskService,
  ApiContentDeskDetailResponse,
  GenerationStatus,
  GenerationPhase,
  StatusText,
  UpdateDeskRequest,
  UpdateFeedbackRequest,
  UpdateContentRequest,
  addContentForReview,
} from "@/services/deskService";
import { topicService, ApiTopic } from "@/services/topicService";
import { Skeleton } from "@/components/ui/skeleton";
import { useDeskStatusStream } from "@/hooks/useDeskStatusStream";

type PhaseStatus = "loading" | "completed" | "stale";

export default function ContentDesk() {
  const { id: topicId } = useParams<{ id: string }>();
  const [topicDetails, setTopicDetails] = useState<ApiTopic | null>(null);
  const [deskDetails, setDeskDetails] =
    useState<ApiContentDeskDetailResponse | null>(null);
  const [platforms, setPlatforms] = useState<string[]>([]);
  const [contentTypes, setContentTypes] = useState<string[]>([]);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [isAddingContent, setIsAddingContent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [runStatus, setRunStatus] = useState<GenerationStatus>({
    phase: GenerationPhase.NOT_RUNNING,
    message: "",
    status_text: StatusText.NO_OP,
  });
  const [ideationStatus, setIdeationStatus] = useState<GenerationStatus>({
    phase: GenerationPhase.NOT_RUNNING,
    message: "",
    status_text: StatusText.NO_OP,
  });
  const [outlineStatus, setOutlineStatus] = useState<GenerationStatus>({
    phase: GenerationPhase.NOT_RUNNING,
    message: "",
    status_text: StatusText.NO_OP,
  });
  const [contentStatus, setContentStatus] = useState<GenerationStatus>({
    phase: GenerationPhase.NOT_RUNNING,
    message: "",
    status_text: StatusText.NO_OP,
  });

  const { status, error: runError } = useDeskStatusStream(deskDetails?._id);

  const fetchDeskAndStatus = useCallback(async (deskId: string) => {
    try {
      console.debug(`Workspaceing desk ${deskId} details and status...`);
      const [deskResult, statusResult] = await Promise.allSettled([
        deskService.getDesk(deskId),
        deskService.getDeskStatus(deskId),
      ]);

      let fetchedDesk = null;
      if (deskResult.status === "fulfilled") {
        fetchedDesk = deskResult.value;
        setDeskDetails(fetchedDesk);
      } else {
        console.error("Refetch desk details failed:", deskResult.reason);
        // Don't throw here maybe, just log, status might still update
      }

      if (statusResult.status !== "fulfilled") {
        console.error("Refetch status failed:", statusResult.reason);
      }
      return fetchedDesk; // Return fetched desk or null
    } catch (error) {
      console.error("Error during combined desk/status fetch:", error);
      return null;
    }
  }, []);

  useEffect(() => {
    if (runError) {
      showErrorToast(
        "Something went wrong, Cant get run status. Please refresh the page."
      );
    } else {
      if (status) {
        setRunStatus(status);
        if (status.phase === "ideation") {
          setIdeationStatus(status);
          setContentStatus(status);
        } else if (status.phase === "outline") {
          setOutlineStatus(status);
        } else if (status.phase === "content") {
          if (status.status_text === "success") {
            showSuccessToast("Content successfully generated!");
          }
          setContentStatus(status);
        }
        if (status.status_text === "success") {
          fetchDeskAndStatus(deskDetails?._id).then((res) => console.log(res));
        }
      }
    }
  }, [status, runError, deskDetails?._id, fetchDeskAndStatus]);

  const handleSaveSettings = async (updateData: UpdateDeskRequest) => {
    if (!deskDetails?._id) return;
    console.log(`Saving settings for desk ${deskDetails._id}`);
    setIsSavingSettings(true);
    try {
      // Instead of partial update, just refetch after saving
      await deskService.updateDesk(deskDetails._id, updateData);
      await fetchDeskAndStatus(deskDetails._id); // Refetch data
      showSuccessToast("Desk settings saved.");
    } catch (error: any) {
      const errorMsg =
        error.response?.data?.detail ||
        error.message ||
        "Failed to save settings.";
      console.error(
        `Error saving settings for desk ${deskDetails._id}: ${errorMsg}`,
        error
      );
      showErrorToast(`Failed to save settings: ${errorMsg}`);
    } finally {
      setIsSavingSettings(false);
    }
  };

  const handleAddContentForReview = async () => {
    if (!topicDetails?._id) return;
    console.log(`Adding content for review ${topicDetails._id}`);
    setIsAddingContent(true);
    try {
      await deskService.addContentForReview(topicDetails._id);
      await fetchDeskAndStatus(deskDetails._id); // Refetch data
      showSuccessToast("Added content for review.");
    } catch (error: any) {
      const errorMsg =
        error.response?.data?.detail ||
        error.message ||
        "Failed to add content for review.";
      console.error(
        `Error adding content for review ${topicDetails._id}: ${errorMsg}`,
        error
      );
      showErrorToast(`Failed to add content for review: ${errorMsg}`);
    } finally {
      setIsAddingContent(false);
    }
  };

  const fetchInitialData = useCallback(async () => {
    if (!topicId) return;
    console.log(`Workspaceing initial data for topic ID: ${topicId}`);
    setIsInitialLoading(true); // Use separate initial loading flag
    setError(null);
    try {
      const topicData = await topicService.getTopic(topicId);
      setTopicDetails(topicData);
      console.debug("Fetched topic details:", topicData);

      if (!topicData?.desk_id) {
        throw new Error("Desk ID not found for this topic.");
      }
      const deskId = topicData.desk_id;
      console.log(`Found Desk ID: ${deskId} for Topic ${topicId}`);

      // Fetch Desk Details, Configs, and Status concurrently
      const [deskRes, platformsRes, typesRes] = await Promise.allSettled([
        fetchDeskAndStatus(deskId), // Use combined fetch
        deskService.getPlatforms(),
        deskService.getContentTypes(),
      ]);

      // Only set platforms/types if fetch succeeded and component mounted
      if (platformsRes.status === "fulfilled") setPlatforms(platformsRes.value);
      else console.error("Platforms fetch failed:", platformsRes.reason);

      if (typesRes.status === "fulfilled") setContentTypes(typesRes.value);
      else console.error("Content types fetch failed:", typesRes.reason);
    } catch (err: any) {
      console.error("Error fetching initial data:", err);
      const errorMsg =
        err.response?.data?.detail ||
        err.message ||
        "Failed to load desk data.";
      setError(errorMsg);
      showErrorToast(errorMsg);
    } finally {
      setIsInitialLoading(false);
    }
  }, [topicId, fetchDeskAndStatus]);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  const handleRun = async (
    runFn: () => Promise<any>,
    deskId: string,
    phase: string
  ) => {
    console.log(`Triggering run for phase '${phase}' on desk ${deskId}`);
    try {
      const result = await runFn();
      showInfoToast(result.message || `${phase} process started.`);
    } catch (error: any) {
      const errorMsg =
        error.response?.data?.detail ||
        error.message ||
        `Failed to start ${phase} process.`;
      console.error(
        `Error triggering run for ${phase} on desk ${deskId}: ${errorMsg}`,
        error
      );
      showErrorToast(`Failed to start ${phase} process: ${errorMsg}`);
    }
  };

  const handleRunIdeation = () => {
    if (deskDetails?._id) {
      handleRun(
        () => deskService.runIdeation(deskDetails._id),
        deskDetails._id,
        "Ideation"
      );
    }
  };
  const handleRunOutline = () => {
    if (deskDetails?._id) {
      handleRun(
        () => deskService.runOutline(deskDetails._id),
        deskDetails._id,
        "Outline"
      );
    }
  };
  const handleRunContent = () => {
    if (deskDetails?._id) {
      handleRun(
        () => deskService.runContentGeneration(deskDetails._id),
        deskDetails._id,
        "Content Generation"
      );
    } else
      showErrorToast(
        "Cannot run content generation: Desk ID or KB ID missing."
      );
  };

  const handleRunDesk = () => {
    if (deskDetails?._id) {
      handleRun(
        () => deskService.runFullDesk(deskDetails._id),
        deskDetails._id,
        "Full Desk"
      );
    } else showErrorToast("Cannot run full desk: Desk ID or KB ID missing.");
  };

  const handleSaveFeedbackGeneric = async (
    updateFn: (deskId: string, data: any) => Promise<any>,
    phase: string,
    feedback: string
  ) => {
    if (deskDetails?._id) {
      console.log(`Saving ${phase} feedback for desk ${deskDetails._id}`);
      try {
        await updateFn(deskDetails._id, { feedback }); // Send only feedback field
        showSuccessToast(`${phase} feedback saved.`);
        // Refetch desk details fully to ensure UI consistency
        await fetchDeskAndStatus(deskDetails._id);
      } catch (error: any) {
        const errorMsg =
          error.response?.data?.detail ||
          error.message ||
          `Failed to save ${phase} feedback.`;
        console.error(
          `Error saving ${phase} feedback for desk ${deskDetails._id}: ${errorMsg}`,
          error
        );
        showErrorToast(`Failed to save ${phase} feedback: ${errorMsg}`);
      }
    }
  };

  const handleSaveIdeationFeedback = async (feedback: string) => {
    console.log("Here");
    await handleSaveFeedbackGeneric(
      deskService.updateIdeationFeedback,
      "Ideation",
      feedback
    );
  };
  const handleSaveOutlineFeedback = async (feedback: string) =>
    await handleSaveFeedbackGeneric(
      deskService.updateOutlineFeedback,
      "Outline",
      feedback
    );
  const handleSaveContentFeedback = async (feedback: string) =>
    await handleSaveFeedbackGeneric(
      deskService.updateContent,
      "Content",
      feedback
    );

  if (isInitialLoading) {
    // Use the initial loading flag
    return (
      <div className="container mx-auto p-4 md:p-6 lg:p-8 space-y-6">
        <Skeleton className="h-24 w-full rounded-lg mb-6" />
        <Skeleton className="h-32 w-full rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-96 w-full rounded-lg" />
          <Skeleton className="h-96 w-full rounded-lg" />
          <Skeleton className="h-96 w-full rounded-lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 text-destructive">
        Error loading data: {error}
      </div>
    );
  }

  if (!deskDetails || !topicDetails) {
    return (
      <div className="container mx-auto p-4">
        Content Desk or Topic details could not be loaded.
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8 space-y-6">
      <DeskDetails
        deskDetails={deskDetails}
        platforms={platforms}
        contentTypes={contentTypes}
        onSave={handleSaveSettings}
        isSaving={isSavingSettings}
        runDesk={handleRunDesk}
        status={runStatus}
      />

      <DeskPhase
        phase="Content"
        currentFeedback={deskDetails?.content?.feedback ?? ""}
        data={deskDetails?.content?.result ?? ""}
        onSaveFeedback={handleSaveContentFeedback}
        status={contentStatus}
        handleRun={handleRunContent}
        addContentForReview={handleAddContentForReview}
        isAddingContent={isAddingContent}
      />
    </div>
  );
}
