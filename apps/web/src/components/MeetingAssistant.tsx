"use client";

import { FormEvent, useEffect, useState } from "react";
import { createMeeting, getMeeting, getMeetingResult, sendToSlack } from "@/lib/api";
import type { Meeting, MeetingResult } from "@/types/meeting";

const finalStatuses = new Set(["completed", "failed"]);

export function MeetingAssistant() {
  const [title, setTitle] = useState("Weekly business sync");
  const [language, setLanguage] = useState("auto");
  const [file, setFile] = useState<File | null>(null);
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [result, setResult] = useState<MeetingResult | null>(null);
  const [webhookUrl, setWebhookUrl] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSending, setIsSending] = useState(false);

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

    if (!file) {
      setError("Choose an MP3, WAV, M4A, or WEBM file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);
    formData.append("language", language);

    setIsUploading(true);

    try {
      const created = await createMeeting(formData);
      const nextMeeting = await getMeeting(created.id);
      setMeeting(nextMeeting);
      setResult(null);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed");
    } finally {
      setIsUploading(false);
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

  return (
    <div className="grid">
      <form className="card stack" onSubmit={handleUpload}>
        <div>
          <p className="eyebrow">MVP pipeline</p>
          <h2 className="section-title">Upload meeting audio</h2>
          <p className="muted">Supported now: MP3, WAV, M4A, WEBM. YouTube and microphone recording come next.</p>
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

        <div className="upload-box">
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
        </div>

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
                {result.action_items.map((item) => (
                  <article className="action-item" key={item.title}>
                    <strong>{item.title}</strong>
                    <span className="tag">{item.priority} · {Math.round(item.confidence * 100)}% confidence</span>
                    <span className="muted">
                      Owner: {item.owner ?? "Not specified"} · Due: {item.due_date ?? "Not specified"}
                    </span>
                    <span>{item.context}</span>
                  </article>
                ))}
              </div>
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
