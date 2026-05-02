import type { ActionItem, Meeting, MeetingResult } from "@/types/meeting";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function createMeeting(formData: FormData): Promise<{ id: string; status: string; title: string }> {
  const response = await fetch(`${API_BASE_URL}/api/meetings`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "Failed to upload meeting audio");
  }

  return response.json();
}

export async function createYouTubeMeeting(payload: { url: string; title: string; language: string }): Promise<{ id: string; status: string; title: string }> {
  const response = await fetch(`${API_BASE_URL}/api/meetings/youtube`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.detail ?? "Failed to import YouTube audio");
  }

  return body;
}

export async function listMeetings(): Promise<Meeting[]> {
  const response = await fetch(`${API_BASE_URL}/api/meetings`);

  if (!response.ok) {
    throw new Error("Failed to load meetings");
  }

  return response.json();
}

export async function getMeeting(id: string): Promise<Meeting> {
  const response = await fetch(`${API_BASE_URL}/api/meetings/${id}`);

  if (!response.ok) {
    throw new Error("Failed to load meeting status");
  }

  return response.json();
}

export async function updateActionItems(id: string, actionItems: ActionItem[]): Promise<MeetingResult> {
  const response = await fetch(`${API_BASE_URL}/api/meetings/${id}/action-items`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ action_items: actionItems })
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.detail ?? "Failed to update action items");
  }

  return body;
}

export async function getMeetingResult(id: string): Promise<MeetingResult> {
  const response = await fetch(`${API_BASE_URL}/api/meetings/${id}/result`);

  if (!response.ok) {
    throw new Error("Meeting result is not ready yet");
  }

  return response.json();
}

export async function sendToSlack(id: string, webhookUrl: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/meetings/${id}/send/slack`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ webhook_url: webhookUrl })
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.detail ?? "Slack delivery failed");
  }

  return body.message;
}

export async function sendToNotion(id: string, token: string, databaseId: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/meetings/${id}/send/notion`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ token, database_id: databaseId })
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.detail ?? "Notion delivery failed");
  }

  return body.message;
}

export async function sendToTrello(id: string, apiKey: string, token: string, listId: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/meetings/${id}/send/trello`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ api_key: apiKey, token, list_id: listId })
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.detail ?? "Trello delivery failed");
  }

  return body.message;
}
