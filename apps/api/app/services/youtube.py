from pathlib import Path
from uuid import uuid4

from app.core.config import settings


class YouTubeImportError(ValueError):
    pass


def download_youtube_audio(url: str) -> Path:
    if not url.startswith(("https://www.youtube.com/", "https://youtube.com/", "https://youtu.be/")):
        raise YouTubeImportError("Only YouTube URLs are supported")

    try:
        from yt_dlp import YoutubeDL
    except ImportError as error:
        raise YouTubeImportError("yt-dlp is not installed") from error

    settings.local_storage_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(settings.local_storage_dir / f"{uuid4().hex}.%(ext)s")
    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
            downloaded_path = Path(downloader.prepare_filename(info)).with_suffix(".mp3")
    except Exception as error:
        raise YouTubeImportError("Failed to download YouTube audio") from error

    if not downloaded_path.exists():
        raise YouTubeImportError("Downloaded YouTube audio file was not found")

    return downloaded_path
