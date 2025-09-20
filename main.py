# from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# from pydantic import BaseModel
# from typing import Dict, List, Optional, Set
# import json
# import uuid
# import asyncio
# import time
# from datetime import datetime, timedelta
# import hashlib
# import os
# from database import (
#     get_db, get_redis, create_tables,
#     User as DBUser, Group as DBGroup, GroupMember, Message as DBMessage
# )

# app = FastAPI()

# # CORS middleware for development
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Data Models
# class User(BaseModel):
#     id: str
#     username: str
#     connected_at: datetime
#     last_seen: datetime
#     is_typing: bool = False
#     typing_in: Optional[str] = None

# class Message(BaseModel):
#     id: str
#     sender_id: str
#     sender_username: str
#     content: str
#     timestamp: datetime
#     message_type: str = "text"  # text, system
#     status: str = "sent"  # sent, delivered, seen

# class PrivateChat(BaseModel):
#     id: str
#     participants: List[str]
#     messages: List[Message] = []
#     created_at: datetime
#     last_activity: datetime

# class Group(BaseModel):
#     id: str
#     name: str
#     description: str
#     type: str  # public, private
#     password: Optional[str] = None
#     creator_id: str
#     members: List[str] = []
#     pending_requests: List[str] = []
#     messages: List[Message] = []
#     created_at: datetime
#     last_activity: datetime

# # In-memory storage (use Redis/DynamoDB in production)
# users: Dict[str, User] = {}
# connections: Dict[str, WebSocket] = {}
# private_chats: Dict[str, PrivateChat] = {}
# groups: Dict[str, Group] = {}
# user_sessions: Dict[str, str] = {}  # websocket_id -> user_id
# message_status: Dict[str, Dict[str, str]] = {}  # message_id -> {user_id: status}

# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: Dict[str, WebSocket] = {}
        
#     async def connect(self, websocket: WebSocket, user_id: str):
#         await websocket.accept()
#         self.active_connections[user_id] = websocket
        
#     def disconnect(self, user_id: str):
#         if user_id in self.active_connections:
#             del self.active_connections[user_id]
#         # Clean up user session
#         self.cleanup_user_session(user_id)
            
#     def cleanup_user_session(self, user_id: str):
#         """Clean up user session and make username available again"""
#         if user_id in users:
#             username = users[user_id].username
#             print(f"Cleaning up session for user: {username}")
#             del users[user_id]
#         if user_id in connections:
#             del connections[user_id]
#         # Clean up any typing indicators
#         for chat_id, typing_user_id in list(user_sessions.items()):
#             if typing_user_id == user_id:
#                 del user_sessions[chat_id]
            
#     async def send_personal_message(self, message: dict, user_id: str):
#         if user_id in self.active_connections:
#             try:
#                 await self.active_connections[user_id].send_text(json.dumps(message))
#                 return True
#             except:
#                 self.disconnect(user_id)
#                 return False
#         return False
        
#     async def broadcast_to_users(self, message: dict, user_ids: List[str]):
#         disconnected = []
#         for user_id in user_ids:
#             if user_id in self.active_connections:
#                 try:
#                     await self.active_connections[user_id].send_text(json.dumps(message))
#                 except:
#                     disconnected.append(user_id)
        
#         for user_id in disconnected:
#             self.disconnect(user_id)

# manager = ConnectionManager()

# # Utility functions
# def generate_id():
#     return str(uuid.uuid4())

# def hash_password(password: str) -> str:
#     return hashlib.sha256(password.encode()).hexdigest()

# def get_private_chat_id(user1_id: str, user2_id: str) -> str:
#     return f"chat_{'_'.join(sorted([user1_id, user2_id]))}"

# def cleanup_inactive_users():
#     """Remove users inactive for more than 10 minutes"""
#     cutoff_time = datetime.now() - timedelta(minutes=10)
#     inactive_users = [
#         user_id for user_id, user in users.items() 
#         if user.last_seen < cutoff_time and user_id not in connections
#     ]
    
#     for user_id in inactive_users:
#         username = users[user_id].username if user_id in users else "Unknown"
#         print(f"Removing inactive user: {username}")
#         manager.cleanup_user_session(user_id)

# # API Routes
# @app.post("/api/check-username")
# async def check_username(data: dict):
#     username = data.get("username", "").strip()
#     if not username or len(username) < 2 or len(username) > 20:
#         raise HTTPException(status_code=400, detail="Username must be 2-20 characters")
    
