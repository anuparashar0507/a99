import React from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

interface TopicTab {
  label: string;
  path: string;
}

interface TopicTabsProps {
  topicId: string;
  isActive: boolean;
}

const TopicTabs: React.FC<TopicTabsProps> = ({ topicId, isActive }) => {
  const location = useLocation();

  const tabs: TopicTab[] = [
    // { label: "Settings", path: `/topic/${topicId}/settings` },
    // { label: "Knowledge Base", path: `/topic/${topicId}/knowledge-base` },
    { label: "Content Desks", path: `/topic/${topicId}/desks` },
    { label: "Pending Posts", path: `/topic/${topicId}/posts` },
  ];

  return (
    <nav className="-mb-px">
      {tabs.map((tab) => (
        <Link
          key={tab.path}
          to={tab.path}
          className={cn(
            "inline-block px-4 py-2 text-sm font-medium border-b-2 transition-colors",
            location.pathname === tab.path
              ? "border-purple-600 text-purple-600"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          )}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
};

export default TopicTabs;
