import React, { useState, useEffect, useMemo, useCallback } from "react"; // Added useCallback, useMemo
import { useParams } from "react-router-dom";
import { RefreshCcw, Trash2 } from "lucide-react";

import {
  ColumnDef,
  SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  RowSelectionState,
} from "@tanstack/react-table";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { ReviewPost } from "./ReviewPost";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Loader } from "@/components/ui/loader";
import ConfirmDeleteDialog from "@/components/topic/ConfirmDeleteDialog"; // Import confirmation dialog
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui/tooltip";

import {
  ApiPost,
  postService,
  PostStatus,
  PostsPaginatedResponse,
} from "@/services/postService";
import { showErrorToast, showSuccessToast } from "@/components/ui/toast.tsx";

const getColumns = (
  topicId: string | undefined,
  handleDeletePost: any,
): ColumnDef<ApiPost>[] => [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected()
            ? true
            : table.getIsSomePageRowsSelected()
              ? "indeterminate"
              : false
        }
        onCheckedChange={(value) => {
          table.toggleAllPageRowsSelected(!!value);
        }}
        aria-label="Select all"
        className="data-[state=checked]:bg-purple-500 data-[state=checked]:border-purple-500"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Select row"
        onClick={(e) => e.stopPropagation()}
        className="data-[state=checked]:bg-purple-500 data-[state=checked]:border-purple-500"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "topic",
    header: "Topic",
    cell: ({ row }) => (
      <span className="font-medium">{row.original.topic}</span>
    ),
  },
  {
    accessorKey: "context",
    header: "Context",
    cell: ({ row }) => (
      <p className="text-sm text-muted-foreground truncate max-w-xs">
        {row.original.context}
      </p>
    ),
  },
  {
    accessorKey: "platform",
    header: "Platform",
    cell: ({ row }) => (
      <Badge
        variant={
          row.original.platform?.toLowerCase().includes("blog")
            ? "secondary"
            : "default"
        }
        className="capitalize"
      >
        {row.original.platform}
      </Badge>
    ),
  },
  {
    accessorKey: "created_at",
    header: "Created At",
    cell: ({ row }) => {
      const createdAt = row.original.created_at;
      if (!createdAt) return "-";
      try {
        const date = new Date(createdAt + "Z");

        const formatter = new Intl.DateTimeFormat("en-US", {
          day: "numeric",
          month: "short",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          hour12: true,
        });

        return formatter.format(date);
      } catch {
        return createdAt;
      }
    },
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const statusMap: {
        [key in PostStatus]?: { name: string; color: string };
      } = {
        [PostStatus.PENDING_REVIEW]: {
          name: "Pending Review",
          color: "text-orange-600 dark:text-orange-400",
        },
        [PostStatus.APPROVED]: {
          name: "Approved",
          color: "text-green-600 dark:text-green-400",
        },
      };
      const statusInfo = statusMap[row.original.status];
      return (
        <p
          className={`font-medium ${statusInfo?.color ?? "text-muted-foreground"}`}
        >
          {statusInfo?.name ?? row.original.status}{" "}
        </p>
      );
    },
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }) => (
      <div className="flex items-center justify-end space-x-2 h-full">
        <Tooltip>
          <TooltipTrigger>
            <ReviewPost
              topicId={row.original.topicId}
              post_id={row.original._id}
              currentPost={row.original}
              reviewMode={row.original.status === PostStatus.PENDING_REVIEW}
            />
          </TooltipTrigger>
          <TooltipContent>
            View Post Details
          </TooltipContent>
        </Tooltip>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size="icon"
              className="h-8 w-8 text-destructive/70 hover:text-destructive hover:bg-destructive/10" // Destructive styling
              variant="ghost"
              onClick={(e) => handleDeletePost(row.original, e)}
            >
              <Trash2 />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            Delete Post
          </TooltipContent>
        </Tooltip>
      </div>
    ),
  },
];

