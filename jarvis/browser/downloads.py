import logging
from pathlib import Path
from typing import Dict, Any, Optional
from jarvis.browser.session import BrowserSession

logger = logging.getLogger("jarvis.browser.downloads")

class DownloadManager:
    """
    Manages safe file downloads via Playwright.
    """

    def __init__(self, session: BrowserSession, download_dir: Optional[Path] = None):
        self.session = session
        if download_dir is None:
            download_dir = Path("downloads").resolve()
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download_file(self, url_or_selector: str) -> Dict[str, Any]:
        page = self.session.get_active_page()
        try:
            with page.expect_download(timeout=30000) as download_info:
                if url_or_selector.startswith("http://") or url_or_selector.startswith("https://"):
                    page.evaluate(f"window.location.href = '{url_or_selector}'")
                else:
                    page.click(url_or_selector, timeout=5000)

            download = download_info.value
            target_path = self.download_dir / download.suggested_filename
            download.save_as(target_path)

            return {
                "success": True,
                "filename": download.suggested_filename,
                "path": str(target_path),
                "size_bytes": target_path.stat().st_size if target_path.exists() else 0
            }
        except Exception as e:
            logger.error(f"Download failed for '{url_or_selector}': {e}")
            return {
                "success": False,
                "target": url_or_selector,
                "error": str(e)
            }