#     # Clean up inactive users first
#     cleanup_inactive_users()
    
#     # Check if username is taken by active users
#     for user in users.values():
#         if user.username.lower() == username.lower():
#             raise HTTPException(status_code=409, detail="Username already taken")
    
#     return {"available": True}

# @app.post("/api/create-user")
# async def create_user(data: dict):
#     username = data.get("username", "").strip()
    
#     # Validate username again
#     if not username or len(username) < 2 or len(username) > 20:
#         raise HTTPException(status_code=400, detail="Invalid username")
    
#     # Clean up inactive users first
#     cleanup_inactive_users()
    
#     for user in users.values():
#         if user.username.lower() == username.lower():
#             raise HTTPException(status_code=409, detail="Username already taken")
    
#     user_id = generate_id()
#     user = User(
#         id=user_id,
#         username=username,
#         connected_at=datetime.now(),
#         last_seen=datetime.now()
#     )
    
#     users[user_id] = user
#     print(f"Created new user: {username} ({user_id})")
#     return {"user_id": user_id, "username": username}

# @app.get("/api/users")
# async def get_online_users():
#     cleanup_inactive_users()
#     online_users = []
#     for user in users.values():
#         if user.id in connections or (datetime.now() - user.last_seen).seconds < 300:  # 5 minutes
#             online_users.append({
#                 "id": user.id,
#                 "username": user.username,
#                 "last_seen": user.last_seen.isoformat(),
#                 "is_typing": user.is_typing,
#                 "typing_in": user.typing_in
#             })
#     return online_users

# @app.get("/api/groups")
# async def get_groups():
#     group_list = []
#     for group in groups.values():
#         group_list.append({
#             "id": group.id,
#             "name": group.name,
#             "description": group.description,
#             "type": group.type,
#             "member_count": len(group.members),
#             "has_password": bool(group.password),
#             "created_at": group.created_at.isoformat()
#         })
#     return sorted(group_list, key=lambda x: x["created_at"], reverse=True)

# @app.post("/api/create-group")
# async def create_group(data: dict):
#     user_id = data.get("user_id")
#     name = data.get("name", "").strip()
#     description = data.get("description", "").strip()
#     group_type = data.get("type", "public")
#     password = data.get("password", "").strip() if data.get("password") else None
    
#     if not user_id or user_id not in users:
#         raise HTTPException(status_code=401, detail="Invalid user")
    
#     if not name or len(name) < 2 or len(name) > 50:
#         raise HTTPException(status_code=400, detail="Group name must be 2-50 characters")
    
#     if len(description) > 200:
#         raise HTTPException(status_code=400, detail="Description too long")
    
#     group_id = generate_id()
#     group = Group(
#         id=group_id,
#         name=name,
#         description=description,
#         type=group_type,
#         password=hash_password(password) if password else None,
#         creator_id=user_id,
#         members=[user_id],
#         created_at=datetime.now(),
#         last_activity=datetime.now()
#     )
    
#     groups[group_id] = group
    
#     # Add system message
#     system_msg = Message(
#         id=generate_id(),
#         sender_id="system",
#         sender_username="System",
#         content=f"{users[user_id].username} created the group",
#         timestamp=datetime.now(),
#         message_type="system"
#     )
#     group.messages.append(system_msg)
    
#     return {"group_id": group_id}

# @app.post("/api/join-group")
# async def join_group(data: dict):
#     user_id = data.get("user_id")
#     group_id = data.get("group_id")
#     password = data.get("password", "")
    
#     if not user_id or user_id not in users:
#         raise HTTPException(status_code=401, detail="Invalid user")
    
#     if group_id not in groups:
#         raise HTTPException(status_code=404, detail="Group not found")
    
#     group = groups[group_id]
    
#     if user_id in group.members:
#         return {"success": True, "message": "Already a member"}
    
#     # Check password for private groups
#     if group.type == "private" and group.password:
#         if not password or hash_password(password) != group.password:
#             raise HTTPException(status_code=403, detail="Incorrect password")
    
#     group.members.append(user_id)
    
#     # Add system message
#     system_msg = Message(
#         id=generate_id(),
#         sender_id="system",
#         sender_username="System",
#         content=f"{users[user_id].username} joined the group",
#         timestamp=datetime.now(),
#         message_type="system"
#     )
#     group.messages.append(system_msg)
    
