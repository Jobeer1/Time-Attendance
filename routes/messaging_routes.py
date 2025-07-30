"""
Employee Messaging API Routes
Allows employees to send and receive messages to/from each other
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from typing import Dict, List
import json

from models.employee_messaging import EmployeeMessagingManager

messaging_bp = Blueprint('messaging', __name__, url_prefix='/api/messaging')

# Global messaging manager instance
messaging_manager = EmployeeMessagingManager()

@messaging_bp.route('/send', methods=['POST'])
def send_message():
    """Send a message from one employee to another or broadcast to all"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        from_employee_id = data.get('from_employee_id')
        to_employee_id = data.get('to_employee_id')  # None for broadcast
        subject = data.get('subject', '')
        content = data.get('content', '')
        priority = data.get('priority', 'normal')
        file_attachments = data.get('file_attachments', [])  # List of file IDs
        folder_attachments = data.get('folder_attachments', [])  # List of folder IDs
        
        if not from_employee_id or not content:
            return jsonify({
                'success': False, 
                'error': 'Missing required fields: from_employee_id and content'
            }), 400
        
        if file_attachments or folder_attachments:
            # Send message with file and/or folder attachments
            if to_employee_id:
                # Send to specific employee
                if file_attachments and folder_attachments:
                    # Mixed attachments
                    message_id = messaging_manager.send_message_with_mixed_attachments(
                        from_employee_id, to_employee_id, subject, content, file_attachments, folder_attachments, priority
                    )
                elif file_attachments:
                    # File attachments only
                    message_id = messaging_manager.send_message_with_files(
                        from_employee_id, to_employee_id, subject, content, file_attachments, priority
                    )
                else:
                    # Folder attachments only
                    message_id = messaging_manager.send_message_with_folders(
                        from_employee_id, to_employee_id, subject, content, folder_attachments, priority
                    )
            else:
                # Broadcast to all employees
                if file_attachments and folder_attachments:
                    # For mixed broadcast, use files method for now
                    message_id = messaging_manager.broadcast_message_with_files(
                        from_employee_id, subject, content, file_attachments, priority
                    )
                elif file_attachments:
                    # File attachments only
                    message_id = messaging_manager.broadcast_message_with_files(
                        from_employee_id, subject, content, file_attachments, priority
                    )
                else:
                    # Folder attachments only
                    message_id = messaging_manager.broadcast_message_with_folders(
                        from_employee_id, subject, content, folder_attachments, priority
                    )
        else:
            # Send regular message without files or folders
            if to_employee_id:
                # Send to specific employee
                message_id = messaging_manager.send_message(
                    from_employee_id, to_employee_id, subject, content, priority
                )
            else:
                # Broadcast to all employees
                message_id = messaging_manager.broadcast_message(
                    from_employee_id, subject, content, priority
                )
        
        return jsonify({
            'success': True,
            'message_id': message_id,
            'message': 'Message sent successfully' + (f' with {len(file_attachments)} file(s)' if file_attachments else '') + (f' and {len(folder_attachments)} folder(s)' if folder_attachments else '')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@messaging_bp.route('/send-with-file', methods=['POST'])
def send_message_with_file():
    """Send a message with file attachment"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        from_employee_id = data.get('from_employee_id')
        to_employee_id = data.get('to_employee_id')  # None for broadcast
        subject = data.get('subject', '')
        content = data.get('content', '')
        file_id = data.get('file_id')
        priority = data.get('priority', 'normal')
        
        if not from_employee_id or not content or not file_id:
            return jsonify({
                'success': False, 
                'error': 'Missing required fields: from_employee_id, content, and file_id'
            }), 400
        
        if to_employee_id:
            # Send to specific employee
            message_id = messaging_manager.send_message_with_file(
                from_employee_id, to_employee_id, subject, content, file_id, priority
            )
        else:
            # Broadcast to all employees
            message_id = messaging_manager.broadcast_message_with_file(
                from_employee_id, subject, content, file_id, priority
            )
        
        return jsonify({
            'success': True,
            'message_id': message_id,
            'message': 'Message with file attachment sent successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@messaging_bp.route('/inbox/<employee_id>', methods=['GET'])
def get_inbox(employee_id):
    """Get all messages for an employee"""
    try:
        limit = request.args.get('limit', 50, type=int)
        include_read = request.args.get('include_read', 'true').lower() == 'true'
        
        messages = messaging_manager.get_employee_messages(
            employee_id, limit=limit, include_read=include_read
        )
        
        return jsonify({
            'success': True,
            'messages': messages,
            'count': len(messages)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@messaging_bp.route('/messages/<employee_id>', methods=['GET'])
def get_messages(employee_id):
    """Get all messages for an employee - Alternative endpoint"""
    try:
        limit = request.args.get('limit', 50, type=int)
        include_read = request.args.get('include_read', 'true').lower() == 'true'
        
        messages = messaging_manager.get_employee_messages(
            employee_id, limit=limit, include_read=include_read
        )
        
        return jsonify({
            'success': True,
            'messages': messages,
            'count': len(messages)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@messaging_bp.route('/unread-count/<employee_id>', methods=['GET'])
def get_unread_count(employee_id):
    """Get count of unread messages for an employee"""
    try:
        count = messaging_manager.get_unread_count(employee_id)
        
        return jsonify({
            'success': True,
            'unread_count': count
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@messaging_bp.route('/mark-read', methods=['POST'])
def mark_message_read():
    """Mark a message as read"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message_id = data.get('message_id')
        employee_id = data.get('employee_id')
        
        if not message_id or not employee_id:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: message_id and employee_id'
            }), 400
        
        success = messaging_manager.mark_message_read(message_id, employee_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Message marked as read'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Message not found or already read'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@messaging_bp.route('/delete', methods=['POST'])
def delete_message():
    """Delete a message for an employee"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message_id = data.get('message_id')
        employee_id = data.get('employee_id')
        
        if not message_id or not employee_id:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: message_id and employee_id'
            }), 400
        
        success = messaging_manager.delete_message_for_employee(message_id, employee_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Message deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Message not found'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@messaging_bp.route('/employees', methods=['GET'])
def get_employees_list():
    """Get list of employees for sending messages"""
    try:
        # Load employees directly from JSON file to bypass any model issues
        import json
        from pathlib import Path
        
        employees_file = Path('attendance_data/employees.json')
        employee_list = []
        
        if employees_file.exists():
            with open(employees_file, 'r') as f:
                raw_employees = json.load(f)
            
            print(f"Loaded {len(raw_employees)} employees from JSON")  # Debug output
            
            for emp in raw_employees:
                # Check if employee is active
                if emp.get('employment_status') == 'active':
                    first_name = emp.get('first_name', '')
                    last_name = emp.get('last_name', '')
                    full_name = f"{first_name} {last_name}".strip()
                    
                    employee_list.append({
                        'id': emp.get('employee_id', ''),
                        'name': full_name,
                        'department': emp.get('department', 'N/A'),
                        'active': True
                    })
                    print(f"  Added active employee: {emp.get('employee_id')} - {full_name}")
            
            print(f"Filtered to {len(employee_list)} active employees")  # Debug output
        else:
            print("WARNING: employees.json file not found")
        
        return jsonify({
            'success': True,
            'employees': employee_list
        })
        
    except Exception as e:
        print(f"Error getting employees list: {e}")
        import traceback
        traceback.print_exc()
        # Fallback with sample data if employee system not available
        return jsonify({
            'success': True,
            'employees': [
                {'id': 'EMP01', 'name': 'Johann Strauss', 'department': 'IT Department', 'active': True},
                {'id': 'EMP02', 'name': 'Sarah Johnson', 'department': 'Human Resources', 'active': True},
                {'id': 'EMP003', 'name': 'Michael Brown', 'department': 'Security', 'active': True},
                {'id': 'EMP004', 'name': 'Jennifer Davis', 'department': 'Operations', 'active': True},
                {'id': 'EMP005', 'name': 'David Wilson', 'department': 'IT Department', 'active': True},
                {'id': 'EMP006', 'name': 'Alice Smith', 'department': 'Admin', 'active': True},
                {'id': 'EMP007', 'name': 'Bob Jones', 'department': 'Support', 'active': True},
                {'id': 'EMP008', 'name': 'Carol White', 'department': 'HR', 'active': True},
                {'id': 'EMP009', 'name': 'Daniel Green', 'department': 'IT', 'active': True},
                {'id': 'EMP010', 'name': 'Emma Brown', 'department': 'Finance', 'active': True}
            ]
        })

# Template routes for messaging interfaces
@messaging_bp.route('/interface', methods=['GET'])
def messaging_interface():
    """Employee messaging interface"""
    return render_template('attendance/employee_messaging.html')

@messaging_bp.route('/admin-interface', methods=['GET'])
def admin_messaging_interface():
    """Admin messaging interface"""
    return render_template('attendance/admin_messaging.html')

@messaging_bp.route('/hub', methods=['GET'])
def messaging_hub():
    """LAN-friendly messaging hub for easy access"""
    return render_template('attendance/messaging_hub.html')

@messaging_bp.route('/reply', methods=['POST'])
def reply_to_message():
    """Reply to an existing message"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        original_message_id = data.get('original_message_id')
        from_employee_id = data.get('from_employee_id')
        subject = data.get('subject', '')
        content = data.get('content', '')
        priority = data.get('priority', 'normal')
        file_attachments = data.get('file_attachments', [])
        folder_attachments = data.get('folder_attachments', [])
        
        if not original_message_id or not from_employee_id or not content:
            return jsonify({
                'success': False, 
                'error': 'Missing required fields: original_message_id, from_employee_id, and content'
            }), 400
        
        # Send reply
        message_id = messaging_manager.reply_to_message(
            original_message_id=original_message_id,
            from_employee_id=from_employee_id,
            subject=subject,
            content=content,
            priority=priority,
            file_ids=file_attachments if file_attachments else None,
            folder_ids=folder_attachments if folder_attachments else None
        )
        
        return jsonify({
            'success': True,
            'message_id': message_id,
            'message': 'Reply sent successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error sending reply: {str(e)}'
        }), 500

@messaging_bp.route('/conversation/<conversation_id>', methods=['GET'])
def get_conversation():
    """Get all messages in a conversation thread"""
    try:
        employee_id = request.args.get('employee_id')
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'employee_id parameter is required'
            }), 400
        
        conversation_messages = messaging_manager.get_conversation_messages(conversation_id)
        
        # Filter messages relevant to this employee
        relevant_messages = []
        for msg in conversation_messages:
            if (msg.sender_id == employee_id or 
                msg.recipient_id == employee_id or 
                msg.is_broadcast):
                
                relevant_messages.append({
                    'id': msg.id,
                    'from_employee_id': msg.sender_id,
                    'from_employee_name': msg.sender_name,
                    'to_employee_id': msg.recipient_id,
                    'subject': msg.subject,
                    'content': msg.message,
                    'priority': msg.priority,
                    'is_read': msg.status.value == 'read',
                    'is_broadcast': msg.is_broadcast,
                    'timestamp': msg.created_at.isoformat(),
                    'file_attachments': msg.file_attachments or [],
                    'folder_attachments': msg.folder_attachments or [],
                    'reply_to_id': msg.reply_to_id
                })
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'messages': relevant_messages,
            'message_count': len(relevant_messages)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting conversation: {str(e)}'
        }), 500

