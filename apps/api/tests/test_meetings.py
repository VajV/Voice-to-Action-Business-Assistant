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


def test_upload_rejects_unsupported_file_type(client):
    response = client.post(
        "/api/meetings",
        data={"title": "Bad file", "language": "auto"},
        files={"file": ("notes.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
