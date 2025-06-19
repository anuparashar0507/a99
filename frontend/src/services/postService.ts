import api from '@/lib/api';
import { PagedResponse } from '@/types/api';

export enum PostStatus {
  PENDING_REVIEW = "pending",
  APPROVED = "approved",
}

export interface ApiPost {
  id: string;
  created_at?: string;
  updated_at?: string;
  topic: string;
  context: string;
  platform: string;
  content_type: string;
  content: string;
  qna: string[];
  topic_id: string;
  status: PostStatus;
  user_id?: string;
}

// Interface for the paginated response structure from GET /posts
export interface PostsPaginatedResponse {
  items: ApiPost[];
  total_items: number;
  page_no: number;
  page_size: number;
  total_pages: number;
}

// Interface for creating a new post (matches PostCreateRequest)
export interface CreatePostData {
  topic_id: string;
  topic: string;
  context: string;
  platform: string;
  content_type: string;
  content: string;
  qna: string[];
  status?: PostStatus; // Optional on creation, defaults likely handled by backend
}

// Interface for updating a post (matches PostUpdateRequest)
export interface UpdatePostData {
  topic?: string;
  context?: string;
  platform?: string;
  content_type?: string;
  content?: string;
  qna?: string[];
  status?: PostStatus;
}

// --- Service Implementation ---
export const postService = {
  /**
   * Get paginated posts, filtered by topic and optionally status.
   */
  getPosts: async (params: {
    topicId: string;
    page?: number;
    size?: number;
    status?: PostStatus | ''; // Allow empty string to signify 'all' if needed, or handle in component
    sortBy?: string;
    sortOrder?: number;
  }): Promise<PostsPaginatedResponse> => {
    const {
      topicId,
      page = 1,
      size = 10,
      status,
      sortBy = 'created_at',
      sortOrder = -1
    } = params;

    // Construct query parameters, omitting undefined values
    const queryParams = {
      pageNo: page,
      pageSize: size,
      topic_id: topicId,
      status: status || undefined, // Send status only if provided and not empty
      sort_by: sortBy,
      sort_order: sortOrder,
    };

    try {
      console.debug("Fetching posts with params:", queryParams);
      const response = await api.get<PostsPaginatedResponse>(`/posts/`, { params: queryParams });
      // Validate response structure
      if (!response.data || !Array.isArray(response.data.items)) {
        console.error("Invalid paginated response structure received:", response.data);
        // Return a default empty structure or throw error
        return { items: [], total_items: 0, page_no: page, page_size: size, total_pages: 0 };
      }
      return response.data;
    } catch (error) {
      console.error('Error fetching posts:', error);
      throw error; // Re-throw for UI error handling
    }
  },

  /**
   * Get a specific post by its ID.
   */
  getPost: async (postId: string): Promise<ApiPost> => {
    if (!postId) throw new Error("Post ID is required.");
    try {
      console.debug(`Workspaceing post with ID: ${postId}`);
      const response = await api.get<ApiPost>(`/posts/${postId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching post ${postId}:`, error);
      throw error;
    }
  },

  /**
   * Create a new post.
   */
  createPost: async (data: CreatePostData): Promise<ApiPost> => {
    try {
      console.debug("Creating post with data:", data);
      const response = await api.post<ApiPost>(`/posts/`, data);
      return response.data;
    } catch (error) {
      console.error('Error creating post:', error);
      throw error;
    }
  },

  /**
   * Update an existing post.
   */
  updatePost: async (
    postId: string,
    data: UpdatePostData
  ): Promise<ApiPost> => {
    if (!postId) throw new Error("Post ID is required for update.");
    if (Object.keys(data).length === 0) {
      console.warn("updatePost called with empty data object.");
      // Optionally throw an error or return early
      // For now, let the API call proceed, backend might handle it
    }
    try {
      console.debug(`Updating post ${postId} with data:`, data);
      const response = await api.patch<ApiPost>(`/posts/${postId}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating post ${postId}:`, error);
      throw error;
    }
  },

  /**
   * Delete multiple posts by their IDs.
   */
  deletePosts: async (
    postIds: string[]
  ): Promise<{ deleted_count: number }> => {
    if (!postIds || postIds.length === 0) {
      console.warn("deletePosts called with empty ID list.");
      return { deleted_count: 0 };
    }
    try {
      console.debug(`Deleting posts with IDs: ${postIds.join(', ')}`);
      // For DELETE requests with body in Axios, payload goes in 'data' key of config
      const response = await api.delete<{ deleted_count: number }>(`/posts/`, {
        data: { post_ids: postIds },
      });
      return response.data;
    } catch (error) {
      console.error('Error deleting posts:', error);
      throw error;
    }
  },

};