#     # Notify other members
#     await manager.broadcast_to_users({
#         "type": "group_message",
#         "group_id": group_id,
#         "message": {
#             "id": system_msg.id,
#             "sender_id": system_msg.sender_id,
#             "sender_username": system_msg.sender_username,
#             "content": system_msg.content,
#             "timestamp": system_msg.timestamp.isoformat(),
#             "message_type": system_msg.message_type
#         }
#     }, [m for m in group.members if m != user_id])
    
#     return {"success": True}

# @app.get("/api/group/{group_id}/messages")
# async def get_group_messages(group_id: str, user_id: str):
#     if user_id not in users:
#         raise HTTPException(status_code=401, detail="Invalid user")
    
#     if group_id not in groups:
#         raise HTTPException(status_code=404, detail="Group not found")
    
#     group = groups[group_id]
    
#     if user_id not in group.members:
#         raise HTTPException(status_code=403, detail="Not a member")
    
#     messages = []
#     for msg in group.messages[-100:]:  # Last 100 messages
#         messages.append({
#             "id": msg.id,
#             "sender_id": msg.sender_id,
#             "sender_username": msg.sender_username,
#             "content": msg.content,
#             "timestamp": msg.timestamp.isoformat(),
#             "message_type": msg.message_type
#         })
    
#     return messages

# @app.get("/api/private-chat/{other_user_id}")
# async def get_private_chat(other_user_id: str, user_id: str):
#     if user_id not in users or other_user_id not in users:
#         raise HTTPException(status_code=401, detail="Invalid user")
    
#     chat_id = get_private_chat_id(user_id, other_user_id)
    
#     if chat_id not in private_chats:
#         return []
    
#     chat = private_chats[chat_id]
#     messages = []
    
#     for msg in chat.messages[-50:]:  # Last 50 messages
#         messages.append({
#             "id": msg.id,
#             "sender_id": msg.sender_id,
#             "sender_username": msg.sender_username,
#             "content": msg.content,
#             "timestamp": msg.timestamp.isoformat(),
#             "message_type": msg.message_type
#         })
    
#     return messages

# # WebSocket endpoint
# @app.websocket("/ws/{user_id}")
# async def websocket_endpoint(websocket: WebSocket, user_id: str):
#     if user_id not in users:
#         await websocket.close(code=4001, reason="Invalid user")
#         return
    
#     await manager.connect(websocket, user_id)
#     connections[user_id] = websocket
#     users[user_id].last_seen = datetime.now()
    
#     print(f"User {users[user_id].username} connected via WebSocket")
    
#     # Notify others that user is online
#     await manager.broadcast_to_users({
#         "type": "user_online",
#         "user": {
#             "id": user_id,
#             "username": users[user_id].username
#         }
#     }, [u for u in users.keys() if u != user_id])
    
#     try:
#         while True:
#             data = await websocket.receive_text()
#             message_data = json.loads(data)
            
#             await handle_websocket_message(user_id, message_data)
            
#     except WebSocketDisconnect:
#         username = users[user_id].username if user_id in users else "Unknown"
#         print(f"User {username} disconnected")
#         manager.disconnect(user_id)
        
#         # Notify others that user is offline
#         await manager.broadcast_to_users({
#             "type": "user_offline",
#             "user_id": user_id
#         }, [u for u in users.keys() if u != user_id])

# async def handle_websocket_message(user_id: str, data: dict):
#     message_type = data.get("type")
    
#     # Update user's last seen
#     if user_id in users:
#         users[user_id].last_seen = datetime.now()
    
#     if message_type == "private_message":
#         await handle_private_message(user_id, data)
#     elif message_type == "group_message":
#         await handle_group_message(user_id, data)
#     elif message_type == "typing":
#         await handle_typing(user_id, data)
#     elif message_type == "stop_typing":
#         await handle_stop_typing(user_id, data)
#     elif message_type == "message_status":
#         await handle_message_status(user_id, data)
#     elif message_type == "end_session":
#         await handle_end_session(user_id)
#     elif message_type == "user_inactive":
#         # User switched tabs or became inactive
#         if user_id in users:
#             users[user_id].last_seen = datetime.now() - timedelta(minutes=5)
#     elif message_type == "user_active":
#         # User came back
#         if user_id in users:
#             users[user_id].last_seen = datetime.now()

