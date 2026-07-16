"""Visual check v2: comprehensive sidebar DOM inspection for Streamlit 1.37.0"""
import os, sys, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8501")
OUTPUT_DIR = Path(__file__).parent / "screenshots"
OUTPUT_DIR.mkdir(exist_ok=True)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        
        print(f"Loading: {FRONTEND_URL}")
        page.goto(FRONTEND_URL, timeout=30000, wait_until="networkidle")
        page.wait_for_selector("section[data-testid='stSidebar']", timeout=30000)
        time.sleep(3)  # Let Streamlit fully render
        
        page.screenshot(path=str(OUTPUT_DIR / "homepage.png"), full_page=True)
        print(f"Screenshot: {OUTPUT_DIR / 'homepage.png'}")

        # Dump ALL sidebar links (any mechanism)
        links = page.evaluate("""
            () => {
                const sb = document.querySelector("section[data-testid='stSidebar']");
                if (!sb) return [];
                const allLinks = sb.querySelectorAll("a, button, [role='button'], [role='link']");
                return Array.from(allLinks).map(el => ({
                    tag: el.tagName,
                    text: el.textContent.trim().substring(0, 60),
                    href: el.getAttribute("href") || "",
                    data_testid: el.getAttribute("data-testid") || "",
                    visible: el.offsetParent !== null,
                    aria_label: el.getAttribute("aria-label") || "",
                }));
            }
        """)
        
        print(f"\n=== All clickable elements in sidebar ===")
        for i, l in enumerate(links):
            visibility = "VISIBLE" if l["visible"] else "HIDDEN"
            print(f"  [{i}] <{l['tag']}> text='{l['text']}' href='{l['href'][:50]}' dtid='{l['data_testid']}' {visibility}")

        # Dump ALL visible text nodes  
        visible_texts = page.evaluate("""
            () => {
                const sb = document.querySelector("section[data-testid='stSidebar']");
                if (!sb) return [];
                return Array.from(sb.querySelectorAll("*"))
                    .filter(el => el.children.length === 0 && el.offsetParent !== null && el.textContent.trim())
                    .map(el => ({
                        tag: el.tagName,
                        text: el.textContent.trim().substring(0, 80),
                        dtid: el.getAttribute("data-testid") || "",
                        cls: (typeof el.className === 'string') ? el.className.split(' ').filter(c => c.startsWith('st')).join(' ') : 'N/A',
                    }))
                    .filter(x => x.text.length > 0);
            }
        """)
        
        print(f"\n=== All visible text elements in sidebar ===")
        for t in visible_texts[:30]:
            print(f"  <{t['tag']}> dtid='{t['dtid']}' cls='{t['cls'][:40]}' text='{t['text']}'")

        # Check for Streamlit-native page nav specifically
        print(f"\n=== Streamlit native page nav check ===")
        page_html = page.evaluate("() => document.querySelector('section[data-testid=\"stSidebar\"]')?.innerHTML?.substring(0, 2000) || 'NO SIDEBAR'")
        # Search for keywords
        for keyword in ["streamlit app", "stock detail", "stPageLink", "page-link", "stSidebarNav"]:
            found = keyword.lower() in page_html.lower()
            print(f"  '{keyword}' in HTML: {found}")
            if found:
                idx = page_html.lower().find(keyword.lower())
                context = page_html[max(0,idx-80):idx+80]
                print(f"    Context: ...{context}...")
        
        browser.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
