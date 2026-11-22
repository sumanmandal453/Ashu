export type AssignmentStatus =
  | "new" | "pending" | "in_progress" | "ai_generated" | "awaiting_approval"
  | "submitted" | "verification_pending" | "overdue";
export type Priority = "low" | "medium" | "high";

export interface User { id: string; name: string; email: string; college: string; department: string; semester: number; rollNumber: string }
export interface Subject { id: string; name: string; code: string; semester: number; faculty: string }
export interface Assignment {
  id: string; title: string; subjectId: string; description: string; questions: string[];
  faculty: string; totalMarks: number; createdAt: string; deadline: string;
  sourcePlatform: string; attachments: string[]; status: AssignmentStatus; priority: Priority;
}
export interface GeneratedDocument { id: string; assignmentId: string; fileName: string; format: "pdf" | "docx"; generatedAt: string; approvalStatus: "draft" | "awaiting" | "approved"; fileStatus: "mock" | "ready" | "failed" }
export interface Submission { id: string; assignmentId: string; documentId: string; submittedAt?: string; status: "uploading" | "verification_pending" | "submitted" | "failed" | "retry_required"; confirmationReference?: string; errorMessage?: string }
export interface Notification { id: string; title: string; message: string; type: string; createdAt: string; readStatus: boolean }
export interface StudyMaterial { id: string; fileName: string; subjectId: string; fileType: string; uploadedAt: string; processingStatus: "queued" | "indexed" | "failed" }
export interface Integration { id: string; provider: string; connectionStatus: "not_connected" | "connecting" | "connected" | "synchronizing" | "error" | "permission_required"; lastSyncedAt?: string; permissionStatus: string }
