import httpx

from app.schemas.analysis import MeetingAnalysisPayload


def build_slack_message(title: str, analysis: MeetingAnalysisPayload) -> dict:
    action_lines = [
        f"• *{item.title}*"
        f"{f' — {item.owner}' if item.owner else ''}"
        f"{f' · due {item.due_date}' if item.due_date else ''}"
        f" · priority: {item.priority}"
        for item in analysis.action_items
    ]
    decisions = (
        "\n".join(f"• {decision}" for decision in analysis.decisions)
        or "No decisions found."
    )
    actions = "\n".join(action_lines) or "No action items found."

    return {
        "text": f"Meeting summary: {title}",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": title[:150]}},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Summary*\n{analysis.summary}"},
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Decisions*\n{decisions}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Action Items*\n{actions}"}},
        ],
    }


async def send_to_slack(webhook_url: str, title: str, analysis: MeetingAnalysisPayload) -> None:
    message = build_slack_message(title, analysis)
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(webhook_url, json=message)
        response.raise_for_status()
