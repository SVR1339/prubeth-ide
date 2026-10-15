import os
import re
from pathlib import Path

TARGETS = [
    Path(r"E:\PRUBETH IDE\resources\app"),
    Path(r"c:\Users\asus\heretic-work\VSCode-win32-x64\resources\app"),
]

# SVG templates with flower + SVR signature watermark
LETTERPRESS_DARK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="260" height="260" opacity="0.12">
  <g transform="translate(256, 225)">
    <g fill="#FFFFFF">
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(45)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(135)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(225)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(315)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(0)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(90)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(180)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(270)"/>
    </g>
    <circle cx="0" cy="0" r="44" fill="#FFFFFF"/>
  </g>
  <text x="256" y="445" text-anchor="middle" font-family="'Space Mono', Consolas, 'Courier New', monospace" font-size="15" letter-spacing="6" fill="#FFFFFF" opacity="0.45" font-weight="600">======          SVR          ======</text>
</svg>
"""

LETTERPRESS_LIGHT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="260" height="260" opacity="0.15">
  <g transform="translate(256, 225)">
    <g fill="#707075">
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(45)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(135)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(225)"/>
      <ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(315)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(0)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(90)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(180)"/>
      <ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(270)"/>
    </g>
    <circle cx="0" cy="0" r="44" fill="#505055"/>
  </g>
  <text x="256" y="445" text-anchor="middle" font-family="'Space Mono', Consolas, 'Courier New', monospace" font-size="15" letter-spacing="6" fill="#303035" opacity="0.45" font-weight="600">======          SVR          ======</text>
</svg>
"""

SPLASH_HTML_CONTENT = """	<body aria-label="">
		<div id="monaco-parts-splash" style="position: fixed; inset: 0; background-color: #12141a; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 999999; user-select: none; pointer-events: none;">
			<div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="118" height="118" style="filter: drop-shadow(0 12px 28px rgba(112, 89, 226, 0.4));">
					<g transform="translate(256, 256)">
						<!-- Diagonal Peach Petals -->
						<g fill="#F7A07E" opacity="0.92">
							<ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(45)"/>
							<ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(135)"/>
							<ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(225)"/>
							<ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(315)"/>
						</g>
						<!-- Cardinal Purple Petals -->
						<g fill="#7059E2" opacity="0.96">
							<ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(0)"/>
							<ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(90)"/>
							<ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(180)"/>
							<ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(270)"/>
						</g>
						<!-- Center Turquoise Disc -->
						<circle cx="0" cy="0" r="44" fill="#4ECDC4" stroke="#FFFFFF" stroke-width="2.5" opacity="0.98"/>
					</g>
				</svg>
				<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 24px; font-weight: 700; letter-spacing: 3px; color: #F1F5F9; margin-top: 22px;">
					PRUBETH IDE
				</div>
				<div style="font-family: 'Space Mono', Consolas, 'Courier New', monospace; font-size: 11px; letter-spacing: 6px; color: rgba(148, 163, 184, 0.5); margin-top: 12px; font-weight: 600; text-transform: uppercase;">
					======&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;SVR&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;======
				</div>
			</div>
		</div>
	</body>"""