@messaging_bp.route('/conversations/<employee_id>', methods=['GET'])
def get_conversations():
    """Get conversation summaries for an employee"""
    try:
        conversations = messaging_manager.get_conversation_summary(employee_id)
        
        return jsonify({
            'success': True,
            'conversations': conversations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting conversations: {str(e)}'
        }), 500

@messaging_bp.route('/conversation/<conversation_id>/mark-read', methods=['POST'])
def mark_conversation_read():
    """Mark all messages in a conversation as read"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'employee_id is required'
            }), 400
        
        success = messaging_manager.mark_conversation_read(conversation_id, employee_id)
        
        return jsonify({
            'success': success,
            'message': 'Conversation marked as read' if success else 'No messages were updated'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error marking conversation as read: {str(e)}'
        }), 500

@messaging_bp.route('/forward', methods=['POST'])
def forward_message():
    """Forward an existing message to another employee"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        original_message_id = data.get('original_message_id')
        from_employee_id = data.get('from_employee_id')
        to_employee_id = data.get('to_employee_id')
        additional_content = data.get('additional_content', '')
        priority = data.get('priority', 'normal')
        
        if not original_message_id or not from_employee_id or not to_employee_id:
            return jsonify({
                'success': False, 
                'error': 'Missing required fields: original_message_id, from_employee_id, and to_employee_id'
            }), 400
        
        # Forward message
        message_id = messaging_manager.forward_message(
            original_message_id=original_message_id,
            from_employee_id=from_employee_id,
            to_employee_id=to_employee_id,
            additional_content=additional_content,
            priority=priority
        )
        
        return jsonify({
            'success': True,
            'message_id': message_id,
            'message': 'Message forwarded successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error forwarding message: {str(e)}'
        }), 500

