export type KbFileType = 'text' | 'file' | 'webpage';

export interface KbDocument {
   _id: string;
   created_at: string;
   updated_at: string;
   name: string;
   doc_type: string;
   doc_link: string;
   kb_id: string;
}

export interface KbTextRequest {
   kb_id: string;
   text: string;
}

export interface KbWebsiteRequest {
   kb_id: string;
   source: string;
   urls: string[];
}

export interface KbFileRequest {
   kb_id: string;
   file: File;
}

export interface KbDeleteRequest {
   kb_id: string;
   sources: string[];
}

export interface KbResponse {
   success: boolean;
   message: string;
   data?: KbDocument;
}