const PendingPosts: React.FC = () => {
  const { id: topicId } = useParams<{ id: string }>(); // Get 'id' param and rename to topicId
  const [posts, setPosts] = useState<ApiPost[]>([]);
  const [isFetchingPosts, setIsFetchingPosts] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10); // Fixed page size for this example
  const [totalItems, setTotalItems] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);

  const [sorting, setSorting] = useState<SortingState>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({}); // Use correct type

  const [postToDelete, setPostToDelete] = useState<ApiPost | null>(null);
  const [isConfirmDeleteDialogOpen, setIsConfirmDeleteDialogOpen] =
    useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchPosts = useCallback(
    async (currentPage: number) => {
      if (!topicId) {
        console.warn("Cannot fetch posts, topicId is missing.");
        return;
      }
      setIsFetchingPosts(true);
      setError(null);
      try {
        console.debug(
          `Workspaceing pending posts for topic ${topicId}, page ${currentPage}`,
        );
        const response = await postService.getPosts({
          topicId: topicId,
          status: PostStatus.PENDING_REVIEW, // Use the correct enum value
          page: currentPage,
          size: pageSize,
        });
        setPosts(response.items || []);
        setTotalItems(response.total_items || 0);
        setTotalPages(response.total_pages || 1);
        setPage(currentPage);
        setRowSelection({});
      } catch (err: any) {
        console.error("Failed to fetch posts", err);
        const errorMsg =
          err.response?.data?.detail || err.message || "Failed to load posts.";
        setError(errorMsg);
        showErrorToast(errorMsg);
      } finally {
        setIsFetchingPosts(false);
      }
    },
    [topicId, pageSize],
  );

  const handleDeletePost = (post: ApiPost, e: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setPostToDelete(post);
    setIsConfirmDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!postToDelete) return;

    setIsDeleting(true);
    try {
      await postService.deletePosts([postToDelete._id]);
      showSuccessToast(`Post "${postToDelete.topic}" deleted successfully.`);
      fetchPosts();
      setIsConfirmDeleteDialogOpen(false); // Close dialog on success
      setPostToDelete(null);
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || err.message || "Failed to delete post.";
      console.error(`Error deleting post ${postToDelete._id}:`, err);
      showErrorToast(errorMsg);
      setIsConfirmDeleteDialogOpen(false);
      setPostToDelete(null);
    } finally {
      setIsDeleting(false);
    }
  };

  const tableColumns = useMemo(
    () => getColumns(topicId, handleDeletePost),
    [topicId],
  );
  useEffect(() => {
    fetchPosts(page);
  }, [topicId, page, fetchPosts]);

  const table = useReactTable({
    data: posts,
    columns: tableColumns,
    state: {
      sorting,
      rowSelection,
    },
    manualPagination: true,
    pageCount: totalPages,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onRowSelectionChange: setRowSelection,
    enableRowSelection: true,
  });

  const handleSync = () => {
    fetchPosts(page);
  };

  const handlePreviousPage = () => {
    if (page > 1) {
      setPage((p) => p - 1);
    }
  };

  const handleNextPage = () => {
    if (page < totalPages) {
      setPage((p) => p + 1);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-xl font-semibold">Pending Review</h2>
        <Button
          size="sm"
          variant="outline"
          onClick={handleSync}
          disabled={isFetchingPosts}
          aria-label="Sync Status"
        >
          {isFetchingPosts ? (
            <RefreshCcw className="size-4 mr-2 animate-spin" />
          ) : (
            <RefreshCcw className="size-4 mr-2" />
          )}
          Sync
        </Button>
      </div>
      <div className="p-0 md:p-4">
        <div className="rounded-lg border overflow-hidden">
          <Table>
            <TableHeader className="bg-muted/50 sticky top-0">
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead
                      key={header.id}
                      style={{
                        width:
                          header.getSize() !== 150
                            ? `${header.getSize()}px`
                            : undefined,
                      }}
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {isFetchingPosts && table.getRowModel().rows.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={tableColumns.length}
                    className="h-60 text-center"
                  >
                    <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground">
                      <Loader size={32} />
                      <span>Loading posts...</span>
                    </div>
                  </TableCell>
                </TableRow>
              )}
              {!isFetchingPosts &&
                table.getRowModel().rows.length > 0 &&
                table.getRowModel().rows.map((row) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <TableCell
                        key={cell.id}
                        style={{
                          width:
                            cell.column.getSize() !== 150
                              ? `${cell.column.getSize()}px`
                              : undefined,
                        }}
                      >
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              {!isFetchingPosts && table.getRowModel().rows.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={tableColumns.length}
                    className="h-24 text-center text-muted-foreground"
                  >
                    No pending posts found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>
      <div className="flex items-center justify-between space-x-2 p-4 border-t">
        <div className="flex-1 text-sm text-muted-foreground">
          {table.getFilteredSelectedRowModel().rows.length} of {posts.length}{" "}
          row(s) selected on this page. (Total: {totalItems})
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button
            disabled={page <= 1 || isFetchingPosts}
            variant="outline"
            size="sm"
            onClick={handlePreviousPage}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNextPage}
            disabled={page >= totalPages || isFetchingPosts}
          >
            Next
          </Button>
        </div>
      </div>
      <ConfirmDeleteDialog
        open={isConfirmDeleteDialogOpen}
        onOpenChange={setIsConfirmDeleteDialogOpen}
        onConfirm={handleConfirmDelete}
        title="Delete Post?"
        description={`Are you sure you want to delete the post with topic "${postToDelete?.topic}"? This action cannot be undone.`}
        isDeleting={isDeleting}
      />
    </div>
  );
};

export default PendingPosts;
