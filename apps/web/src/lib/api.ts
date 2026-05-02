import type { Meeting, MeetingResult } from "@/types/meeting";

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

export async function getMeeting(id: string): Promise<Meeting> {
  const response = await fetch(`${API_BASE_URL}/api/meetings/${id}`);

  if (!response.ok) {
    throw new Error("Failed to load meeting status");
  }

  return response.json();
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
