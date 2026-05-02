export type MeetingStatus =
  | "queued"
  | "processing"
  | "transcribed"
  | "analyzed"
  | "completed"
  | "failed";

export type Meeting = {
  id: string;
  title: string;
  source_type: "upload" | "youtube" | "microphone";
  language: string;
  status: MeetingStatus;
  progress: {
    stage: string;
    percent: number;
  };
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type ActionItem = {
  title: string;
  owner: string | null;
  due_date: string | null;
  priority: "low" | "medium" | "high";
  context: string;
  confidence: number;
};

export type MeetingResult = {
  transcript: string;
  summary: string;
  decisions: string[];
  action_items: ActionItem[];
  risks: string[];
  follow_up_questions: string[];
};
