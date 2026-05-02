"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  createMeeting,
  createYouTubeMeeting,
  getMeeting,
  getMeetingResult,
  listMeetings,
  sendToNotion,
  sendToSlack,
  sendToTrello,
  updateActionItems
} from "@/lib/api";
import type { ActionItem, Meeting, MeetingResult } from "@/types/meeting";

const finalStatuses = new Set(["completed", "failed"]);

export function MeetingAssistant() {
  const [title, setTitle] = useState("Weekly business sync");
  const [language, setLanguage] = useState("auto");
  const [sourceMode, setSourceMode] = useState<"upload" | "youtube">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [result, setResult] = useState<MeetingResult | null>(null);
  const [editableActionItems, setEditableActionItems] = useState<ActionItem[]>([]);
  const [webhookUrl, setWebhookUrl] = useState("");
  const [notionToken, setNotionToken] = useState("");
  const [notionDatabaseId, setNotionDatabaseId] = useState("");
  const [trelloApiKey, setTrelloApiKey] = useState("");
  const [trelloToken, setTrelloToken] = useState("");
  const [trelloListId, setTrelloListId] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isSavingActions, setIsSavingActions] = useState(false);

  async function refreshMeetings() {
    const nextMeetings = await listMeetings();
    setMeetings(nextMeetings);
  }

  async function loadMeetingResult(nextMeeting: Meeting) {
    setMeeting(nextMeeting);

    if (nextMeeting.status === "completed") {
      const nextResult = await getMeetingResult(nextMeeting.id);
      setResult(nextResult);
      setEditableActionItems(nextResult.action_items);
    } else {
      setResult(null);
      setEditableActionItems([]);
    }
  }

  useEffect(() => {
    window.setTimeout(() => {
      refreshMeetings().catch(() => undefined);
    }, 0);
  }, []);

  useEffect(() => {
    if (!meeting || finalStatuses.has(meeting.status)) {
      return;
    }

    const timer = window.setInterval(async () => {
      try {
        const nextMeeting = await getMeeting(meeting.id);
        setMeeting(nextMeeting);

        if (nextMeeting.status === "completed") {
          const nextResult = await getMeetingResult(nextMeeting.id);
          setResult(nextResult);
          setEditableActionItems(nextResult.action_items);
          refreshMeetings().catch(() => undefined);
        }
      } catch (pollError) {
        setError(pollError instanceof Error ? pollError.message : "Polling failed");
      }
    }, 1500);

    return () => window.clearInterval(timer);
  }, [meeting]);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    if (sourceMode === "upload" && !file) {
      setError("Choose an MP3, WAV, M4A, or WEBM file first.");
      return;
    }

    setIsUploading(true);

    try {
      const created = sourceMode === "youtube"
        ? await createYouTubeMeeting({ url: youtubeUrl, title, language })
        : await createUploadMeeting();
      const nextMeeting = await getMeeting(created.id);
      await loadMeetingResult(nextMeeting);
      await refreshMeetings();
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  async function createUploadMeeting() {
    const formData = new FormData();
    if (file) {
      formData.append("file", file);
    }
    formData.append("title", title);
    formData.append("language", language);
    return createMeeting(formData);
  }

  function updateEditableActionItem(index: number, patch: Partial<ActionItem>) {
    setEditableActionItems((items) =>
      items.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item))
    );
  }

  async function handleSaveActionItems() {
    if (!meeting) {
      return;
    }

    setIsSavingActions(true);
    setError(null);
    setMessage(null);

    try {
      const nextResult = await updateActionItems(meeting.id, editableActionItems);
      setResult(nextResult);
      setEditableActionItems(nextResult.action_items);
      setMessage("Action items updated.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to update action items");
    } finally {
      setIsSavingActions(false);
    }
  }

  async function handleSlackSend() {
    if (!meeting || !webhookUrl) {
      setError("Add a Slack webhook URL first.");
      return;
    }

    setIsSending(true);
    setError(null);
    setMessage(null);

    try {
      const nextMessage = await sendToSlack(meeting.id, webhookUrl);
      setMessage(nextMessage);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Slack delivery failed");
    } finally {
      setIsSending(false);
    }
  }

  async function handleNotionSend() {
    if (!meeting || !notionToken || !notionDatabaseId) {
      setError("Add a Notion token and database ID first.");
      return;
    }

    await sendIntegration(() => sendToNotion(meeting.id, notionToken, notionDatabaseId), "Notion delivery failed");
  }

  async function handleTrelloSend() {
    if (!meeting || !trelloApiKey || !trelloToken || !trelloListId) {
      setError("Add Trello API key, token, and list ID first.");
      return;
    }

    await sendIntegration(
      () => sendToTrello(meeting.id, trelloApiKey, trelloToken, trelloListId),
      "Trello delivery failed"
    );
  }

  async function sendIntegration(send: () => Promise<string>, fallbackMessage: string) {
    setIsSending(true);
    setError(null);
    setMessage(null);

    try {
      const nextMessage = await send();
      setMessage(nextMessage);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : fallbackMessage);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="grid">
      <form className="card stack" onSubmit={handleUpload}>
        <div>
          <p className="eyebrow">MVP pipeline</p>
          <h2 className="section-title">Upload meeting audio</h2>
          <p className="muted">Supported now: audio upload and YouTube import. Microphone recording comes next.</p>
        </div>

        <div className="field">
          <label htmlFor="sourceMode">Source</label>
          <select id="sourceMode" value={sourceMode} onChange={(event) => setSourceMode(event.target.value as "upload" | "youtube")}>
            <option value="upload">Audio upload</option>
            <option value="youtube">YouTube URL</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="title">Meeting title</label>
          <input id="title" value={title} onChange={(event) => setTitle(event.target.value)} />
        </div>

        <div className="field">
          <label htmlFor="language">Language</label>
          <select id="language" value={language} onChange={(event) => setLanguage(event.target.value)}>
            <option value="auto">Auto</option>
            <option value="ru">Russian</option>
            <option value="en">English</option>
          </select>
        </div>

        {sourceMode === "upload" ? <div className="upload-box">
          <div className="field">
            <label htmlFor="file">Audio file</label>
            <input
              id="file"
              type="file"
              accept=".mp3,.wav,.m4a,.webm,audio/*"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </div>
          <p className="muted">{file ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB` : "No file selected"}</p>
        </div> : (
          <div className="field">
            <label htmlFor="youtubeUrl">YouTube URL</label>
            <input id="youtubeUrl" type="url" value={youtubeUrl} onChange={(event) => setYoutubeUrl(event.target.value)} placeholder="https://www.youtube.com/watch?v=..." />
          </div>
        )}

        <button className="button" disabled={isUploading} type="submit">
          {isUploading ? "Uploading..." : "Create action items"}
        </button>

        {meeting ? (
          <div className="stack">
            <span className="status">{meeting.status} · {meeting.progress.stage}</span>
            <div className="progress" aria-label="Processing progress">
              <span style={{ width: `${meeting.progress.percent}%` }} />
            </div>
            {meeting.error_message ? <p className="error">{meeting.error_message}</p> : null}
          </div>
        ) : null}

        {error ? <p className="error">{error}</p> : null}
        {message ? <p>{message}</p> : null}

        <div className="stack">
          <h3 className="section-title">Recent meetings</h3>
          {meetings.length === 0 ? <p className="muted">No meetings yet.</p> : null}
          {meetings.map((item) => (
            <button
              className="meeting-row"
              key={item.id}
              onClick={() => loadMeetingResult(item).catch((loadError) => setError(loadError instanceof Error ? loadError.message : "Failed to load meeting"))}
              type="button"
            >
              <span>{item.title}</span>
              <span>{item.status}</span>
            </button>
          ))}
        </div>
      </form>

      <section className="card stack">
        {!result ? (
          <div className="stack">
            <p className="eyebrow">Result preview</p>
            <h2 className="section-title">Transcript, summary, decisions, tasks</h2>
            <p className="muted">Upload a meeting to see extracted business outcomes here.</p>
          </div>
        ) : (
          <div className="stack">
            <div>
              <p className="eyebrow">AI summary</p>
              <h2 className="section-title">{meeting?.title}</h2>
              <p>{result.summary}</p>
            </div>

            <div>
              <h3 className="section-title">Decisions</h3>
              <ul className="list">
                {result.decisions.map((decision) => (
                  <li key={decision}>{decision}</li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="section-title">Action Items</h3>
              <div className="stack">
                {editableActionItems.map((item, index) => (
                  <article className="action-item" key={`${item.title}-${index}`}>
                    <input value={item.title} onChange={(event) => updateEditableActionItem(index, { title: event.target.value })} />
                    <span className="tag">{item.priority} · {Math.round(item.confidence * 100)}% confidence</span>
                    <div className="inline-fields">
                      <input placeholder="Owner" value={item.owner ?? ""} onChange={(event) => updateEditableActionItem(index, { owner: event.target.value || null })} />
                      <input placeholder="Due date" type="date" value={item.due_date ?? ""} onChange={(event) => updateEditableActionItem(index, { due_date: event.target.value || null })} />
                      <select value={item.priority} onChange={(event) => updateEditableActionItem(index, { priority: event.target.value as ActionItem["priority"] })}>
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    </div>
                    <textarea value={item.context} onChange={(event) => updateEditableActionItem(index, { context: event.target.value })} />
                  </article>
                ))}
              </div>
              <button className="secondary-button" disabled={isSavingActions} onClick={handleSaveActionItems} type="button">
                {isSavingActions ? "Saving..." : "Save edited action items"}
              </button>
            </div>

            <div className="field">
              <label htmlFor="webhook">Slack webhook URL</label>
              <input
                id="webhook"
                placeholder="https://hooks.slack.com/services/..."
                type="url"
                value={webhookUrl}
                onChange={(event) => setWebhookUrl(event.target.value)}
              />
            </div>
            <button className="secondary-button" disabled={isSending} onClick={handleSlackSend} type="button">
              {isSending ? "Sending..." : "Send summary to Slack"}
            </button>

            <div className="integration-grid">
              <div className="stack">
                <h3 className="section-title">Notion</h3>
                <input placeholder="Internal integration token" type="password" value={notionToken} onChange={(event) => setNotionToken(event.target.value)} />
                <input placeholder="Database ID" value={notionDatabaseId} onChange={(event) => setNotionDatabaseId(event.target.value)} />
                <button className="secondary-button" disabled={isSending} onClick={handleNotionSend} type="button">Send to Notion</button>
              </div>
              <div className="stack">
                <h3 className="section-title">Trello</h3>
                <input placeholder="API key" type="password" value={trelloApiKey} onChange={(event) => setTrelloApiKey(event.target.value)} />
                <input placeholder="Token" type="password" value={trelloToken} onChange={(event) => setTrelloToken(event.target.value)} />
                <input placeholder="List ID" value={trelloListId} onChange={(event) => setTrelloListId(event.target.value)} />
                <button className="secondary-button" disabled={isSending} onClick={handleTrelloSend} type="button">Create Trello cards</button>
              </div>
            </div>

            <div>
              <h3 className="section-title">Transcript</h3>
              <div className="transcript">{result.transcript}</div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
