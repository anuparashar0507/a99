import api from '@/lib/api';

// API response interface based on the provided sample
export interface ApiTopic {
   _id: string;
   created_at: string;
   updated_at: string;
   kb_id: string;
   settings_id: string;
   user_id: string;
   topic: string;
   context: string;
   desk_id: string;
}

// Request interface for creating a new topic
export interface CreateTopicRequest {
   topic: string;
   context: string;
}

export const topicService = {
   /**
    * Get all topics
    */
   getTopics: async (): Promise<ApiTopic[]> => {
      try {
         const response = await api.get(`/topics/`);
         // Handle the paginated response structure
         if (response.data && response.data.items && Array.isArray(response.data.items)) {
            return response.data.items;
         }
         // Fallback in case the response structure is different
         return Array.isArray(response.data) ? response.data : [];
      } catch (error) {
         console.error('Error fetching topics:', error);
         throw error;
      }
   },

   /**
    * Get topic by id 
    */
   getTopic: async (topicId: string): Promise<ApiTopic> => {
      try {
         const response = await api.get(`/topics/${topicId}`);
         return response.data;
      } catch (error) {
         console.error('Error fetching topics:', error);
         throw error;
      }
   },

   /**
    * Create a new topic
    */
   createTopic: async (data: CreateTopicRequest): Promise<ApiTopic> => {
      try {
         const response = await api.post(`/topics/`, data);
         return response.data;
      } catch (error) {
         console.error('Error creating topic:', error);
         throw error;
      }
   },

   /**
    * Copy a topic
    */
   copyTopic: async (topicId: string): Promise<ApiTopic> => {
      try {
         const response = await api.post(`/topics/copy`, {
            topic_id: topicId,
         });
         return response.data;
      } catch (error) {
         console.error('Error copying topic:', error);
         throw error;
      }
   },

   /**
    * Update an existing topic
    */
   updateTopic: async (topicId: string, data: UpdateTopicRequest): Promise<ApiTopic> => {
      if (!topicId) throw new Error("Topic ID is required for update.");
      if (Object.keys(data).length === 0) {
         console.warn("updateTopic called with empty data.");
         // Avoid API call if nothing to update
         // Fetch and return current data instead? Requires getTopic call.
         // Or throw error? Let's throw for now.
         throw new Error("No update data provided.");
      }
      try {
         // Assuming backend uses Put for partial updates
         const response = await api.put<ApiTopic>(`/topics/${topicId}`, data);
         return response.data;
      } catch (error) {
         console.error(`Error updating topic ${topicId}:`, error);
         throw error;
      }
   },


   /**
    * Delete an existing topic by its ID.
    */
   deleteTopic: async (topicId: string): Promise<void> => {
      if (!topicId) throw new Error("Topic ID is required for deletion.");
      try {
         // Assuming backend returns 200/204 No Content on successful deletion
         await api.delete(`/topics/${topicId}`);
         // No explicit return needed if backend sends no content
      } catch (error) {
         console.error(`Error deleting topic ${topicId}:`, error);
         // Re-throw for the UI to handle
         throw error;
      }
   },
};
