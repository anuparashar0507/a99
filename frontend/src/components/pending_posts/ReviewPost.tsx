import { useEffect, useState } from "react";
import "react-quill/dist/quill.snow.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ReactTimeAgo from "react-time-ago";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button, buttonVariants } from "@/components/ui/button";
import { Check, Copy, Eye, Loader2 } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { ApiPost, postService } from "@/services/postService";
import { useProject } from "@/context/TopicContext.tsx";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { IPost } from "@/lib/types";
import { cn, htmlToMarkdown, markdownToHtml } from "@/lib/utils";
import Editor from "./Editor.tsx";
import { showErrorToast, showSuccessToast } from "@/components/ui/toast.tsx";

export const ReviewPost: React.FC<{
  currentPost: ApiPost;
  reviewMode: boolean;
  topicId: string;
  post_id: string;
}> = ({ reviewMode, currentPost, topicId, post_id }) => {
  const { changeTab } = useProject();
  const [sheetVisible, setSheetVisible] = useState<boolean>(false);
  const [post, setPost] = useState<Partial<IPost>>({});
  const [revision, setRevision] = useState<number>(0);
  const [prompt, setPrompt] = useState<string>("");
  const [copied, setCopied] = useState<boolean>(false);
  const [copiedTitle, setCopiedTitle] = useState<boolean>(false);

  const [editorMarkdownValue, setEditorMarkdownValue] = useState<string>("");
  const [isFetchingPost, setIsFetchingPost] = useState<boolean>(false);
  const [isRegeneratingPost, setIsRegeneratingPost] = useState<boolean>(false);
  const [isUpdatingPost, setIsUpdatingPost] = useState<boolean>(false);

  console.log(post);
  const onEditorContentChanged = (content: string) => {
    setEditorMarkdownValue(content);
  };

  const refetchData = async () => {
    setIsFetchingPost(true);
    try {
      const res = await postService.getPostById(topicId, post_id);
      const content = res.blog?.[revision]?.content;
      setEditorMarkdownValue(reviewMode ? markdownToHtml(content) : content);

      if (reviewMode) {
        setPost({
          ...res,
          blog:
            res.blog?.map((val) => ({
              ...val,
              content: markdownToHtml(val.content),
            })) || [],
        });
      } else {
        setPost(res);
      }
    } catch (err) {
      console.error("Error fetching post:", err);
    } finally {
      setIsFetchingPost(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(editorMarkdownValue);
    setCopied(true);
    setTimeout(() => setCopied(false), 5000);
  };

  const handleCopyTitle = () => {
    navigator.clipboard.writeText(post?.topic ?? "");
    setCopiedTitle(true);
    setTimeout(() => setCopiedTitle(false), 5000);
  };

  const onRegenerate = async () => {
    setIsRegeneratingPost(true);
    try {
      await postService.regeneratePost(topicId, {
        post_id: post_id,
        blog: htmlToMarkdown(editorMarkdownValue),
        feedback: prompt,
      });
      await refetchData();
    } catch (err) {
      console.error("Regeneration failed:", err);
    } finally {
      setIsRegeneratingPost(false);
    }
  };

  const handleSave = async () => {
    setIsUpdatingPost(true);
    try {
      await postService.updatePost(post_id, {
        content: editorMarkdownValue,
      });
      showSuccessToast("Saved Post Content!");
      if (changeTab) changeTab(2);
    } catch (err) {
      console.error(err);
      showErrorToast("Somehting went wrong, please try again!");
    } finally {
      setIsUpdatingPost(false);
    }
  };

  useEffect(() => {
    setPost(currentPost);
    setEditorMarkdownValue(currentPost.content);
  }, [currentPost]);

  return (
    <Sheet open={sheetVisible} onOpenChange={setSheetVisible}>
      <SheetTrigger
        className={buttonVariants({ variant: "link" })}
        onClick={() => setSheetVisible(true)}
      >
        <Eye className="size-3 mr-1" />
      </SheetTrigger>
      <SheetContent side="bottom" className="h-5/6 bg-white overflow-y-auto">
        <div className="w-full">
          <SheetHeader>
            <SheetTitle>{!reviewMode ? "View" : "Review"} Post</SheetTitle>
          </SheetHeader>
          <div className="p-4 h-4/5">
            {isFetchingPost ? (
              <div className="h-full grid place-items-center">
                <Loader2 className="animate-spin" size={40} />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <div className="w-full flex space-x-2 gap-4">
                    <div
                      className={cn(
                        "flex space-x-2",
                        reviewMode
                          ? "w-5/6 justify-end"
                          : "w-full justify-between items-center"
                      )}
                    >
                      {!reviewMode && (
                        <span className="flex space-x-2 items-center">
                          <p className="text-lg text-primary font-semibold">
                            📌 {post.topic}
                          </p>
                          <button
                            onClick={handleCopyTitle}
                            className="flex items-center"
                          >
                            {copiedTitle ? (
                              <Check className="size-4 mr-1 text-green-500" />
                            ) : (
                              <Copy className="size-4 mr-1" />
                            )}
                            {copiedTitle && (
                              <p className="text-green-500 text-xs">copied</p>
                            )}
                          </button>
                        </span>
                      )}
                      <Button variant="ghost" onClick={handleCopy}>
                        {copied ? (
                          <Check className="size-4 mr-1 text-green-500" />
                        ) : (
                          <Copy className="size-4 mr-1" />
                        )}
                        <p className={copied ? "text-green-500" : ""}>
                          {copied ? "Copied" : "Copy"}
                        </p>
                      </Button>

                      <Button
                        className="bg-purple-600 hover:bg-purple-700"
                        onClick={handleSave}
                      >
                        {isUpdatingPost ? (
                          <Loader2 className="animate-spin mr-2" />
                        ) : null}
                        Save
                      </Button>
                      {/* reviewMode && (
                        <div className="w-64">
                          <Select
                            value={String(revision)}
                            onValueChange={(value) => {
                              setRevision(Number(value));
                              setEditorMarkdownValue(
                                post?.blog?.[Number(value)]?.content ?? "",
                              );
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {(post?.blog ?? []).map((blog, index) => (
                                <SelectItem key={index} value={String(index)}>
                                  {index + 1 === 1 ? (
                                    <p className="font-medium">Latest</p>
                                  ) : (
                                    <span className="w-full flex space-x-1 items-baseline justify-between">
                                      <p>Revision {index + 1}</p>
                                      <ReactTimeAgo
                                        date={new Date(blog.created_at)}
                                        className="text-muted-foreground text-xs"
                                      />
                                    </span>
                                  )}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )*/}
                    </div>
                    {/*reviewMode && (
                      <div className="w-1/6">
                        <Button
                          onClick={handleApprove}
                          loading={isUpdatingPost}
                          disabled={isUpdatingPost || isRegeneratingPost}
                          className="w-full"
                        >
                          Approve
                        </Button>
                      </div>
                    )*/}
                  </div>
                </div>
                <div className="flex gap-4">
                  {reviewMode ? (
                    <Editor
                      value={editorMarkdownValue}
                      onChange={onEditorContentChanged}
                    />
                  ) : (
                    <div className="w-full p-2 rounded-lg bg-slate-100 h-[30rem] overflow-y-auto">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        className="markdown"
                      >
                        {editorMarkdownValue}
                      </ReactMarkdown>
                    </div>
                  )}
                  {/*reviewMode && (
                    <div className="w-1/6 flex flex-col space-y-4">
                      <Textarea
                        rows={4}
                        placeholder="Write prompt to regenerate the blog"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                      />
                      <Button
                        variant="secondary"
                        loading={isRegeneratingPost}
                        onClick={onRegenerate}
                      >
                        Regenerate
                      </Button>
                    </div>
                  )*/}
                </div>
              </div>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};
