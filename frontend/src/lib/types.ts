export enum Path {
   HOME = "/",
   AUTH = "auth",
   LOGIN = "login",
   TOPIC = "topic",
   KNOWLEDGE_BASE = "knowledge-base",
   CONTENTDESK = "desks",
   PENDING_POSTS = "posts",
   SETTINGS = "settings",
}

export enum PostStatus {
   INITIALIZED = "initialized",
   IN_PROGRESS = "in_progress",
   COMPLETED = "completed",
   IN_REVIEW = "in_review",
   SCHEDULED = "scheduled",
   PENDING = "pending",
   PUBLISHED = "published",
   APPROVED = "approved",
}

export interface IPost {
   _id: string;
   post_id: string;
   blog: { content: string; created_at: string }[];
   blog_title: string;
   context: string;
   conversations: [
      string,
      string,
      string[],
      string,
      string,
      string[],
      string,
      string,
      string[]
   ][];
   created_at: string;
   history: [
      string,
      string,
      string[],
      string,
      string,
      string[],
      string,
      string,
      string[]
   ];
   integration_id: string;
   perspectives: string[];
   platform: string;
   scratchpad_id: number;
   sources: any[];
   status: string;
   topic: string;
   updated_at: string;
}

export interface IAgentProject {
   _id: string;
   project_id: string;
   answer_generator_agent: string;
   content_formatter_agent: string;
   example_blogs: any[];
   expert_persona_generator_agent: string;
   format: any[];
   human_in_loop: boolean;
   activate: boolean;
   image_store: number;
   instructions: string;
   name: string;
   org: string;
   outline_generator_agent: string;
   outline_refiner_agent: string;
   post_limit: number;
   question_generator_agent: string;
   rag_store: number;
   related_topic_generator_agent: string;
   section_writter_agent: string;
   sectional_question_generator_agent: string;
   tone: any[];
   topics: ITopic[];
}

export interface ITopic {
   topic_id: string;
   text: string;
   context: string;
   created_at: string;
   enabled: boolean;
}