def apply_branding():
    print("=" * 70)
    print("APPLYING PRUBETH IDE SPLASH SCREEN & SVR SIGNATURE WATERMARK")
    print("=" * 70)

    for target in TARGETS:
        if not target.exists():
            print(f"Skipping: {target}")
            continue

        print(f"\nProcessing target: {target}")

        # 1. Update HTML splash in workbench.html & sessions.html
        html_files = [
            target / "out" / "vs" / "code" / "electron-browser" / "workbench" / "workbench.html",
            target / "out" / "vs" / "sessions" / "electron-browser" / "sessions.html"
        ]
        for hpath in html_files:
            if hpath.exists():
                text = hpath.read_text(encoding="utf-8")
                # Replace <body aria-label="">...</body>
                new_text = re.sub(
                    r'<body aria-label="">.*?</body>',
                    SPLASH_HTML_CONTENT,
                    text,
                    flags=re.DOTALL
                )
                if new_text != text:
                    hpath.write_text(new_text, encoding="utf-8")
                    print(f"  [UPDATED HTML SPLASH] {hpath.name}")
                else:
                    print(f"  [UNCHANGED HTML] {hpath.name}")

        # 2. Update workbench.js and sessions.js showDefaultSplash to ensure branding is preserved
        js_files = [
            target / "out" / "vs" / "code" / "electron-browser" / "workbench" / "workbench.js",
            target / "out" / "vs" / "sessions" / "electron-browser" / "sessions.js"
        ]
        for jpath in js_files:
            if jpath.exists():
                text = jpath.read_text(encoding="utf-8")
                # Ensure body is appended if not present
                old_append = 'window.document.body.appendChild(splash);'
                if old_append in text and 'prubeth-splash-brand' not in text:
                    brand_injection = """
      if (!window.document.getElementById('prubeth-splash-brand')) {
        const brandDiv = window.document.createElement('div');
        brandDiv.id = 'prubeth-splash-brand';
        brandDiv.style.position = 'fixed';
        brandDiv.style.top = '50%';
        brandDiv.style.left = '50%';
        brandDiv.style.transform = 'translate(-50%, -50%)';
        brandDiv.style.display = 'flex';
        brandDiv.style.flexDirection = 'column';
        brandDiv.style.alignItems = 'center';
        brandDiv.style.justifyContent = 'center';
        brandDiv.style.zIndex = '999999';
        brandDiv.style.pointerEvents = 'none';
        brandDiv.style.userSelect = 'none';
        brandDiv.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="118" height="118" style="filter: drop-shadow(0 12px 28px rgba(112, 89, 226, 0.4));"><g transform="translate(256, 256)"><g fill="#F7A07E" opacity="0.92"><ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(45)"/><ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(135)"/><ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(225)"/><ellipse cx="0" cy="-115" rx="42" ry="84" transform="rotate(315)"/></g><g fill="#7059E2" opacity="0.96"><ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(0)"/><ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(90)"/><ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(180)"/><ellipse cx="0" cy="-115" rx="46" ry="88" transform="rotate(270)"/></g><circle cx="0" cy="0" r="44" fill="#4ECDC4" stroke="#FFFFFF" stroke-width="2.5" opacity="0.98"/></g></svg><div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 24px; font-weight: 700; letter-spacing: 3px; color: #F1F5F9; margin-top: 22px;">PRUBETH IDE</div><div style="font-family: 'Space Mono', Consolas, 'Courier New', monospace; font-size: 11px; letter-spacing: 6px; color: rgba(148, 163, 184, 0.5); margin-top: 12px; font-weight: 600; text-transform: uppercase;">======&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;SVR&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;======</div>`;
        splash.appendChild(brandDiv);
      }
      window.document.body.appendChild(splash);"""
                    text = text.replace(old_append, brand_injection)
                    jpath.write_text(text, encoding="utf-8")
                    print(f"  [INJECTED JS BRAND] {jpath.name}")

        # 3. Update letterpress watermarks with flower + SVR signature watermark
        watermark_paths = [
            target / "out" / "media" / "letterpress-dark.svg",
            target / "out" / "media" / "letterpress-light.svg",
            target / "out" / "media" / "letterpress-hcDark.svg",
            target / "out" / "media" / "letterpress-hcLight.svg",
            target / "out" / "vs" / "workbench" / "browser" / "parts" / "editor" / "media" / "letterpress-dark.svg",
            target / "out" / "vs" / "workbench" / "browser" / "parts" / "editor" / "media" / "letterpress-light.svg",
            target / "out" / "vs" / "workbench" / "browser" / "parts" / "editor" / "media" / "letterpress-hcDark.svg",
            target / "out" / "vs" / "workbench" / "browser" / "parts" / "editor" / "media" / "letterpress-hcLight.svg",
            target / "out" / "vs" / "sessions" / "contrib" / "chat" / "browser" / "media" / "letterpress-sessions-dark.svg",
            target / "out" / "vs" / "sessions" / "contrib" / "chat" / "browser" / "media" / "letterpress-sessions-light.svg",
        ]

        for wpath in watermark_paths:
            if wpath.exists():
                is_light = "light" in wpath.name.lower() or "hclight" in wpath.name.lower()
                content = LETTERPRESS_LIGHT if is_light else LETTERPRESS_DARK
                wpath.write_text(content, encoding="utf-8")
                print(f"  [UPDATED WATERMARK] {wpath.relative_to(target)}")

    print("\nSplash Screen and Watermark Branding Complete!")

if __name__ == "__main__":
    apply_branding()
