"""
Supabase Storage helper functions
"""
import os
from typing import Optional, Dict, Any
from supabase_client import supabase_admin

class Storage:
    """Storage operations using Supabase Storage"""
    
    def __init__(self):
        self.storage = supabase_admin.storage
    
    async def upload_avatar(self, user_id: str, file_content: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """Upload user avatar to Supabase Storage"""
        try:
            file_path = f"{user_id}/{filename}"
            
            # Upload to avatars bucket
            result = self.storage.from_("avatars").upload(
                file_path,
                file_content,
                {
                    "content-type": content_type,
                    "upsert": "true"
                }
            )
            
            # Get public URL
            public_url = self.storage.from_("avatars").get_public_url(file_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "public_url": public_url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_question_attachment(
        self, 
        user_id: str, 
        question_id: str, 
        file_content: bytes, 
        filename: str, 
        content_type: str
    ) -> Dict[str, Any]:
        """Upload question attachment"""
        try:
            file_path = f"{user_id}/{question_id}/{filename}"
            
            # Upload to question-attachments bucket
            result = self.storage.from_("question-attachments").upload(
                file_path,
                file_content,
                {"content-type": content_type}
            )
            
            # Create signed URL (valid for 24 hours)
            signed_url_data = self.storage.from_("question-attachments").create_signed_url(
                file_path,
                86400  # 24 hours
            )
            
            return {
                "success": True,
                "file_path": file_path,
                "signed_url": signed_url_data.get("signedURL"),
                "filename": filename
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_answer_attachment(
        self,
        user_id: str,
        answer_id: str,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Upload answer attachment"""
        try:
            file_path = f"{user_id}/{answer_id}/{filename}"
            
            # Upload to answer-attachments bucket
            result = self.storage.from_("answer-attachments").upload(
                file_path,
                file_content,
                {"content-type": content_type}
            )
            
            # Create signed URL (valid for 24 hours)
            signed_url_data = self.storage.from_("answer-attachments").create_signed_url(
                file_path,
                86400  # 24 hours
            )
            
            return {
                "success": True,
                "file_path": file_path,
                "signed_url": signed_url_data.get("signedURL"),
                "filename": filename
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_question_attachments(self, user_id: str, question_id: str) -> list:
        """Get all attachments for a question with signed URLs"""
        try:
            folder_path = f"{user_id}/{question_id}"
            
            # List files in folder
            files = self.storage.from_("question-attachments").list(folder_path)
            
            attachments = []
            for file in files:
                # Create signed URL
                signed_url_data = self.storage.from_("question-attachments").create_signed_url(
                    f"{folder_path}/{file['name']}",
                    3600  # 1 hour
                )
                
                attachments.append({
                    "name": file["name"],
                    "size": file.get("metadata", {}).get("size", 0),
                    "url": signed_url_data.get("signedURL")
                })
            
            return attachments
        except Exception as e:
            print(f"Error getting attachments: {str(e)}")
            return []
    
    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete a file from storage"""
        try:
            self.storage.from_(bucket).remove([file_path])
            return True
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False

# Create singleton instance
storage = Storage()
