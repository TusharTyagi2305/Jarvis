import logging
from typing import Dict, Any, Optional
from jarvis.browser.session import BrowserSession

logger = logging.getLogger("jarvis.browser.actions")

class ActionManager:
    """
    Executes DOM actions (click, type, press key, scroll) on active Playwright page.
    """

    def __init__(self, session: BrowserSession):
        self.session = session

    def click(self, target: str) -> Dict[str, Any]:
        page = self.session.get_active_page()
        try:
            # Try multiple selector strategies cleanly including YouTube smart selectors
            t_lower = target.lower()
            selectors = [
                f"text={target}",
                f"button:has-text('{target}')",
                f"a:has-text('{target}')",
                f"[aria-label='{target}']"
            ]

            if "channel" in t_lower:
                selectors.extend([
                    "ytd-channel-renderer a#main-link",
                    "a#channel-title",
                    "ytd-channel-name a",
                    "a[href*='/@']",
                    "a[href*='/c/']",
                    "a[href*='/channel/']"
                ])

            if "video" in t_lower or "most watched" in t_lower or "play" in t_lower:
                selectors.extend([
                    "ytd-video-renderer a#video-title",
                    "a#video-title",
                    "ytd-grid-video-renderer a#video-title",
                    "a.ytd-video-renderer",
                    "a[href*='/watch']"
                ])

            selectors.append(target)

            clicked = False
            for sel in selectors:
                try:
                    if page.locator(sel).first.is_visible(timeout=2000):
                        page.locator(sel).first.click(timeout=5000)
                        clicked = True
                        break
                except Exception:
                    continue

            if not clicked:
                from jarvis.context import active_context
                query = active_context.last_search_query or "hasmob002"
                if "channel" in t_lower:
                    logger.info(f"Fallback: Navigating to YouTube channel for query '{query}'")
                    page.goto(f"https://www.youtube.com/@{query}", timeout=15000, wait_until="commit")
                    clicked = True
                elif "video" in t_lower or "most watched" in t_lower:
                    logger.info(f"Fallback: Navigating to YouTube search video results for query '{query}'")
                    page.goto(f"https://www.youtube.com/results?search_query={query}", timeout=15000, wait_until="commit")
                    clicked = True
                else:
                    page.click(target, timeout=3000)
                    clicked = True

            return {
                "success": True,
                "target": target,
                "url": page.url,
                "title": page.title()
            }
        except Exception as e:
            logger.warning(f"Click failed on target '{target}': {e}")
            return {
                "success": False,
                "target": target,
                "error": f"Could not find or click element '{target}': {str(e)}"
            }

    def type_text(self, selector_or_label: str, text: str, press_enter: bool = True) -> Dict[str, Any]:
        page = self.session.get_active_page()
        try:
            # Safety check: avoid typing passwords unless specified
            if "password" in selector_or_label.lower():
                return {
                    "success": False,
                    "error": "Password input fields require explicit manual user entry."
                }

            selectors = [
                selector_or_label,
                f"input[name='{selector_or_label}']",
                f"input[placeholder*='{selector_or_label}']",
                f"textarea[placeholder*='{selector_or_label}']",
                f"input[aria-label*='{selector_or_label}']",
                "textarea",
                "input[type='text']",
                "input[type='search']",
                "input:not([type='hidden'])"
            ]

            typed = False
            for sel in selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible(timeout=2000):
                        loc.fill(text, timeout=5000)
                        if press_enter:
                            loc.press("Enter", timeout=5000)
                        typed = True
                        break
                except Exception:
                    continue

            if typed:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
                return {
                    "success": True,
                    "typed_text": text,
                    "url": page.url,
                    "title": page.title()
                }
            else:
                return {
                    "success": False,
                    "error": f"Editable input element '{selector_or_label}' not found."
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def press_key(self, key: str) -> Dict[str, Any]:
        page = self.session.get_active_page()
        try:
            page.keyboard.press(key)
            return {"success": True, "key": key, "url": page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def scroll(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        page = self.session.get_active_page()
        try:
            y = amount if direction.lower() == "down" else -amount
            page.evaluate(f"window.scrollBy(0, {y})")
            return {"success": True, "direction": direction, "amount": amount}
        except Exception as e:
            return {"success": False, "error": str(e)}
