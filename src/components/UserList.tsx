import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Id } from "../../convex/_generated/dataModel";

interface UserListProps {
  currentUserId: Id<"users">;
  selectedChat: any;
  setSelectedChat: (chat: any) => void;
}

export function UserList({ currentUserId, selectedChat, setSelectedChat }: UserListProps) {
  const onlineUsers = useQuery(api.users.getOnlineUsers);

  const otherUsers = onlineUsers?.filter(user => user._id !== currentUserId) || [];

  if (otherUsers.length === 0) {
    return (
      <div className="p-6 text-center text-discord-text fade-in">
        <div className="w-16 h-16 bg-gradient-to-r from-gray-500 to-gray-600 rounded-full flex items-center justify-center mx-auto mb-4 opacity-50">
          <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-lg font-medium mb-1">No other users online</p>
        <p className="text-sm opacity-70">Be the first to start chatting! 🌟</p>
      </div>
    );
  }

  return (
    <div className="overflow-y-auto">
      <div className="p-4 text-xs font-semibold text-discord-text uppercase tracking-wide border-b border-discord-border/50">
        Online Users ({otherUsers.length})
      </div>
      
      <div className="space-y-1 p-2">
        {otherUsers.map((user, index) => {
          const chatId = `private_${currentUserId < user._id ? currentUserId : user._id}_${currentUserId < user._id ? user._id : currentUserId}`;
          const isSelected = selectedChat?.id === chatId;

          return (
            <div
              key={user._id}
              onClick={() => {
                setSelectedChat({
                  type: "private",
                  id: chatId,
                  name: user.username,
                  otherUserId: user._id,
                });
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
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg">
                    {user.username[0]?.toUpperCase()}
                  </div>
                  <div className="status-indicator bg-green-500">
                    <div className="pulse-ring"></div>
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-white truncate text-lg">{user.username}</h3>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <p className="text-sm text-green-400 font-medium">Online now</p>
                  </div>
                </div>
                <div className="text-discord-text hover:text-white transition-colors">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
