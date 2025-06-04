import React, { useState } from "react";
import {
  Trash2,
  Download,
  Search,
  Upload,
  FileText,
  FileDown,
  File,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { KbDocument } from "@/types/knowledgeBase";

interface TableProps {
  documents: KbDocument[];
  isLoading: boolean;
  onDelete: (documentId: string) => void;
  onUpload: () => void;
}

const Table: React.FC<TableProps> = ({
  documents,
  isLoading,
  onDelete,
  onUpload,
}) => {
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("All");

  const fileTypes = ["pdf", "docx", "txt"];

  const filteredData = documents.filter((item) => {
    const docType = item.doc_type.toLowerCase();
    const filter = activeFilter.toLowerCase();
    const searchTerm = search.toLowerCase();

    const matchesFilter =
      filter === "all" ||
      (filter === "file" && fileTypes.includes(docType)) ||
      filter === docType;

    if (!matchesFilter) return false;

    return (
      item.name.toLowerCase().includes(searchTerm) ||
      docType.includes(searchTerm)
    );
  });

  const toLocaleDate = (createdAt: string) => {
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
  };

  return (
    <div className="mt-4">
      <div className="flex flex-wrap items-center justify-between mb-4 gap-2">
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 w-4 h-4" />
          <Input
            placeholder="Search"
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-2">
          <div className="bg-gray-100 rounded-md overflow-hidden">
            <div className="flex justify-between bg-gray-100 p-1 overflow-hidden">
              {["All", "text", "file", "website"].map((filter) => (
                <button
                  key={filter}
                  onClick={() => setActiveFilter(filter)}
                  className={`w-auto py-2 px-3 text-sm font-medium ${
                    activeFilter === filter
                      ? "bg-white rounded-md text-black shadow-sm"
                      : "text-gray-400 hover:text-black"
                  }`}
                >
                  {filter === "file"
                    ? "File"
                    : filter === "webpage"
                      ? "Website"
                      : filter === "text"
                        ? "Text"
                        : filter}
                </button>
              ))}
            </div>
          </div>
          <Button variant="outline" className="ml-2" onClick={onUpload}>
            <Upload size={16} className="mr-1" />
            Upload
          </Button>
        </div>
      </div>

      <div className="bg-white rounded-lg border overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b">
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                Name
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                Type
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                Created At
              </th>
              <th className="px-4 py-3 w-20"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td
                  colSpan={5}
                  className="px-4 py-8 text-center text-sm text-gray-500"
                >
                  Loading...
                </td>
              </tr>
            ) : filteredData.length === 0 ? (
              <tr>
                <td
                  colSpan={5}
                  className="px-4 py-8 text-center text-sm text-gray-500"
                >
                  No documents found, use upload button
                </td>
              </tr>
            ) : (
              filteredData.map((doc) => (
                <tr key={doc._id} className="border-b">
                  <td className="px-4 py-3 text-sm">
                    {["pdf", "docx", "txt"].includes(
                      doc.doc_type.toLowerCase(),
                    ) ? (
                      <a
                        href={doc.doc_link}
                        download
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center hover:text-blue-800 transition-colors"
                      >
                        <span className="mr-2">
                          {doc.doc_type === "pdf" && <FileText size={16} />}
                          {doc.doc_type === "docx" && <File size={16} />}
                          {doc.doc_type === "txt" && <FileDown size={16} />}
                        </span>
                        {doc.name}
                      </a>
                    ) : (
                      doc.name
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm capitalize">
                    {doc.doc_type === "file"
                      ? "File"
                      : doc.doc_type === "webpage"
                        ? "Website"
                        : doc.doc_type}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {toLocaleDate(doc.created_at)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDelete(doc.name)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Table;