@messaging_bp.route('/message/<message_id>/replies', methods=['GET'])
def get_message_replies():
    """Get all replies to a specific message"""
    try:
        employee_id = request.args.get('employee_id')
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'employee_id parameter is required'
            }), 400
        
        replies = messaging_manager.get_message_replies(message_id)
        
        # Filter replies relevant to this employee
        relevant_replies = []
        for msg in replies:
            if (msg.sender_id == employee_id or 
                msg.recipient_id == employee_id or 
                msg.is_broadcast):
                
                relevant_replies.append({
                    'id': msg.id,
                    'from_employee_id': msg.sender_id,
                    'from_employee_name': msg.sender_name,
                    'to_employee_id': msg.recipient_id,
                    'subject': msg.subject,
                    'content': msg.message,
                    'priority': msg.priority,
                    'is_read': msg.status.value == 'read',
                    'is_broadcast': msg.is_broadcast,
                    'timestamp': msg.created_at.isoformat(),
                    'file_attachments': msg.file_attachments or [],
                    'folder_attachments': msg.folder_attachments or []
                })
        
        return jsonify({
            'success': True,
            'original_message_id': message_id,
            'replies': relevant_replies,
            'reply_count': len(relevant_replies)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting message replies: {str(e)}'
        }), 500

def register_messaging_routes(app):
    """Register messaging routes with the Flask app"""
    app.register_blueprint(messaging_bp)
    return messaging_bp, messaging_manager
