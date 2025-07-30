"""
Employee Messaging System
Allows employees to send messages, announcements, and notifications to each other
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
import os
import uuid

class MessageType(Enum):
    """Types of messages"""
    PERSONAL = "personal"        # Direct message between employees
    ANNOUNCEMENT = "announcement" # General announcement to all
    SHIFT_NOTE = "shift_note"    # Shift handover notes
    URGENT = "urgent"           # Urgent notifications
    REMINDER = "reminder"       # Reminders and notes

class MessageStatus(Enum):
    """Message status"""
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"

@dataclass
class EmployeeMessage:
    """Employee message data structure"""
    id: str
    sender_id: str
    sender_name: str
    recipient_id: Optional[str]  # None for broadcast messages
    recipient_name: Optional[str]
    subject: str
    message: str
    message_type: MessageType
    status: MessageStatus
    created_at: datetime
    read_at: Optional[datetime] = None
    priority: str = "normal"  # low, normal, high, urgent
    is_broadcast: bool = False
    expires_at: Optional[datetime] = None
    attachment_url: Optional[str] = None
    file_attachments: Optional[List[dict]] = None  # For multiple file attachments
    folder_attachments: Optional[List[dict]] = None  # For folder sharing attachments
    reply_to_id: Optional[str] = None  # For message replies
    conversation_id: Optional[str] = None  # For conversation threading

class EmployeeMessagingManager:
    """Manages employee messaging system"""
    
    def __init__(self):
        self.messages: Dict[str, EmployeeMessage] = {}
        self._load_messages()
    
    def _get_file_path(self):
        """Get the file path for messages storage"""
        return os.path.join(os.path.dirname(__file__), '..', 'attendance_data', 'employee_messages.json')
    
    def _load_messages(self):
        """Load messages from JSON file"""
        file_path = self._get_file_path()
        file_path = os.path.abspath(file_path)
        
        if not os.path.exists(file_path):
            # Create empty file if it doesn't exist
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for item in data:
                    # Handle message type and status enums
                    try:
                        msg_type = MessageType(item['message_type'])
                    except (KeyError, ValueError):
                        msg_type = MessageType.PERSONAL
                    
                    try:
                        status = MessageStatus(item['status'])
                    except (KeyError, ValueError):
                        status = MessageStatus.UNREAD
                    
                    message = EmployeeMessage(
                        id=item['id'],
                        sender_id=item['sender_id'],
                        sender_name=item['sender_name'],
                        recipient_id=item.get('recipient_id'),
                        recipient_name=item.get('recipient_name'),
                        subject=item['subject'],
                        message=item['message'],
                        message_type=msg_type,
                        status=status,
                        created_at=datetime.fromisoformat(item['created_at']),
                        read_at=datetime.fromisoformat(item['read_at']) if item.get('read_at') else None,
                        priority=item.get('priority', 'normal'),
                        is_broadcast=item.get('is_broadcast', False),
                        expires_at=datetime.fromisoformat(item['expires_at']) if item.get('expires_at') else None,
                        attachment_url=item.get('attachment_url'),
                        file_attachments=item.get('file_attachments'),  # Load file attachments if present
                        folder_attachments=item.get('folder_attachments'),  # Load folder attachments if present
                        reply_to_id=item.get('reply_to_id'),
                        conversation_id=item.get('conversation_id')
                    )
                    self.messages[message.id] = message
                
                print(f"[INFO] Loaded {len(self.messages)} employee messages")
        except Exception as e:
            print(f"[ERROR] Failed to load messages: {e}")
            self.messages = {}
    
    def _save_messages(self):
        """Save messages to JSON file"""
        file_path = self._get_file_path()
        file_path = os.path.abspath(file_path)
        
        try:
            data = []
            for message in self.messages.values():
                # Handle enum values properly
                msg_type = message.message_type.value if hasattr(message.message_type, 'value') else str(message.message_type)
                status = message.status.value if hasattr(message.status, 'value') else str(message.status)
                
                data.append({
                    'id': message.id,
                    'sender_id': message.sender_id,
                    'sender_name': message.sender_name,
                    'recipient_id': message.recipient_id,
                    'recipient_name': message.recipient_name,
                    'subject': message.subject,
                    'message': message.message,
                    'message_type': msg_type,
                    'status': status,
                    'created_at': message.created_at.isoformat(),
                    'read_at': message.read_at.isoformat() if message.read_at else None,
                    'priority': message.priority,
                    'is_broadcast': message.is_broadcast,
                    'expires_at': message.expires_at.isoformat() if message.expires_at else None,
                    'attachment_url': message.attachment_url,
                    'file_attachments': message.file_attachments,  # Save file attachments if present
                    'folder_attachments': message.folder_attachments,  # Save folder attachments if present
                    'reply_to_id': message.reply_to_id,
                    'conversation_id': message.conversation_id
                })
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"[INFO] Saved {len(data)} employee messages")
        except Exception as e:
            print(f"[ERROR] Failed to save messages: {e}")
    
    def send_message_detailed(self, sender_id: str, sender_name: str, 
                    recipient_id: Optional[str], recipient_name: Optional[str],
                    subject: str, message: str, message_type: MessageType = MessageType.PERSONAL,
                    priority: str = "normal", is_broadcast: bool = False,
                    expires_hours: Optional[int] = None) -> str:
        """Send a new message (detailed) - renamed from send_message_original"""
        
        message_id = f"MSG{datetime.now().strftime('%Y%m%d%H%M%S')}{len(self.messages):03d}"
        
        expires_at = None
        if expires_hours:
            expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        new_message = EmployeeMessage(
            id=message_id,
            sender_id=sender_id,
            sender_name=sender_name,
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            subject=subject,
            message=message,
            message_type=message_type,
            status=MessageStatus.UNREAD,
            created_at=datetime.now(),
            priority=priority,
            is_broadcast=is_broadcast,
            expires_at=expires_at
        )
        
        self.messages[message_id] = new_message
        self._save_messages()
        
        return message_id
    
    def send_message_api(self, from_employee_id: str, to_employee_id: str, subject: str, content: str, priority: str = "normal") -> str:
        """Send a message between employees - API compatible method"""
        return self.send_message_detailed(
            sender_id=from_employee_id,
            sender_name=from_employee_id,  # Will use ID as name for now
            recipient_id=to_employee_id,
            recipient_name=to_employee_id,  # Will use ID as name for now
            subject=subject,
            message=content,
            priority=priority,
            is_broadcast=False
        )
    
    def broadcast_message_api(self, from_employee_id: str, subject: str, content: str, priority: str = "normal") -> str:
        """Broadcast a message to all employees - API compatible method"""
        return self.send_message_detailed(
            sender_id=from_employee_id,
            sender_name=from_employee_id,  # Will use ID as name for now
            recipient_id=None,
            recipient_name=None,
            subject=subject,
            message=content,
            priority=priority,
            is_broadcast=True
        )
    
    def get_messages_for_employee(self, employee_id: str, include_broadcasts: bool = True) -> List[EmployeeMessage]:
        """Get all messages for a specific employee"""
        employee_messages = []
        
        for message in self.messages.values():
            # Check if message is expired
            if message.expires_at and datetime.now() > message.expires_at:
                continue
            
            # Include messages where employee is recipient or broadcast messages
            if (message.recipient_id == employee_id or 
                (include_broadcasts and message.is_broadcast)):
                employee_messages.append(message)
        
        # Sort by creation date (newest first)
        employee_messages.sort(key=lambda x: x.created_at, reverse=True)
        return employee_messages
    
    def get_sent_messages(self, sender_id: str) -> List[EmployeeMessage]:
        """Get all messages sent by a specific employee"""
        sent_messages = [msg for msg in self.messages.values() if msg.sender_id == sender_id]
        sent_messages.sort(key=lambda x: x.created_at, reverse=True)
        return sent_messages
    
    def mark_as_read(self, message_id: str, employee_id: str) -> bool:
        """Mark a message as read"""
        if message_id not in self.messages:
            return False
        
        message = self.messages[message_id]
        
        # Only allow recipient to mark as read
        if message.recipient_id != employee_id and not message.is_broadcast:
            return False
        
        message.status = MessageStatus.READ
        message.read_at = datetime.now()
        self._save_messages()
        
        return True
    
    def mark_message_read(self, message_id: str, employee_id: str) -> bool:
        """Mark message as read - API compatible method"""
        return self.mark_as_read(message_id, employee_id)
    
    def get_unread_count(self, employee_id: str) -> int:
        """Get count of unread messages for an employee"""
        unread_count = 0
        
        for message in self.messages.values():
            # Check if message is expired
            if message.expires_at and datetime.now() > message.expires_at:
                continue
            
            # Count unread messages for this employee
            if ((message.recipient_id == employee_id or message.is_broadcast) and 
                message.status == MessageStatus.UNREAD):
                unread_count += 1
        
        return unread_count
    
    def delete_message(self, message_id: str, employee_id: str) -> bool:
        """Delete a message (only sender or recipient can delete)"""
        if message_id not in self.messages:
            return False
        
        message = self.messages[message_id]
        
        # Only sender or recipient can delete
        if message.sender_id != employee_id and message.recipient_id != employee_id:
            return False
        
        del self.messages[message_id]
        self._save_messages()
        
        return True
    
    def delete_message_for_employee(self, message_id: str, employee_id: str) -> bool:
        """Delete message for employee - API compatible method"""
        return self.delete_message(message_id, employee_id)
    
    def get_employee_messages(self, employee_id: str, limit: int = 50, include_read: bool = True) -> List[dict]:
        """Get messages for employee - API compatible method"""
        messages = self.get_messages_for_employee(employee_id, include_broadcasts=True)
        
        # Filter by read status if needed
        if not include_read:
            messages = [msg for msg in messages if msg.status == MessageStatus.UNREAD]
        
        # Sort by date (newest first) and limit
        messages.sort(key=lambda x: x.created_at, reverse=True)
        messages = messages[:limit]
        
        # Convert to dict format expected by API
        return [
            {
                'id': msg.id,
                'from_employee_id': msg.sender_id,
                'from_employee_name': msg.sender_name,
                'to_employee_id': msg.recipient_id,
                'subject': msg.subject,
                'content': msg.message,
                'priority': msg.priority,
                'is_read': msg.status == MessageStatus.READ,
                'is_broadcast': msg.is_broadcast,
                'timestamp': msg.created_at.isoformat(),
                'file_attachments': msg.file_attachments or [],
                'folder_attachments': msg.folder_attachments or [],
                'reply_to_id': msg.reply_to_id,
                'conversation_id': msg.conversation_id
            }
            for msg in messages
        ]
    
    def get_recent_announcements(self, limit: int = 5) -> List[EmployeeMessage]:
        """Get recent announcements for display"""
        announcements = [
            msg for msg in self.messages.values() 
            if msg.message_type == MessageType.ANNOUNCEMENT and msg.is_broadcast
            and (not msg.expires_at or datetime.now() <= msg.expires_at)
        ]
        
        announcements.sort(key=lambda x: x.created_at, reverse=True)
        return announcements[:limit]
    
    def send_message_with_file(self, from_employee_id: str, to_employee_id: str, 
                              subject: str, content: str, file_id: str,
                              priority: str = "normal") -> str:
        """Send a message with a file attachment"""
        # Create file share
        from models.medical_file_sharing import file_manager
        
        success, share_id, message = file_manager.create_file_share(
            file_id=file_id,
            shared_by=from_employee_id,
            shared_with=to_employee_id,
            expires_hours=168  # 7 days
        )
        
        if not success:
            raise Exception(f"Failed to create file share: {message}")
        
        # Add file info to message content
        file_info = file_manager.get_file_info(file_id)
        if file_info:
            content += f"\n\n📎 Attached File: {file_info.original_filename}"
            content += f"\n📊 Size: {file_info.file_size / (1024*1024):.1f} MB"
            content += f"\n🏥 Category: {file_info.file_category.value.replace('_', ' ').title()}"
            if file_info.study_description:
                content += f"\n📋 Study: {file_info.study_description}"
        
        # Send message with attachment URL
        message_id = self.send_message_detailed(
            sender_id=from_employee_id,
            sender_name=from_employee_id,
            recipient_id=to_employee_id,
            recipient_name=to_employee_id,
            subject=subject,
            message=content,
            priority=priority,
            is_broadcast=False
        )
        
        # Update message with attachment info
        if message_id in self.messages:
            self.messages[message_id].attachment_url = f"/api/files/download/{share_id}"
            self._save_messages()
        
        # Update share with message ID
        if share_id in file_manager.file_shares:
            file_manager.file_shares[share_id].message_id = message_id
            file_manager._save_shares()
        
        return message_id
    
    def broadcast_message_with_file(self, from_employee_id: str, subject: str, 
                                   content: str, file_id: str,
                                   priority: str = "normal") -> str:
        """Broadcast a message with a file attachment to all employees"""
        # Create public file share
        from models.medical_file_sharing import file_manager
        
        success, share_id, message = file_manager.create_file_share(
            file_id=file_id,
            shared_by=from_employee_id,
            shared_with=None,  # Public share
            expires_hours=168  # 7 days
        )
        
        if not success:
            raise Exception(f"Failed to create file share: {message}")
        
        # Add file info to message content
        file_info = file_manager.get_file_info(file_id)
        if file_info:
            content += f"\n\n📎 Attached File: {file_info.original_filename}"
            content += f"\n📊 Size: {file_info.file_size / (1024*1024):.1f} MB"
            content += f"\n🏥 Category: {file_info.file_category.value.replace('_', ' ').title()}"
            if file_info.study_description:
                content += f"\n📋 Study: {file_info.study_description}"
        
        # Send broadcast message
        message_id = self.send_message_detailed(
            sender_id=from_employee_id,
            sender_name=from_employee_id,
            recipient_id=None,
            recipient_name=None,
            subject=subject,
            message=content,
            priority=priority,
            is_broadcast=True
        )
        
        # Update message with attachment info
        if message_id in self.messages:
            self.messages[message_id].attachment_url = f"/api/files/download/{share_id}"
            self._save_messages()
        
        # Update share with message ID
        if share_id in file_manager.file_shares:
            file_manager.file_shares[share_id].message_id = message_id
            file_manager._save_shares()
        
        return message_id
    
    def send_message_with_files(self, from_employee_id: str, to_employee_id: str, 
                               subject: str, content: str, file_ids: List[str],
                               priority: str = "normal") -> str:
        """Send a message with multiple file attachments"""
        from models.medical_file_sharing import file_manager
        
        share_ids = []
        file_infos = []
        
        # Create file shares for all files
        for file_id in file_ids:
            success, share_id, message = file_manager.create_file_share(
                file_id=file_id,
                shared_by=from_employee_id,
                shared_with=to_employee_id,
                expires_hours=168  # 7 days
            )
            
            if not success:
                # Clean up any previously created shares
                for cleanup_share_id in share_ids:
                    file_manager.delete_share(cleanup_share_id)
                raise Exception(f"Failed to create file share for {file_id}: {message}")
            
            share_ids.append(share_id)
            
            # Get file info
            file_info = file_manager.get_file_info(file_id)
            if file_info:
                file_infos.append({
                    'file_id': file_id,
                    'share_id': share_id,
                    'filename': file_info.original_filename,
                    'file_size': file_info.file_size,
                    'category': file_info.file_category.value
                })
        
        # Add file attachments info to message content
        if file_infos:
            content += f"\n\n📎 Attached Files ({len(file_infos)}):"
            for info in file_infos:
                content += f"\n   • {info['filename']} ({info['file_size'] / (1024*1024):.1f} MB)"
        
        # Send message
        message_id = self.send_message_detailed(
            sender_id=from_employee_id,
            sender_name=from_employee_id,
            recipient_id=to_employee_id,
            recipient_name=to_employee_id,
            subject=subject,
            message=content,
            priority=priority,
            is_broadcast=False
        )
        
        # Update message with attachment info
        if message_id in self.messages:
            self.messages[message_id].file_attachments = file_infos
            self._save_messages()
        
        # Update shares with message ID
        for share_id in share_ids:
            if share_id in file_manager.file_shares:
                file_manager.file_shares[share_id].message_id = message_id
        file_manager._save_shares()
        
        return message_id
    
    def broadcast_message_with_files(self, from_employee_id: str, subject: str, 
                                    content: str, file_ids: List[str],
                                    priority: str = "normal") -> str:
        """Broadcast a message with multiple file attachments to all employees"""
        from models.medical_file_sharing import file_manager
        
        share_ids = []
        file_infos = []
        
        # Create public file shares for all files
        for file_id in file_ids:
            success, share_id, message = file_manager.create_file_share(
                file_id=file_id,
                shared_by=from_employee_id,
                shared_with=None,  # Public share
                expires_hours=168  # 7 days
            )
            
            if not success:
                # Clean up any previously created shares
                for cleanup_share_id in share_ids:
                    file_manager.delete_share(cleanup_share_id)
                raise Exception(f"Failed to create file share for {file_id}: {message}")
            
            share_ids.append(share_id)
            
            # Get file info
            file_info = file_manager.get_file_info(file_id)
            if file_info:
                file_infos.append({
                    'file_id': file_id,
                    'share_id': share_id,
                    'filename': file_info.original_filename,
                    'file_size': file_info.file_size,
                    'category': file_info.file_category.value
                })
        
        # Add file attachments info to message content
        if file_infos:
            content += f"\n\n📎 Attached Files ({len(file_infos)}):"
            for info in file_infos:
                content += f"\n   • {info['filename']} ({info['file_size'] / (1024*1024):.1f} MB)"
        
        # Send broadcast message
        message_id = self.send_message_detailed(
            sender_id=from_employee_id,
            sender_name=from_employee_id,
            recipient_id=None,
            recipient_name=None,
            subject=subject,
            message=content,
            priority=priority,
            is_broadcast=True
        )
        
        # Update message with attachment info
        if message_id in self.messages:
            self.messages[message_id].file_attachments = file_infos
            self._save_messages()
        
        # Update shares with message ID
        for share_id in share_ids:
            if share_id in file_manager.file_shares:
                file_manager.file_shares[share_id].message_id = message_id
        file_manager._save_shares()
        
        return message_id

    def send_message_with_folders(self, from_employee_id: str, to_employee_id: str, 
                                 subject: str, content: str, folder_ids: List[str],
                                 priority: str = "normal") -> str:
        """Send a message with folder attachments"""
        from models.folder_sharing import folder_manager
        
        share_ids = []
        folder_infos = []
        
        # Create folder shares for all folders
        for folder_id in folder_ids:
            success, share_id = folder_manager.share_folder(
                folder_id=folder_id,
                shared_by=from_employee_id,
                shared_with=[to_employee_id],
                expires_days=7
            )
            
            if not success:
                # Clean up any previously created shares
                for cleanup_share_id in share_ids:
                    # Note: folder_manager doesn't have delete_share method, 
                    # would need to add one or mark as inactive
                    pass
                raise Exception(f"Failed to create folder share for {folder_id}: {share_id}")
            
            share_ids.append(share_id)
            
            # Get folder info
            folder_info = folder_manager.get_folder_info(folder_id)
            if folder_info:
                folder_infos.append({
                    'folder_id': folder_id,
                    'share_id': share_id,
                    'folder_name': folder_info['folder_name'],
                    'total_files': folder_info['total_files'],
                    'total_size': folder_info['total_size'],
                    'compressed_size': folder_info['compressed_size']
                })
        
        # Add folder attachments info to message content
        if folder_infos:
            content += f"\n\n📁 Attached Folders ({len(folder_infos)}):"
            for info in folder_infos:
                size_mb = info['total_size'] / (1024*1024) if info['total_size'] else 0
                compressed_mb = info['compressed_size'] / (1024*1024) if info['compressed_size'] else 0
                content += f"\n   • {info['folder_name']} ({info['total_files']} files, {size_mb:.1f} MB"
                if compressed_mb:
                    content += f" → {compressed_mb:.1f} MB compressed"
                content += ")"
        
        # Send message
        message_id = self.send_message_detailed(
            sender_id=from_employee_id,
            sender_name=from_employee_id,
            recipient_id=to_employee_id,
            recipient_name=to_employee_id,
            subject=subject,
            message=content,
            priority=priority
        )
        
        # Update message with folder attachment info
        if message_id in self.messages:
            self.messages[message_id].folder_attachments = folder_infos
            self._save_messages()
        
        # Update shares with message ID
        for share_id in share_ids:
            if share_id in folder_manager.folder_shares:
                folder_manager.folder_shares[share_id].message_id = message_id
        folder_manager._save_shares()
        
        return message_id

    def broadcast_message_with_folders(self, from_employee_id: str, subject: str, 
                                     content: str, folder_ids: List[str],
                                     priority: str = "normal") -> str:
        """Broadcast a message with folder attachments to all employees"""
        from models.folder_sharing import folder_manager
        
        share_ids = []
        folder_infos = []
        
        # Create folder shares for all folders (broadcast = shared_with=None)
        for folder_id in folder_ids:
            success, share_id = folder_manager.share_folder(
                folder_id=folder_id,
                shared_by=from_employee_id,
                shared_with=None,  # None means broadcast to all
                expires_days=7
            )
            
            if not success:
                # Clean up any previously created shares
                for cleanup_share_id in share_ids:
                    pass  # Would need cleanup method
                raise Exception(f"Failed to create folder share for {folder_id}: {share_id}")
            
            share_ids.append(share_id)
            
            # Get folder info
            folder_info = folder_manager.get_folder_info(folder_id)
            if folder_info:
                folder_infos.append({
                    'folder_id': folder_id,
                    'share_id': share_id,
                    'folder_name': folder_info['folder_name'],
                    'total_files': folder_info['total_files'],
                    'total_size': folder_info['total_size'],
                    'compressed_size': folder_info['compressed_size']
                })
        
        # Add folder attachments info to message content
        if folder_infos:
            content += f"\n\n📁 Attached Folders ({len(folder_infos)}):"
            for info in folder_infos:
                size_mb = info['total_size'] / (1024*1024) if info['total_size'] else 0
                compressed_mb = info['compressed_size'] / (1024*1024) if info['compressed_size'] else 0
                content += f"\n   • {info['folder_name']} ({info['total_files']} files, {size_mb:.1f} MB"
                if compressed_mb:
                    content += f" → {compressed_mb:.1f} MB compressed"
                content += ")"
        
        # Send broadcast message
        message_id = self.send_message_detailed(
            sender_id=from_employee_id,
            sender_name=from_employee_id,
            recipient_id=None,
            recipient_name=None,
            subject=subject,
            message=content,
            priority=priority,
            is_broadcast=True
        )
        
        # Update message with folder attachment info
        if message_id in self.messages:
            self.messages[message_id].folder_attachments = folder_infos
            self._save_messages()
        
        # Update shares with message ID
        for share_id in share_ids:
            if share_id in folder_manager.folder_shares:
                folder_manager.folder_shares[share_id].message_id = message_id
        folder_manager._save_shares()
        
        return message_id

    def send_message_with_mixed_attachments(self, from_employee_id: str, to_employee_id: str,
                                          subject: str, content: str, 
                                          file_ids: List[str] = None, folder_ids: List[str] = None,
                                          priority: str = "normal") -> str:
        """Send a message with both file and folder attachments"""
        from models.medical_file_sharing import file_manager
        from models.folder_sharing import folder_manager as folder_mgr
        
        file_share_ids = []
        folder_share_ids = []
        file_infos = []
        folder_infos = []
        
        # Handle file attachments
        if file_ids:
            for file_id in file_ids:
                success, share_id, message = file_manager.create_file_share(
                    file_id=file_id,
                    shared_by=from_employee_id,
                    shared_with=to_employee_id,
                    expires_hours=168  # 7 days
                )
                
                if success:
                    file_share_ids.append(share_id)
                    file_info = file_manager.get_file_info(file_id)
                    if file_info:
                        file_infos.append({
                            'file_id': file_id,
                            'share_id': share_id,
                            'filename': file_info.original_filename,
                            'file_size': file_info.file_size,
                            'category': file_info.file_category.value
                        })
        
        # Handle folder attachments
        if folder_ids:
            for folder_id in folder_ids:
                success, share_id = folder_mgr.share_folder(
                    folder_id=folder_id,
                    shared_by=from_employee_id,
                    shared_with=[to_employee_id],
                    expires_days=7
                )
                
                if success:
                    folder_share_ids.append(share_id)
                    folder_info = folder_mgr.get_folder_info(folder_id)
                    if folder_info:
                        folder_infos.append({
                            'folder_id': folder_id,
                            'share_id': share_id,
                            'folder_name': folder_info['folder_name'],
                            'total_files': folder_info['total_files'],
                            'total_size': folder_info['total_size'],
                            'compressed_size': folder_info['compressed_size']
                        })
        
        # Add attachment info to message content
        if file_infos:
            content += f"\n\n📎 Attached Files ({len(file_infos)}):"
            for info in file_infos:
                content += f"\n   • {info['filename']} ({info['file_size'] / (1024*1024):.1f} MB)"
        
        if folder_infos:
            content += f"\n\n📁 Attached Folders ({len(folder_infos)}):"
            for info in folder_infos:
                size_mb = info['total_size'] / (1024*1024) if info['total_size'] else 0
                compressed_mb = info['compressed_size'] / (1024*1024) if info['compressed_size'] else 0
                content += f"\n   • {info['folder_name']} ({info['total_files']} files, {size_mb:.1f} MB"
                if compressed_mb:
                    content += f" → {compressed_mb:.1f} MB compressed"
                content += ")"
        
        # Send message
        message_id = self.send_message_detailed(
            sender_id=from_employee_id,
            sender_name=from_employee_id,
            recipient_id=to_employee_id,
            recipient_name=to_employee_id,
            subject=subject,
            message=content,
            priority=priority
        )
        
        # Update message with attachment info
        if message_id in self.messages:
            self.messages[message_id].file_attachments = file_infos
            self.messages[message_id].folder_attachments = folder_infos
            self._save_messages()
        
        # Update shares with message ID
        for share_id in file_share_ids:
            if share_id in file_manager.file_shares:
                file_manager.file_shares[share_id].message_id = message_id
        file_manager._save_shares()
        
        for share_id in folder_share_ids:
            if share_id in folder_mgr.folder_shares:
                folder_mgr.folder_shares[share_id].message_id = message_id
        folder_mgr._save_shares()
        
        return message_id

    def reply_to_message(self, original_message_id: str, from_employee_id: str, 
                        subject: str, content: str, priority: str = "normal",
                        file_ids: List[str] = None, folder_ids: List[str] = None) -> str:
        """Reply to an existing message"""
        # Get the original message
        if original_message_id not in self.messages:
            raise Exception("Original message not found")
        
        original_message = self.messages[original_message_id]
        
        # Determine recipient (reply to sender)
        to_employee_id = original_message.sender_id
        
        # Create conversation ID if it doesn't exist
        conversation_id = original_message.conversation_id
        if not conversation_id:
            conversation_id = f"CONV{datetime.now().strftime('%Y%m%d%H%M%S')}"
            # Update original message with conversation ID
            original_message.conversation_id = conversation_id
        
        # Prefix subject with "Re: " if not already present
        if not subject.startswith("Re: "):
            reply_subject = f"Re: {original_message.subject}"
        else:
            reply_subject = subject
        
        # Send reply with attachments if provided
        if file_ids or folder_ids:
            message_id = self.send_message_with_mixed_attachments(
                from_employee_id=from_employee_id,
                to_employee_id=to_employee_id,
                subject=reply_subject,
                content=content,
                file_ids=file_ids,
                folder_ids=folder_ids,
                priority=priority
            )
        else:
            message_id = self.send_message_detailed(
                sender_id=from_employee_id,
                sender_name=from_employee_id,
                recipient_id=to_employee_id,
                recipient_name=to_employee_id,
                subject=reply_subject,
                message=content,
                priority=priority
            )
        
        # Update reply with conversation threading info
        if message_id in self.messages:
            self.messages[message_id].reply_to_id = original_message_id
            self.messages[message_id].conversation_id = conversation_id
            self._save_messages()
        
        return message_id

    def get_conversation_messages(self, conversation_id: str) -> List[EmployeeMessage]:
        """Get all messages in a conversation thread"""
        conversation_messages = [
            msg for msg in self.messages.values() 
            if msg.conversation_id == conversation_id
        ]
        
        # Sort by creation date (oldest first for conversation flow)
        conversation_messages.sort(key=lambda x: x.created_at)
        return conversation_messages

    def get_message_replies(self, message_id: str) -> List[EmployeeMessage]:
        """Get all replies to a specific message"""
        replies = [
            msg for msg in self.messages.values() 
            if msg.reply_to_id == message_id
        ]
        
        # Sort by creation date (newest first)
        replies.sort(key=lambda x: x.created_at, reverse=True)
        return replies

    def get_conversation_summary(self, employee_id: str) -> List[dict]:
        """Get conversation summaries for an employee"""
        # Group messages by conversation
        conversations = {}
        
        for message in self.messages.values():
            # Only include messages relevant to this employee
            if (message.sender_id == employee_id or 
                message.recipient_id == employee_id or 
                message.is_broadcast):
                
                conv_id = message.conversation_id or message.id
                
                if conv_id not in conversations:
                    conversations[conv_id] = []
                conversations[conv_id].append(message)
        
        # Create conversation summaries
        summaries = []
        for conv_id, messages in conversations.items():
            messages.sort(key=lambda x: x.created_at, reverse=True)
            latest_message = messages[0]
            
            # Count unread messages in conversation
            unread_count = sum(1 for msg in messages 
                             if msg.status == MessageStatus.UNREAD and 
                             (msg.recipient_id == employee_id or msg.is_broadcast))
            
            # Get other participant(s)
            participants = set()
            for msg in messages:
                if msg.sender_id != employee_id:
                    participants.add(msg.sender_id)
                if msg.recipient_id and msg.recipient_id != employee_id:
                    participants.add(msg.recipient_id)
            
            summaries.append({
                'conversation_id': conv_id,
                'subject': latest_message.subject,
                'latest_message': latest_message.message[:100] + '...' if len(latest_message.message) > 100 else latest_message.message,
                'latest_timestamp': latest_message.created_at.isoformat(),
                'participants': list(participants),
                'message_count': len(messages),
                'unread_count': unread_count,
                'has_attachments': any(msg.file_attachments or msg.folder_attachments for msg in messages),
                'priority': latest_message.priority,
                'is_broadcast': latest_message.is_broadcast
            })
        
        # Sort by latest message timestamp
        summaries.sort(key=lambda x: x['latest_timestamp'], reverse=True)
        return summaries

    def mark_conversation_read(self, conversation_id: str, employee_id: str) -> bool:
        """Mark all messages in a conversation as read for an employee"""
        updated_count = 0
        
        for message in self.messages.values():
            if (message.conversation_id == conversation_id and
                message.status == MessageStatus.UNREAD and
                (message.recipient_id == employee_id or message.is_broadcast)):
                
                message.status = MessageStatus.READ
                message.read_at = datetime.now()
                updated_count += 1
        
        if updated_count > 0:
            self._save_messages()
        
        return updated_count > 0

    def forward_message(self, original_message_id: str, from_employee_id: str,
                       to_employee_id: str, additional_content: str = "",
                       priority: str = "normal") -> str:
        """Forward an existing message to another employee"""
        # Get the original message
        if original_message_id not in self.messages:
            raise Exception("Original message not found")
        
        original_message = self.messages[original_message_id]
        
        # Create forwarded content
        forward_content = f"--- Forwarded Message ---\n"
        forward_content += f"From: {original_message.sender_name}\n"
        forward_content += f"Date: {original_message.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        forward_content += f"Subject: {original_message.subject}\n\n"
        forward_content += original_message.message
        
        if additional_content:
            forward_content = f"{additional_content}\n\n{forward_content}"
        
        # Forward with original attachments if any
        file_ids = []
        folder_ids = []
        
        if original_message.file_attachments:
            file_ids = [att['file_id'] for att in original_message.file_attachments]
        
        if original_message.folder_attachments:
            folder_ids = [att['folder_id'] for att in original_message.folder_attachments]
        
        # Send forwarded message
        if file_ids or folder_ids:
            message_id = self.send_message_with_mixed_attachments(
                from_employee_id=from_employee_id,
                to_employee_id=to_employee_id,
                subject=f"Fwd: {original_message.subject}",
                content=forward_content,
                file_ids=file_ids,
                folder_ids=folder_ids,
                priority=priority
            )
        else:
            message_id = self.send_message_detailed(
                sender_id=from_employee_id,
                sender_name=from_employee_id,
                recipient_id=to_employee_id,
                recipient_name=to_employee_id,
                subject=f"Fwd: {original_message.subject}",
                message=forward_content,
                priority=priority
            )
        
        return message_id

# Global message manager instance
message_manager = EmployeeMessagingManager()