# async def handle_end_session(user_id: str):
#     """Handle user ending their session manually"""
#     username = users[user_id].username if user_id in users else "Unknown"
#     print(f"User {username} ended session manually")
#     manager.disconnect(user_id)
    
#     # Notify others that user is offline
#     await manager.broadcast_to_users({
#         "type": "user_offline",
#         "user_id": user_id
#     }, [u for u in users.keys() if u != user_id])

# async def handle_private_message(sender_id: str, data: dict):
#     recipient_id = data.get("recipient_id")
#     content = data.get("content", "").strip()
#     message_id = data.get("message_id", generate_id())
    
#     if not content or not recipient_id or recipient_id not in users:
#         return
    
#     chat_id = get_private_chat_id(sender_id, recipient_id)
    
#     if chat_id not in private_chats:
#         private_chats[chat_id] = PrivateChat(
#             id=chat_id,
#             participants=[sender_id, recipient_id],
#             created_at=datetime.now(),
#             last_activity=datetime.now()
#         )
    
#     chat = private_chats[chat_id]
    
#     message = Message(
#         id=message_id,
#         sender_id=sender_id,
#         sender_username=users[sender_id].username,
#         content=content,
#         timestamp=datetime.now(),
#         status="sent"
#     )
    
#     chat.messages.append(message)
#     chat.last_activity = datetime.now()
    
#     # Send to both users
#     message_payload = {
#         "type": "private_message",
#         "chat_id": chat_id,
#         "message": {
#             "id": message.id,
#             "sender_id": message.sender_id,
#             "sender_username": message.sender_username,
#             "content": message.content,
#             "timestamp": message.timestamp.isoformat(),
#             "message_type": message.message_type
#         }
#     }
    
#     await manager.send_personal_message(message_payload, sender_id)
#     delivered = await manager.send_personal_message(message_payload, recipient_id)
    
#     # Update message status to delivered if recipient received it
#     if delivered:
#         await manager.send_personal_message({
#             "type": "message_status",
#             "chat_id": chat_id,
#             "message_id": message_id,
#             "status": "delivered"
#         }, sender_id)

# async def handle_group_message(sender_id: str, data: dict):
#     group_id = data.get("group_id")
#     content = data.get("content", "").strip()
#     message_id = data.get("message_id", generate_id())
    
#     if not content or group_id not in groups:
#         return
    
#     group = groups[group_id]
    
#     if sender_id not in group.members:
#         return
    
#     message = Message(
#         id=message_id,
#         sender_id=sender_id,
#         sender_username=users[sender_id].username,
#         content=content,
#         timestamp=datetime.now()
#     )
    
#     group.messages.append(message)
#     group.last_activity = datetime.now()
    
#     message_payload = {
#         "type": "group_message",
#         "group_id": group_id,
#         "message": {
#             "id": message.id,
#             "sender_id": message.sender_id,
#             "sender_username": message.sender_username,
#             "content": message.content,
#             "timestamp": message.timestamp.isoformat(),
#             "message_type": message.message_type
#         }
#     }
    
#     await manager.broadcast_to_users(message_payload, group.members)

# async def handle_message_status(user_id: str, data: dict):
#     chat_id = data.get("chat_id")
#     message_id = data.get("message_id")
#     status = data.get("status")
    
#     if not chat_id or not message_id or not status:
#         return
    
#     # Find the other participant in private chat
#     if chat_id.startswith("chat_"):
#         chat = private_chats.get(chat_id)
#         if chat:
#             other_user_id = None
#             for participant in chat.participants:
#                 if participant != user_id:
#                     other_user_id = participant
#                     break
            
#             if other_user_id:
#                 # Send status update to sender
#                 await manager.send_personal_message({
#                     "type": "message_status",
#                     "chat_id": chat_id,
#                     "message_id": message_id,
#                     "status": status
#                 }, other_user_id)

# async def handle_typing(user_id: str, data: dict):
#     chat_type = data.get("chat_type")  # "private" or "group"
#     chat_id = data.get("chat_id")
    
#     if user_id not in users:
#         return
        
#     users[user_id].is_typing = True
#     users[user_id].typing_in = chat_id
    
#     typing_payload = {
#         "type": "user_typing",
#         "user_id": user_id,
#         "username": users[user_id].username,
#         "chat_type": chat_type,
#         "chat_id": chat_id
#     }
    
