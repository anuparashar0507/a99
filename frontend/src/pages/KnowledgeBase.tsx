import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import UploadModal from "@/components/knowledgebase/UploadModal";
import Table from "@/components/knowledgebase/Table";
import { KnowledgeBaseService } from "@/services/knowledgeBaseService";
import { KbDocument } from "@/types/knowledgeBase";
import { useToast } from "@/components/ui/use-toast";
import { topicService } from "@/services/topicService";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const KnowledgeBase: React.FC = () => {
  const { id: topicId } = useParams<{ id: string }>();
  const { toast } = useToast();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [documents, setDocuments] = useState<KbDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [kbId, setKbId] = useState<string>("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<string | null>(null);

  const fetchTopicDetails = async () => {
    if (!topicId) return;

    try {
      const topics = await topicService.getTopics();
      const topic = topics.find((c) => c._id === topicId);
      if (topic && topic.kb_id) {
        setKbId(topic.kb_id);
      } else {
        toast({
          title: "Error",
          description: "Could not find knowledge base ID for this topic",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error fetching topic details:", error);
      toast({
        title: "Error",
        description: "Failed to fetch topic details",
        variant: "destructive",
      });
    }
  };

  const fetchDocuments = async () => {
    if (!topicId) return;

    try {
      setIsLoading(true);
      const docs = await KnowledgeBaseService.getDocumentsByTopic(topicId);
      setDocuments(docs);
    } catch (error) {
      console.error("Error fetching documents:", error);
      toast({
        title: "Error",
        description: "Failed to fetch documents",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const confirmDelete = (documentId: string) => {
    setDocumentToDelete(documentId);
    setDeleteDialogOpen(true);
  };

  const handleDelete = async () => {
    if (!documentToDelete || !kbId) return;

    try {
      await KnowledgeBaseService.deleteDocument(kbId, documentToDelete);
      toast({
        title: "Success",
        description: "Document deleted successfully",
      });
      fetchDocuments();
    } catch (error) {
      console.error("Error deleting document:", error);
      toast({
        title: "Error",
        description: "Failed to delete document",
        variant: "destructive",
      });
    } finally {
      setDeleteDialogOpen(false);
      setDocumentToDelete(null);
    }
  };

  useEffect(() => {
    if (topicId) {
      fetchTopicDetails();
      fetchDocuments();
    }
  }, [topicId]);

  return (
    <div className="p-6">
      <Table
        documents={documents}
        isLoading={isLoading}
        onDelete={confirmDelete}
        onUpload={() => setIsModalOpen(true)}
      />

      {isModalOpen && (
        <UploadModal
          onClose={() => setIsModalOpen(false)}
          onSuccess={() => {
            setIsModalOpen(false);
            fetchDocuments();
            toast({
              title: "Success",
              description: "Document uploaded successfully",
            });
          }}
          topicId={topicId || ""}
        />
      )}

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the
              document from your knowledge base.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default KnowledgeBase;
