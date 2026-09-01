import logging
from typing import Dict, Any, List
from jarvis.browser.session import BrowserSession

logger = logging.getLogger("jarvis.browser.inspection")

class InspectionManager:
    """
    Extracts concise, structured summary of visible page elements (buttons, links, inputs).
    """

    def __init__(self, session: BrowserSession):
        self.session = session

    def get_page_info(self, max_elements: int = 25) -> Dict[str, Any]:
        page = self.session.get_active_page()
        try:
            url = page.url
            title = page.title()

            # Extract visible links
            links = page.evaluate("""(maxCount) => {
                const results = [];
                const anchors = document.querySelectorAll('a[href]');
                for (let a of anchors) {
                    if (results.length >= maxCount) break;
                    const text = (a.innerText || a.ariaLabel || '').trim();
                    if (text && a.offsetWidth > 0 && a.offsetHeight > 0) {
                        results.push({ text: text.substring(0, 50), href: a.href });
                    }
                }
                return results;
            }""", max_elements)

            # Extract visible buttons
            buttons = page.evaluate("""(maxCount) => {
                const results = [];
                const btns = document.querySelectorAll('button, input[type="button"], input[type="submit"], [role="button"]');
                for (let b of btns) {
                    if (results.length >= maxCount) break;
                    const text = (b.innerText || b.value || b.ariaLabel || '').trim();
                    if (text && b.offsetWidth > 0 && b.offsetHeight > 0) {
                        results.push({ text: text.substring(0, 50), id: b.id || '', name: b.name || '' });
                    }
                }
                return results;
            }""", max_elements)

            # Extract visible inputs
            inputs = page.evaluate("""(maxCount) => {
                const results = [];
                const inps = document.querySelectorAll('input:not([type="hidden"]), textarea, select');
                for (let i of inps) {
                    if (results.length >= maxCount) break;
                    if (i.offsetWidth > 0 && i.offsetHeight > 0) {
                        results.push({
                            type: i.type || i.tagName.toLowerCase(),
                            name: i.name || '',
                            id: i.id || '',
                            placeholder: i.placeholder || '',
                            value: (i.value || '').substring(0, 50)
                        });
                    }
                }
                return results;
            }""", max_elements)

            return {
                "url": url,
                "title": title,
                "links_count": len(links),
                "buttons_count": len(buttons),
                "inputs_count": len(inputs),
                "sample_links": links[:10],
                "sample_buttons": buttons[:10],
                "sample_inputs": inputs[:10]
            }
        except Exception as e:
            logger.error(f"Failed to inspect page info: {e}")
            return {"error": str(e)}

    def get_visible_text(self, max_length: int = 5000) -> Dict[str, Any]:
        page = self.session.get_active_page()
        try:
            text = page.evaluate("() => document.body ? document.body.innerText : ''")
            clean_text = " ".join(text.split())[:max_length]
            return {
                "url": page.url,
                "title": page.title(),
                "text_length": len(text),
                "text_summary": clean_text
            }
        except Exception as e:
            return {"error": str(e)}