#     if chat_type == "private":
#         # Extract other user from private chat
#         for other_user_id in users.keys():
#             if other_user_id != user_id and get_private_chat_id(user_id, other_user_id) == chat_id:
#                 await manager.send_personal_message(typing_payload, other_user_id)
#                 break
#     elif chat_type == "group" and chat_id in groups:
#         group = groups[chat_id]
#         await manager.broadcast_to_users(typing_payload, [m for m in group.members if m != user_id])

# async def handle_stop_typing(user_id: str, data: dict):
#     if user_id not in users:
#         return
        
#     users[user_id].is_typing = False
#     users[user_id].typing_in = None
    
#     chat_type = data.get("chat_type")
#     chat_id = data.get("chat_id")
    
#     stop_typing_payload = {
#         "type": "user_stop_typing",
#         "user_id": user_id,
#         "chat_type": chat_type,
#         "chat_id": chat_id
#     }
    
#     if chat_type == "private":
#         for other_user_id in users.keys():
#             if other_user_id != user_id and get_private_chat_id(user_id, other_user_id) == chat_id:
#                 await manager.send_personal_message(stop_typing_payload, other_user_id)
#                 break
#     elif chat_type == "group" and chat_id in groups:
#         group = groups[chat_id]
#         await manager.broadcast_to_users(stop_typing_payload, [m for m in group.members if m != user_id])

# # Periodic cleanup task
# @app.on_event("startup")
# async def startup_event():
#     create_tables()  # Remove await since it's now sync
    
#     async def periodic_cleanup():
#         while True:
#             await asyncio.sleep(300)
    
#     asyncio.create_task(periodic_cleanup())

# # Serve static files
# if os.path.exists("static"):
#     app.mount("/", StaticFiles(directory="static", html=True), name="static")

# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)


from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
users: Dict[str, dict] = {}
connections: Dict[str, WebSocket] = {}
groups: Dict[str, dict] = {}
messages: Dict[str, list] = {}
private_chats: Dict[str, list] = {}

def generate_id():
    return str(uuid.uuid4())

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_private_chat_id(user1_id: str, user2_id: str) -> str:
    return f"chat_{'_'.join(sorted([user1_id, user2_id]))}"

# API Routes
@app.get("/health")
async def health():
    return {"status": "ok", "connections": len(connections)}

@app.post("/api/create-user")
async def create_user(data: dict):
    username = data.get("username", "").strip()
    
    if not username or len(username) < 2 or len(username) > 20:
        raise HTTPException(status_code=400, detail="Username must be 2-20 characters")
    
    for user in users.values():
        if user["username"].lower() == username.lower():
            raise HTTPException(status_code=409, detail="Username already taken")
    
    user_id = generate_id()
    users[user_id] = {
        "id": user_id,
        "username": username,
        "connected_at": datetime.utcnow().isoformat(),
        "last_seen": datetime.utcnow().isoformat()
    }
    
    return {"user_id": user_id, "username": username}

@app.get("/api/users")
async def get_online_users():
    online_users = []
    for user in users.values():
        if user["id"] in connections:
            online_users.append({
                "id": user["id"],
                "username": user["username"],
                "last_seen": user["last_seen"],
                "is_typing": False,
                "typing_in": None
            })
    return online_users

@app.get("/api/groups")
async def get_groups():
    group_list = []
    for group in groups.values():
        group_list.append({
            "id": group["id"],
            "name": group["name"],
            "description": group.get("description", ""),
            "type": group["type"],
            "member_count": len(group.get("members", [])),
            "has_password": bool(group.get("password_hash")),
            "created_at": group["created_at"]
        })
    return sorted(group_list, key=lambda x: x["created_at"], reverse=True)

@app.post("/api/create-group")
async def create_group(data: dict):
    user_id = data.get("user_id")
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    group_type = data.get("type", "public")
    password = data.get("password", "").strip() if data.get("password") else None
    
    if user_id not in users:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    if not name or len(name) < 2 or len(name) > 50:
        raise HTTPException(status_code=400, detail="Group name must be 2-50 characters")
    
    group_id = generate_id()
    groups[group_id] = {
        "id": group_id,
        "name": name,
        "description": description,
        "type": group_type,
        "password_hash": hash_password(password) if password else None,
        "creator_id": user_id,
        "members": [user_id],
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat()
    }
    
    # Initialize group messages
    messages[group_id] = [{
        "id": generate_id(),
        "sender_id": "system",
        "sender_username": "System",
        "content": f"{users[user_id]['username']} created the group",
        "timestamp": datetime.utcnow().isoformat(),
        "message_type": "system"
    }]
    
    return {"group_id": group_id}

