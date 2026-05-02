import httpx

from app.schemas.analysis import MeetingAnalysisPayload


def build_notion_properties(title: str) -> dict:
    return {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": title,
                    }
                }
            ]
        }
    }


def build_notion_children(analysis: MeetingAnalysisPayload) -> list[dict]:
    action_lines = [
        f"{item.title}"
        f"{f' — {item.owner}' if item.owner else ''}"
        f"{f' · due {item.due_date}' if item.due_date else ''}"
        f" · priority: {item.priority}"
        for item in analysis.action_items
    ]
    sections = [
        ("Summary", [analysis.summary]),
        ("Decisions", analysis.decisions or ["No decisions found."]),
        ("Action Items", action_lines or ["No action items found."]),
        ("Risks", analysis.risks or ["No risks found."]),
        ("Follow-up Questions", analysis.follow_up_questions or ["No follow-up questions."]),
    ]

    children = []
    for heading, lines in sections:
        children.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": heading}}]},
            }
        )
        for line in lines:
            children.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line[:1900]}}],
                    },
                }
            )
    return children


async def send_to_notion(
    token: str,
    database_id: str,
    title: str,
    analysis: MeetingAnalysisPayload,
    api_base_url: str,
) -> None:
    payload = {
        "parent": {"database_id": database_id},
        "properties": build_notion_properties(title),
        "children": build_notion_children(analysis)[:100],
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(f"{api_base_url}/pages", headers=headers, json=payload)
        response.raise_for_status()
