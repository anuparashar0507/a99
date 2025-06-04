// src/services/deskService.ts
import api from '@/lib/api';

// --- Enums mirroring Pydantic ---
export enum GenerationPhase {
  IDEATION = 'ideation',
  OUTLINE = 'outline',
  CONTENT = 'content',
  NOT_RUNNING = 'not_running',
  COMPLETED = 'completed', // Added based on potential need
}

export enum StatusText {
  ERROR = 'error',
  PROCESSING = 'processing',
  SUCCESS = 'success',
  COMPLETED = "completed",
  NO_OP = "no_op",
}

// --- Interfaces mirroring Pydantic Models ---
export interface GenerationStatus {
  phase: GenerationPhase;
  message: string;
  status_text: StatusText;
}

export interface ApiIdeation {
  id: string;
  created_at?: string;
  updated_at?: string;
  feedback: string;
  result: string; // Result from ideation agent (JSON string expected)
}

export interface ApiOutline {
  id: string;
  created_at?: string;
  updated_at?: string;
  feedback: string;
  result: string; // Result from outline agent (Markdown string expected)
}

export interface ApiContent {
  id: string;
  created_at?: string;
  updated_at?: string;
  feedback?: string; // Make optional if not always present
  result: string; // Final formatted content string
}

export interface ApiContentDesk {
  _id: string;
  created_at?: string;
  updated_at?: string;
  name: string;
  topic: string;
  context: string;
  platform?: string | null; // Optional now
  content_type?: string | null; // Optional now
  ideation_id: string;
  outline_id: string;
  content_id: string;
  status: GenerationStatus;
  // user_id is removed from the model itself
}

export interface ApiContentDeskDetailResponse extends ApiContentDesk {
  ideation?: ApiIdeation | null;
  outline?: ApiOutline | null;
  content?: ApiContent | null;
}

// --- Request Interfaces ---
export interface UpdateDeskRequest {
  name?: string;
  topic?: string;
  context?: string;
  platform?: string | null;
  content_type?: string | null;
}

export interface UpdateFeedbackRequest {
  feedback: string;
}

export interface UpdateContentRequest {
  feedback?: string;
  result?: string;
}

// --- Service Implementation ---
export const deskService = {
  /** Config Endpoints */
  getContentTypes: async (): Promise<string[]> => {
    try {
      const response = await api.get<string[]>(`/config/content-types`);
      return response.data;
    } catch (error) {
      console.error('Error fetching content types:', error);
      throw error; // Re-throw for UI handling
    }
  },

  getPlatforms: async (): Promise<string[]> => {
    try {
      const response = await api.get<string[]>(`/config/platforms`);
      return response.data;
    } catch (error) {
      console.error('Error fetching platforms:', error);
      throw error;
    }
  },

  /** Desk Endpoints */
  getDesk: async (deskId: string): Promise<ApiContentDeskDetailResponse> => {
    try {
      const response = await api.get<ApiContentDeskDetailResponse>(`/desk/${deskId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching desk ${deskId}:`, error);
      throw error;
    }
  },

  updateDesk: async (
    deskId: string,
    data: UpdateDeskRequest
  ): Promise<ApiContentDesk> => {
    try {
      const response = await api.patch<ApiContentDesk>(`/desk/${deskId}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating desk ${deskId}:`, error);
      throw error;
    }
  },

  updateIdeationFeedback: async (
    deskId: string,
    data: UpdateFeedbackRequest
  ): Promise<ApiIdeation> => {
    try {
      const response = await api.patch<ApiIdeation>(
        `/desk/${deskId}/ideation`,
        data
      );
      return response.data;
    } catch (error) {
      console.error(`Error updating ideation feedback for desk ${deskId}:`, error);
      throw error;
    }
  },

  updateOutlineFeedback: async (
    deskId: string,
    data: UpdateFeedbackRequest
  ): Promise<ApiOutline> => {
    try {
      const response = await api.patch<ApiOutline>(
        `/desk/${deskId}/outline`,
        data
      );
      return response.data;
    } catch (error) {
      console.error(`Error updating outline feedback for desk ${deskId}:`, error);
      throw error;
    }
  },

  updateContent: async (
    deskId: string,
    data: UpdateContentRequest
  ): Promise<ApiContent> => {
    try {
      const response = await api.patch<ApiContent>(
        `/desk/${deskId}/content`,
        data
      );
      return response.data;
    } catch (error) {
      console.error(`Error updating content for desk ${deskId}:`, error);
      throw error;
    }
  },

  /** Run Endpoints (Background Triggers) */
  runIdeation: async (deskId: string): Promise<{ message: string }> => {
    try {
      const response = await api.post<{ message: string }>(
        `/desk/${deskId}/run/ideation`
      );
      return response.data;
    } catch (error) {
      console.error(`Error triggering ideation run for desk ${deskId}:`, error);
      throw error;
    }
  },

  runOutline: async (deskId: string): Promise<{ message: string }> => {
    try {
      const response = await api.post<{ message: string }>(
        `/desk/${deskId}/run/outline`
      );
      return response.data;
    } catch (error) {
      console.error(`Error triggering outline run for desk ${deskId}:`, error);
      throw error;
    }
  },

  runContentGeneration: async (
    deskId: string,
  ): Promise<{ message: string }> => {
    try {
      // Pass kb_id as query parameter
      const response = await api.post<{ message: string }>(
        `/desk/${deskId}/run/content`
      );
      return response.data;
    } catch (error) {
      console.error(`Error triggering content run for desk ${deskId}:`, error);
      throw error;
    }
  },

  runFullDesk: async (
      deskId: string,
   ): Promise<{ message: string }> => {
      try {
         // Assuming endpoint exists and takes kb_id as query param
         const response = await api.post<{ message: string }>(
             `/desk/${deskId}/run`
         );
         return response.data;
      } catch (error) {
         console.error(`Error triggering full desk run for desk ${deskId}:`, error);
         throw error;
      }
   },


  /** Status Endpoint */
  getDeskStatus: async (deskId: string): Promise<GenerationStatus> => {
    try {
      const response = await api.get<GenerationStatus>(`/desk/${deskId}/status`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching status for desk ${deskId}:`, error);
      // Avoid throwing here if polling fails transiently? Or let caller handle.
      // Returning null might complicate state. Throwing is often better.
      throw error;
    }
  },

  /**
   * NEW: Signal backend to take generated content and create a Post record for review.
   */
  addContentForReview: async (topicId: string): Promise<ApiPost> => {
    if (!topicId) throw new Error("topicId is required to add content for review.");
    try {
      console.debug(`Requesting add content to review for topic ${topicId}`);
      // Makes a POST request, expecting the newly created ApiPost in response
      const response = await api.post<ApiPost>(`/desk/topic/${topicId}/content/add`);
      return response.data;
    } catch (error) {
      console.error(`Error adding content for review for topic ${topicId}:`, error);
      // Consider extracting user-friendly error message from response if available
      // const errorMsg = error.response?.data?.detail || `Failed to submit content for review.`
      // throw new Error(errorMsg);
      throw error; // Re-throw for UI handling
    }
  },
};
