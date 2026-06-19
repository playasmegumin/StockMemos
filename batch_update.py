import os
import sys

base = "/mnt/c/Users/Apogee/Documents/Kimi/Workspaces/StockAnalyzer"

files = {
    "streamlit_app": os.path.join(base, "frontend/streamlit_app.py"),
    "page_2_个股分析": os.path.join(base, "frontend/pages/2_个股分析.py"),
    "page_2_自选股": os.path.join(base, "frontend/pages/2_自选股与备忘录.py"),
    "page_3_事件时间线": os.path.join(base, "frontend/pages/3_事件时间线.py"),
    "page_3_事件追踪": os.path.join(base, "frontend/pages/3_事件追踪.py"),
    "page_4_策略回测": os.path.join(base, "frontend/pages/4_策略与回测.py"),
    "page_4_策略配置": os.path.join(base, "frontend/pages/4_策略配置.py"),
    "page_5_设置": os.path.join(base, "frontend/pages/5_设置与投递.py"),
}

results = []

for name, path in files.items():
    if not os.path.exists(path):
        results.append(f"MISS {name}: not found")
        continue
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "render_sidebar" in content:
        results.append(f"OK {name}: already has render_sidebar")
        continue
    
    # Insert render_sidebar() after CSS block
    css_end_marker = """, unsafe_allow_html=True)"""
    if css_end_marker not in content:
        results.append(f"WARN {name}: CSS marker not found")
        continue
    
    insert_pos = content.find(css_end_marker) + len(css_end_marker)
    new_code = """

render_sidebar()
"""
    new_content = content[:insert_pos] + new_code + content[insert_pos:]
    
    # Add sys.path if not present
    if "sys.path.append" not in new_content:
        first_import = new_content.find("import ")
        if first_import >= 0:
            import_block = """import sys
sys.path.append("/app")

"""
            new_content = new_content[:first_import] + import_block + new_content[first_import:]
    
    # Add from import if not present
    if "from app.components.sidebar import render_sidebar" not in new_content:
        import_marker = "sys.path.append(\"/app\")\n"
        import_pos = new_content.find(import_marker) + len(import_marker)
        import_line = """from app.components.sidebar import render_sidebar

"""
        new_content = new_content[:import_pos] + import_line + new_content[import_pos:]
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    results.append(f"OK {name}: updated")

for r in results:
    print(r)