@app.post("/api/join-group")
async def join_group(data: dict):
    user_id = data.get("user_id")
    group_id = data.get("group_id")
    password = data.get("password", "")
    
    if user_id not in users:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group = groups[group_id]
    
    if user_id in group.get("members", []):
        return {"success": True, "message": "Already a member"}
    
    # Check password for private groups
    if group["type"] == "private" and group.get("password_hash"):
        if not password or hash_password(password) != group["password_hash"]:
            raise HTTPException(status_code=403, detail="Incorrect password")
    
    group["members"].append(user_id)
    
    # Add system message
    if group_id not in messages:
        messages[group_id] = []
    
    messages[group_id].append({
        "id": generate_id(),
        "sender_id": "system",
        "sender_username": "System",
        "content": f"{users[user_id]['username']} joined the group",
        "timestamp": datetime.utcnow().isoformat(),
        "message_type": "system"
    })
    
    return {"success": True}

@app.get("/api/group/{group_id}/messages")
async def get_group_messages(group_id: str, user_id: str):
    if user_id not in users:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group = groups[group_id]
    if user_id not in group.get("members", []):
        raise HTTPException(status_code=403, detail="Not a member")
    
    return messages.get(group_id, [])[-100:]  # Last 100 messages

@app.get("/api/private-chat/{other_user_id}")
async def get_private_chat(other_user_id: str, user_id: str):
    if user_id not in users or other_user_id not in users:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    chat_id = get_private_chat_id(user_id, other_user_id)
    return private_chats.get(chat_id, [])[-50:]  # Last 50 messages

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    if user_id not in users:
        await websocket.close(code=4001, reason="Invalid user")
        return
    
    await websocket.accept()
    connections[user_id] = websocket
    
    # Notify others user is online
    for other_user_id, ws in connections.items():
        if other_user_id != user_id:
            try:
                await ws.send_text(json.dumps({
                    "type": "user_online",
                    "user": {
                        "id": user_id,
                        "username": users[user_id]["username"]
                    }
                }))
            except:
                pass
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "private_message":
                recipient_id = message_data.get("recipient_id")
                content = message_data.get("content", "").strip()
                message_id = message_data.get("message_id", generate_id())
                
                if content and recipient_id:
                    chat_id = get_private_chat_id(user_id, recipient_id)
                    
                    # Store message
                    if chat_id not in private_chats:
                        private_chats[chat_id] = []
                    
                    message = {
                        "id": message_id,
                        "sender_id": user_id,
                        "sender_username": users[user_id]["username"],
                        "content": content,
                        "timestamp": datetime.utcnow().isoformat(),
                        "message_type": "text"
                    }
                    
                    private_chats[chat_id].append(message)
                    
                    # Send to both users
                    message_payload = {
                        "type": "private_message",
                        "chat_id": chat_id,
                        "message": message
                    }
                    
                    await websocket.send_text(json.dumps(message_payload))
                    if recipient_id in connections:
                        await connections[recipient_id].send_text(json.dumps(message_payload))
            
            elif message_data.get("type") == "group_message":
                group_id = message_data.get("group_id")
                content = message_data.get("content", "").strip()
                message_id = message_data.get("message_id", generate_id())
                
                if content and group_id in groups:
                    group = groups[group_id]
                    
                    if user_id in group.get("members", []):
                        # Store message
                        if group_id not in messages:
                            messages[group_id] = []
                        
                        message = {
                            "id": message_id,
                            "sender_id": user_id,
                            "sender_username": users[user_id]["username"],
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat(),
                            "message_type": "text"
                        }
                        
                        messages[group_id].append(message)
                        
                        # Send to all group members
                        message_payload = {
                            "type": "group_message",
                            "group_id": group_id,
                            "message": message
                        }
                        
                        for member_id in group["members"]:
                            if member_id in connections:
                                await connections[member_id].send_text(json.dumps(message_payload))
            
    except WebSocketDisconnect:
        if user_id in connections:
            del connections[user_id]
        
        # Notify others user is offline
        for other_user_id, ws in connections.items():
            try:
                await ws.send_text(json.dumps({
                    "type": "user_offline",
                    "user_id": user_id
                }))
            except:
                pass

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)