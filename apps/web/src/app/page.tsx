import { MeetingAssistant } from "@/components/MeetingAssistant";

export default function Home() {
  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Voice-to-Action Business Assistant</p>
        <h1>Turn meeting audio into business actions.</h1>
        <p className="subtitle">
          Upload a call recording, get a transcript, extract decisions and action items, then send a clean summary to Slack.
        </p>
      </section>
      <MeetingAssistant />
    </main>
  );
}
