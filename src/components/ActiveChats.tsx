import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Id } from "../../convex/_generated/dataModel";

interface ActiveChatsProps {
  currentUserId: Id<"users">;
  selectedChat: any;
  setSelectedChat: (chat: any) => void;
}

export function ActiveChats({ currentUserId, selectedChat, setSelectedChat }: ActiveChatsProps) {
  const activeChats = useQuery(api.messages.getActiveChats, { userId: currentUserId });

  if (!activeChats || activeChats.length === 0) {
    return (
      <div className="p-6 text-center text-discord-text fade-in">
        <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-4 opacity-50">
          <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
          </svg>
        </div>
        <p className="text-lg font-medium mb-1">No recent chats</p>
        <p className="text-sm opacity-70">Start a conversation with someone! 💬</p>
      </div>
    );
  }

  return (
    <div className="overflow-y-auto">
      <div className="p-4 text-xs font-semibold text-discord-text uppercase tracking-wide border-b border-discord-border/50">
        Recent Chats ({activeChats.length})
      </div>
      
      <div className="space-y-1 p-2">
        {activeChats.map((chat, index) => {
          const isSelected = selectedChat?.id === chat.chatId;
          const chatName = chat.chatType === "private" 
            ? (chat as any).otherUser?.username || "Unknown User"
            : (chat as any).group?.name || "Unknown Group";

          const timeAgo = (timestamp: number) => {
            const now = Date.now();
            const diff = now - timestamp;
            const minutes = Math.floor(diff / 60000);
            const hours = Math.floor(diff / 3600000);
            const days = Math.floor(diff / 86400000);

            if (days > 0) return `${days}d ago`;
            if (hours > 0) return `${hours}h ago`;
            if (minutes > 0) return `${minutes}m ago`;
            return 'Just now';
          };

          return (
            <div
              key={chat.chatId}
              onClick={() => {
                if (chat.chatType === "private") {
                  setSelectedChat({
                    type: "private",
                    id: chat.chatId,
                    name: chatName,
                    otherUserId: chat.otherUserId,
                  });
                } else {
                  setSelectedChat({
                    type: "group",
                    id: chat.chatId,
                    name: chatName,
                    groupId: chat.groupId,
                  });
                }
              }}
              className={`p-3 rounded-xl cursor-pointer transition-all duration-300 hover:scale-[1.02] slide-up ${
                isSelected 
                  ? "bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 shadow-glow" 
                  : "hover:bg-discord-hover/50 glass-effect"
              }`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg ${
                    chat.chatType === "private" 
                      ? "bg-gradient-to-r from-purple-500 to-pink-500" 
                      : "bg-gradient-to-r from-green-500 to-blue-500"
                  }`}>
                    {chat.chatType === "private" ? chatName[0]?.toUpperCase() : "#"}
                  </div>
                  {chat.chatType === "private" && (
                    <div className="status-indicator bg-green-500">
                      <div className="pulse-ring"></div>
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-white truncate">{chatName}</h3>
                    <span className="text-xs text-discord-text">
                      {timeAgo(chat.lastMessageTime)}
                    </span>
                  </div>
                  <p className="text-sm text-discord-text flex items-center space-x-2">
                    <span>{chat.chatType === "private" ? "Private chat" : "Group chat"}</span>
                    {chat.chatType === "group" && (
                      <>
                        <span>•</span>
                        <span className="text-green-400">Active</span>
                      </>
                    )}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
