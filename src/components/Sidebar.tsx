import { useState } from "react";
import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Id } from "../../convex/_generated/dataModel";
import { UserList } from "./UserList";
import { GroupList } from "./GroupList";
import { ActiveChats } from "./ActiveChats";
import { CreateGroupModal } from "./CreateGroupModal";

interface SidebarProps {
  currentUserId: Id<"users">;
  selectedChat: {
    type: "private" | "group";
    id: string;
    name: string;
    otherUserId?: Id<"users">;
    groupId?: Id<"groups">;
  } | null;
  setSelectedChat: (chat: any) => void;
}

export function Sidebar({ currentUserId, selectedChat, setSelectedChat }: SidebarProps) {
  const [activeTab, setActiveTab] = useState<"chats" | "users" | "groups">("chats");
  const [showCreateGroup, setShowCreateGroup] = useState(false);

  const currentUser = useQuery(api.users.getCurrentUser, 
    currentUserId ? { sessionId: localStorage.getItem("chat-session-id") || "" } : "skip"
  );

  const tabs = [
    { id: "chats", label: "Chats", icon: "💬" },
    { id: "users", label: "Users", icon: "👥" },
    { id: "groups", label: "Groups", icon: "🏢" },
  ];

  return (
    <div className="w-full md:w-80 bg-discord-secondary/80 backdrop-blur-md border-r border-discord-border flex flex-col shadow-xl h-full">
      {/* Header */}
      <div className="p-4 border-b border-discord-border/50 bg-gradient-to-r from-purple-500/10 to-pink-500/10 flex-shrink-0">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            Hushgram
          </h1>
          <div className="flex items-center space-x-2 glass-effect px-3 py-1 rounded-full">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-white font-medium">{currentUser?.username}</span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-discord-dark/50 rounded-xl p-1 backdrop-blur-sm">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all duration-300 flex items-center justify-center space-x-2 ${
                activeTab === tab.id
                  ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-glow transform scale-105"
                  : "text-discord-text hover:text-white hover:bg-discord-hover/50"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full">
          {activeTab === "chats" && (
            <ActiveChats
              currentUserId={currentUserId}
              selectedChat={selectedChat}
              setSelectedChat={setSelectedChat}
            />
          )}
          {activeTab === "users" && (
            <UserList
              currentUserId={currentUserId}
              selectedChat={selectedChat}
              setSelectedChat={setSelectedChat}
            />
          )}
          {activeTab === "groups" && (
            <GroupList
              currentUserId={currentUserId}
              selectedChat={selectedChat}
              setSelectedChat={setSelectedChat}
              onCreateGroup={() => setShowCreateGroup(true)}
            />
          )}
        </div>
      </div>

      {/* Create Group Modal */}
      {showCreateGroup && (
        <CreateGroupModal
          currentUserId={currentUserId}
          onClose={() => setShowCreateGroup(false)}
        />
      )}
    </div>
  );
}
