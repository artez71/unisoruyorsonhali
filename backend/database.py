"""
Database helper functions for Supabase
"""
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from supabase_client import supabase_admin
from postgrest.exceptions import APIError

class Database:
    """Database operations using Supabase"""
    
    def __init__(self):
        self.db = supabase_admin
    
    # User Operations
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        try:
            result = self.db.table("users").insert(user_data).execute()
            return result.data[0] if result.data else None
        except APIError as e:
            raise Exception(f"Error creating user: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            result = self.db.table("users").select("*").eq("email", email).execute()
            return result.data[0] if result.data else None
        except APIError:
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            result = self.db.table("users").select("*").eq("username", username).execute()
            return result.data[0] if result.data else None
        except APIError:
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            result = self.db.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except APIError:
            return None
    
    async def update_user_last_question(self, user_id: str):
        """Update user's last question timestamp"""
        try:
            self.db.table("users").update({
                "last_question_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
        except APIError:
            pass
    
    async def update_user_last_answer(self, user_id: str):
        """Update user's last answer timestamp"""
        try:
            self.db.table("users").update({
                "last_answer_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
        except APIError:
            pass
    
    # Question Operations
    async def create_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new question"""
        try:
            result = self.db.table("questions").insert(question_data).execute()
            return result.data[0] if result.data else None
        except APIError as e:
            raise Exception(f"Error creating question: {str(e)}")
    
    async def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get question by ID"""
        try:
            result = self.db.table("questions").select("*").eq("id", question_id).execute()
            return result.data[0] if result.data else None
        except APIError:
            return None
    
    async def get_questions(self, limit: int = 50, offset: int = 0, 
                           category: str = None, search: str = None) -> List[Dict[str, Any]]:
        """Get questions with optional filtering"""
        try:
            query = self.db.table("questions").select("*")
            
            if category:
                query = query.eq("category", category)
            
            if search:
                query = query.or_(f"title.ilike.%{search}%,content.ilike.%{search}%")
            
            result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            return result.data if result.data else []
        except APIError:
            return []
    
    async def update_question(self, question_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a question"""
        try:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            self.db.table("questions").update(update_data).eq("id", question_id).execute()
            return True
        except APIError:
            return False
    
    async def delete_question(self, question_id: str) -> bool:
        """Delete a question"""
        try:
            self.db.table("questions").delete().eq("id", question_id).execute()
            return True
        except APIError:
            return False
    
    async def increment_question_views(self, question_id: str):
        """Increment question view count"""
        try:
            question = await self.get_question_by_id(question_id)
            if question:
                self.db.table("questions").update({
                    "view_count": question.get("view_count", 0) + 1
                }).eq("id", question_id).execute()
        except APIError:
            pass
    
    # Answer Operations
    async def create_answer(self, answer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new answer"""
        try:
            result = self.db.table("answers").insert(answer_data).execute()
            return result.data[0] if result.data else None
        except APIError as e:
            raise Exception(f"Error creating answer: {str(e)}")
    
    async def get_answers_by_question(self, question_id: str) -> List[Dict[str, Any]]:
        """Get all answers for a question"""
        try:
            result = self.db.table("answers").select("*").eq(
                "question_id", question_id
            ).order("created_at", desc=False).execute()
            return result.data if result.data else []
        except APIError:
            return []
    
    async def get_answer_by_id(self, answer_id: str) -> Optional[Dict[str, Any]]:
        """Get answer by ID"""
        try:
            result = self.db.table("answers").select("*").eq("id", answer_id).execute()
            return result.data[0] if result.data else None
        except APIError:
            return None
    
    async def update_answer(self, answer_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an answer"""
        try:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            self.db.table("answers").update(update_data).eq("id", answer_id).execute()
            return True
        except APIError:
            return False
    
    async def delete_answer(self, answer_id: str) -> bool:
        """Delete an answer"""
        try:
            self.db.table("answers").delete().eq("id", answer_id).execute()
            return True
        except APIError:
            return False
    
    # Notification Operations
    async def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new notification"""
        try:
            result = self.db.table("notifications").insert(notification_data).execute()
            return result.data[0] if result.data else None
        except APIError as e:
            print(f"Error creating notification: {str(e)}")
            return None
    
    async def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's notifications"""
        try:
            result = self.db.table("notifications").select("*").eq(
                "user_id", user_id
            ).order("created_at", desc=True).limit(limit).execute()
            return result.data if result.data else []
        except APIError:
            return []
    
    async def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            self.db.table("notifications").update({
                "is_read": True
            }).eq("id", notification_id).execute()
            return True
        except APIError:
            return False
    
    # Like Operations
    async def toggle_question_like(self, question_id: str, user_id: str) -> bool:
        """Toggle question like"""
        try:
            # Check if already liked
            result = self.db.table("question_likes").select("*").eq(
                "question_id", question_id
            ).eq("user_id", user_id).execute()
            
            if result.data:
                # Unlike
                self.db.table("question_likes").delete().eq(
                    "question_id", question_id
                ).eq("user_id", user_id).execute()
                
                # Decrement like count
                question = await self.get_question_by_id(question_id)
                if question:
                    self.db.table("questions").update({
                        "like_count": max(0, question.get("like_count", 0) - 1)
                    }).eq("id", question_id).execute()
                return False
            else:
                # Like
                self.db.table("question_likes").insert({
                    "question_id": question_id,
                    "user_id": user_id
                }).execute()
                
                # Increment like count
                question = await self.get_question_by_id(question_id)
                if question:
                    self.db.table("questions").update({
                        "like_count": question.get("like_count", 0) + 1
                    }).eq("id", question_id).execute()
                return True
        except APIError:
            return False
    
    # Leaderboard
    async def get_leaderboard(self, limit: int = 7) -> List[Dict[str, Any]]:
        """Get leaderboard - top users by question and answer count"""
        try:
            # Get all users
            users_result = self.db.table("users").select(
                "id, username, university, faculty, department"
            ).execute()
            
            if not users_result.data:
                return []
            
            leaderboard = []
            for user in users_result.data:
                user_id = user["id"]
                
                # Count questions
                q_result = self.db.table("questions").select(
                    "id", count="exact"
                ).eq("author_id", user_id).execute()
                question_count = q_result.count if q_result.count else 0
                
                # Count answers
                a_result = self.db.table("answers").select(
                    "id", count="exact"
                ).eq("author_id", user_id).execute()
                answer_count = a_result.count if a_result.count else 0
                
                total_contributions = question_count + answer_count
                
                if total_contributions > 0:
                    leaderboard.append({
                        "username": user["username"],
                        "university": user["university"],
                        "faculty": user["faculty"],
                        "department": user["department"],
                        "question_count": question_count,
                        "answer_count": answer_count,
                        "total_contributions": total_contributions
                    })
            
            # Sort by total contributions, then by username
            leaderboard.sort(key=lambda x: (-x["total_contributions"], x["username"]))
            
            # Return top 7
            return leaderboard[:limit]
        except APIError as e:
            print(f"Error getting leaderboard: {str(e)}")
            return []
    
    # User Profile
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get complete user profile with stats"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Get question count
            q_result = self.db.table("questions").select("id", count="exact").eq(
                "author_id", user_id
            ).execute()
            question_count = q_result.count if q_result.count else 0
            
            # Get answer count
            a_result = self.db.table("answers").select("id", count="exact").eq(
                "author_id", user_id
            ).execute()
            answer_count = a_result.count if a_result.count else 0
            
            # Get recent questions
            recent_questions = await self.get_questions(limit=5, offset=0)
            recent_questions = [q for q in recent_questions if q["author_id"] == user_id][:5]
            
            # Get recent answers
            a_recent = self.db.table("answers").select("*").eq(
                "author_id", user_id
            ).order("created_at", desc=True).limit(5).execute()
            recent_answers = a_recent.data if a_recent.data else []
            
            return {
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "university": user["university"],
                    "faculty": user["faculty"],
                    "department": user["department"],
                    "created_at": user["created_at"]
                },
                "stats": {
                    "question_count": question_count,
                    "answer_count": answer_count
                },
                "recent_questions": recent_questions,
                "recent_answers": recent_answers
            }
        except APIError:
            return None

# Create singleton instance
db = Database()
