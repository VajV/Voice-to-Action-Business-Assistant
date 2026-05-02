import httpx

from app.schemas.analysis import ActionItem


def build_card_description(item: ActionItem, meeting_title: str) -> str:
    return "\n".join(
        [
            f"Meeting: {meeting_title}",
            f"Owner: {item.owner or 'Not specified'}",
            f"Due: {item.due_date or 'Not specified'}",
            f"Priority: {item.priority}",
            f"Confidence: {round(item.confidence * 100)}%",
            "",
            item.context,
        ]
    )


async def create_trello_cards(
    api_key: str,
    token: str,
    list_id: str,
    meeting_title: str,
    action_items: list[ActionItem],
    api_base_url: str,
) -> int:
    async with httpx.AsyncClient(timeout=15) as client:
        for item in action_items:
            response = await client.post(
                f"{api_base_url}/cards",
                params={
                    "key": api_key,
                    "token": token,
                    "idList": list_id,
                    "name": item.title,
                    "desc": build_card_description(item, meeting_title),
                    "due": item.due_date,
                },
            )
            response.raise_for_status()

    return len(action_items)
