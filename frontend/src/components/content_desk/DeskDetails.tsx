import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Loader2, CircleCheck } from "lucide-react";
import {
  ApiContentDesk,
  UpdateDeskRequest,
  GenerationStatus,
} from "@/services/deskService";
import { showInfoToast } from "@/components/ui/toast.tsx";

interface DeskDetailsProps {
  deskDetails: ApiContentDesk;
  platforms: string[];
  contentTypes: string[];
  onSave: (updateData: UpdateDeskRequest) => Promise<void>;
  isSaving: boolean;
  runDesk: () => void;
  status: GenerationStatus;
}

export default function DeskDetails<DeskDetailsProps>({
  deskDetails,
  platforms,
  contentTypes,
  onSave,
  isSaving,
  status,
  runDesk,
}) {
  const [selectedPlatform, setSelectedPlatform] = useState<string | undefined>(
    undefined
  );
  const [selectedContentType, setSelectedContentType] = useState<
    string | undefined
  >(undefined);

  const deskNotRunning =
    status &&
    (status.phase === "not_running" ||
      status.status_text === "success" ||
      status.status_text === "error");
  const completed =
    status && status.phase === "content" && status.status_text === "success";

  useEffect(() => {
    setSelectedPlatform(deskDetails?.platform ?? undefined);
    setSelectedContentType(deskDetails?.content_type ?? undefined);
  }, [deskDetails?.platform, deskDetails?.content_type]);

  /**
   * Unifed handler that first saves any setting changes and then runs the desk.
   * It assumes that the `onSave` prop returns a promise that resolves upon completion.
   */
  const handleSaveAndRun = async () => {
    const updateData: UpdateDeskRequest = {};
    if (
      selectedPlatform !== undefined &&
      selectedPlatform !== (deskDetails.platform ?? undefined)
    ) {
      updateData.platform = selectedPlatform;
    }
    if (
      selectedContentType !== undefined &&
      selectedContentType !== (deskDetails.content_type ?? undefined)
    ) {
      updateData.content_type = selectedContentType;
    }

    if (!platforms.includes(selectedPlatform)) {
      showErrorToast(
        "Please select a Platform to start the generation process."
      );
      return;
    }
    if (!contentTypes.includes(selectedContentType)) {
      showErrorToast(
        "Please select a Content Type to start the generation process."
      );
      return;
    }

    // First, save the settings if there are any changes.
    if (Object.keys(updateData).length > 0) {
      console.debug("Saving desk settings before running:", updateData);
      try {
        await onSave(updateData); // Wait for the save operation to complete.
      } catch (error) {
        console.error("Failed to save settings:", error);
        // Optional: Stop execution if the save fails.
        return;
      }
    }

    // Then, run the desk.
    console.debug("Running desk...");
    runDesk();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Desk Details</CardTitle>
      </CardHeader>
      <CardContent className="">
        <div className="pb-4 border-b mb-3">
          <h1 className="text-2xl font-bold tracking-tight">
            Topic: {deskDetails.topic}
          </h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label htmlFor="platform">Platform</Label>
            <Select
              value={selectedPlatform ?? ""}
              onValueChange={(value) =>
                setSelectedPlatform(value === "" ? undefined : value)
              }
            >
              <SelectTrigger id="platform">
                <SelectValue placeholder="Select platform..." />
              </SelectTrigger>
              <SelectContent>
                {platforms.map((p) => (
                  <SelectItem key={p} value={p}>
                    {p}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label htmlFor="contentType">Content Type</Label>
            <Select
              value={selectedContentType ?? ""}
              onValueChange={(value) =>
                setSelectedContentType(value === "" ? undefined : value)
              }
            >
              <SelectTrigger id="contentType">
                <SelectValue placeholder="Select content type..." />
              </SelectTrigger>
              <SelectContent>
                {contentTypes.map((ct) => (
                  <SelectItem key={ct} value={ct}>
                    {ct}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end gap-2 border-t pt-4">
        <Button
          className="bg-purple-600 hover:bg-purple-700"
          // Disable the button if settings are being saved or the desk is already running.
          disabled={isSaving || !deskNotRunning}
          onClick={handleSaveAndRun}
        >
          {/* Show a spinner if saving or running */}
          {(isSaving || !deskNotRunning) && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          )}
          {/* Show a checkmark if completed and idle */}
          {completed && deskNotRunning && !isSaving && (
            <CircleCheck className="mr-2 h-4 w-4" />
          )}
          {/* Dynamically set button text based on the current state */}
          {isSaving
            ? "Saving..."
            : !deskNotRunning
            ? "Running..."
            : "Save and Run Desk"}
        </Button>
      </CardFooter>
    </Card>
  );
}
