def test_upload_meeting_processes_demo_result(client):
    response = client.post(
        "/api/meetings",
        data={"title": "Demo Sync", "language": "ru"},
        files={"file": ("meeting.mp3", b"fake audio content", "audio/mpeg")},
    )

    assert response.status_code == 201
    meeting_id = response.json()["id"]

    status_response = client.get(f"/api/meetings/{meeting_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"

    result_response = client.get(f"/api/meetings/{meeting_id}/result")
    assert result_response.status_code == 200
    result = result_response.json()
    assert result["summary"]
    assert result["transcript"]
    assert result["action_items"]

    list_response = client.get("/api/meetings")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == meeting_id

    next_items = [
        {
            **result["action_items"][0],
            "title": "Updated action item",
            "owner": "VajV",
        }
    ]
    update_response = client.patch(
        f"/api/meetings/{meeting_id}/action-items",
        json={"action_items": next_items},
    )
    assert update_response.status_code == 200
    assert update_response.json()["action_items"][0]["title"] == "Updated action item"


def test_upload_rejects_unsupported_file_type(client):
    response = client.post(
        "/api/meetings",
        data={"title": "Bad file", "language": "auto"},
        files={"file": ("notes.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_youtube_import_rejects_non_youtube_url(client):
    response = client.post(
        "/api/meetings/youtube",
        json={"url": "https://example.com/video", "title": "Bad URL", "language": "auto"},
    )

    assert response.status_code == 422
