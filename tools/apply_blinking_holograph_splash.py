import os
import re
from pathlib import Path

TARGETS = [
    Path(r"E:\PRUBETH IDE\resources\app"),
    Path(r"c:\Users\asus\heretic-work\VSCode-win32-x64\resources\app"),
]

WATERMARK_TEXT = "DONT HIRE ROBOTS - JUST USE IT"

HOLOGRAPHIC_SPLASH_HTML = f"""	<body aria-label="">
		<div id="monaco-parts-splash" class="prubeth-holograph-splash" style="position: fixed; inset: 0; background: radial-gradient(circle at 50% 45%, #181c28 0%, #0d1017 70%, #080a0f 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 999999; user-select: none; pointer-events: none; overflow: hidden;">
			<style>
				@keyframes holoPulse {{
					0%, 100% {{
						transform: scale(1);
						filter: drop-shadow(0 0 18px rgba(112, 89, 226, 0.5)) drop-shadow(0 0 35px rgba(0, 240, 255, 0.35));
					}}
					50% {{
						transform: scale(1.045);
						filter: drop-shadow(0 0 30px rgba(112, 89, 226, 0.85)) drop-shadow(0 0 55px rgba(0, 240, 255, 0.65));
					}}
				}}
				@keyframes holoSpin {{
					0% {{ transform: rotate(0deg); }}
					100% {{ transform: rotate(360deg); }}
				}}
				@keyframes holoSpinReverse {{
					0% {{ transform: rotate(360deg); }}
					100% {{ transform: rotate(0deg); }}
				}}
				@keyframes holoBlink {{
					0%, 100% {{ opacity: 0.94; }}
					48% {{ opacity: 0.94; }}
					50% {{ opacity: 0.70; }}
					52% {{ opacity: 1.0; }}
					54% {{ opacity: 0.85; }}
					56% {{ opacity: 0.98; }}
				}}
				@keyframes holoTextGlow {{
					0%, 100% {{
						text-shadow: 0 0 10px rgba(0, 240, 255, 0.4), 0 0 22px rgba(112, 89, 226, 0.35);
						color: #F8FAFC;
					}}
					50% {{
						text-shadow: 0 0 18px rgba(0, 240, 255, 0.8), 0 0 36px rgba(112, 89, 226, 0.7);
						color: #FFFFFF;
					}}
				}}
				@keyframes holoWatermark {{
					0%, 100% {{
						opacity: 0.45;
						letter-spacing: 3px;
					}}
					50% {{
						opacity: 0.75;
						letter-spacing: 3.5px;
					}}
				}}
				@keyframes holoBeamSweep {{
					0% {{ transform: translateX(-100%); }}
					100% {{ transform: translateX(100%); }}
				}}
				.holo-flower-container {{
					position: relative;
					width: 140px;
					height: 140px;
					display: flex;
					align-items: center;
					justify-content: center;
					animation: holoPulse 2.8s ease-in-out infinite, holoBlink 4s ease-in-out infinite;
				}}
				.holo-orbit-ring {{
					position: absolute;
					inset: -12px;
					border-radius: 50%;
					border: 1.5px dashed rgba(0, 240, 255, 0.45);
					animation: holoSpin 16s linear infinite;
				}}
				.holo-orbit-ring-outer {{
					position: absolute;
					inset: -24px;
					border-radius: 50%;
					border: 1px dotted rgba(112, 89, 226, 0.35);
					animation: holoSpinReverse 24s linear infinite;
				}}
			</style>

			<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative;">
				<!-- Holographic Blooming Flower with Quantum Orbit Rings -->
				<div class="holo-flower-container">
					<div class="holo-orbit-ring-outer"></div>
					<div class="holo-orbit-ring"></div>
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="130" height="130">
						<defs>
							<linearGradient id="peachGrad" x1="0%" y1="0%" x2="100%" y2="100%">
								<stop offset="0%" stop-color="#FFB088" />
								<stop offset="100%" stop-color="#F7A07E" />
							</linearGradient>
							<linearGradient id="purpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
								<stop offset="0%" stop-color="#8F78FF" />
								<stop offset="100%" stop-color="#7059E2" />
							</linearGradient>
							<radialGradient id="turquoiseCore" cx="50%" cy="50%" r="50%">
								<stop offset="0%" stop-color="#A5F3FC" />
								<stop offset="60%" stop-color="#4ECDC4" />
								<stop offset="100%" stop-color="#06B6D4" />
							</radialGradient>
						</defs>
						<g transform="translate(256, 256)">
							<!-- Diagonal Peach Petals -->
							<g fill="url(#peachGrad)" opacity="0.94">
								<ellipse cx="0" cy="-115" rx="43" ry="86" transform="rotate(45)"/>
								<ellipse cx="0" cy="-115" rx="43" ry="86" transform="rotate(135)"/>
								<ellipse cx="0" cy="-115" rx="43" ry="86" transform="rotate(225)"/>
								<ellipse cx="0" cy="-115" rx="43" ry="86" transform="rotate(315)"/>
							</g>
							<!-- Cardinal Royal Purple Petals -->
							<g fill="url(#purpleGrad)" opacity="0.98">
								<ellipse cx="0" cy="-115" rx="47" ry="90" transform="rotate(0)"/>
								<ellipse cx="0" cy="-115" rx="47" ry="90" transform="rotate(90)"/>
								<ellipse cx="0" cy="-115" rx="47" ry="90" transform="rotate(180)"/>
								<ellipse cx="0" cy="-115" rx="47" ry="90" transform="rotate(270)"/>
							</g>
							<!-- Center Holographic Turquoise Core -->
							<circle cx="0" cy="0" r="46" fill="url(#turquoiseCore)" stroke="#FFFFFF" stroke-width="2.5" />
							<circle cx="0" cy="0" r="16" fill="#FFFFFF" opacity="0.8" />
						</g>
					</svg>
				</div>

				<!-- Holographic Title -->
				<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 25px; font-weight: 800; letter-spacing: 3.5px; margin-top: 32px; animation: holoTextGlow 2.8s ease-in-out infinite;">
					PRUBETH IDE
				</div>

				<!-- Holographic Creator Signature Watermark -->
				<div style="font-family: 'Space Mono', Consolas, 'Courier New', monospace; font-size: 11px; color: #38BDF8; margin-top: 12px; font-weight: 600; text-transform: uppercase; animation: holoWatermark 2.8s ease-in-out infinite;">
					{WATERMARK_TEXT}
				</div>

				<!-- Quantum Loading Beam -->
				<div style="width: 180px; height: 2px; background: rgba(255, 255, 255, 0.08); margin-top: 24px; border-radius: 2px; overflow: hidden; position: relative;">
					<div style="position: absolute; top: 0; left: 0; width: 45%; height: 100%; background: linear-gradient(90deg, transparent, #00F0FF, #7059E2, transparent); animation: holoBeamSweep 1.6s ease-in-out infinite;"></div>
				</div>
			</div>
		</div>
	</body>"""

def apply_blinking_holograph():
    print("=" * 70)
    print("APPLYING BLINKING HOLOGRAPHIC LOADING SCREEN FOR PRUBETH IDE")
    print("=" * 70)

    for target in TARGETS:
        if not target.exists():
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
                new_text = re.sub(
                    r'<body aria-label="">.*?</body>',
                    HOLOGRAPHIC_SPLASH_HTML,
                    text,
                    flags=re.DOTALL
                )
                hpath.write_text(new_text, encoding="utf-8")
                print(f"  [UPDATED HOLOGRAPHIC HTML] {hpath.name}")

        # 2. Update workbench.js and sessions.js
        js_files = [
            target / "out" / "vs" / "code" / "electron-browser" / "workbench" / "workbench.js",
            target / "out" / "vs" / "sessions" / "electron-browser" / "sessions.js"
        ]
        for jpath in js_files:
            if jpath.exists():
                text = jpath.read_text(encoding="utf-8")
                # Replace the innerHTML of prubeth-splash-brand with holographic content if present
                if 'prubeth-splash-brand' in text:
                    text = re.sub(
                        r'brandDiv\.innerHTML = `.*?`;',
                        f'brandDiv.innerHTML = `<div class="holo-flower-container"><div class="holo-orbit-ring-outer"></div><div class="holo-orbit-ring"></div><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="130" height="130"><g transform="translate(256, 256)"><g fill="#F7A07E" opacity="0.94"><ellipse cx="0" cy="-115" rx="43" ry="86" transform="rotate(45)"/><ellipse cx="0" cy="-115" rx="43" ry="86" transform="rotate(135)"/><ellipse cx="0" cy="-115" rx="43" ry="86" transform="rotate(225)"/><ellipse cx="0" cy="-115" rx="43" ry="86" transform="rotate(315)"/></g><g fill="#7059E2" opacity="0.98"><ellipse cx="0" cy="-115" rx="47" ry="90" transform="rotate(0)"/><ellipse cx="0" cy="-115" rx="47" ry="90" transform="rotate(90)"/><ellipse cx="0" cy="-115" rx="47" ry="90" transform="rotate(180)"/><ellipse cx="0" cy="-115" rx="47" ry="90" transform="rotate(270)"/></g><circle cx="0" cy="0" r="46" fill="#4ECDC4" stroke="#FFFFFF" stroke-width="2.5"/><circle cx="0" cy="0" r="16" fill="#FFFFFF" opacity="0.8"/></g></svg></div><div style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; font-size: 25px; font-weight: 800; letter-spacing: 3.5px; color: #FFFFFF; margin-top: 32px; animation: holoTextGlow 2.8s ease-in-out infinite;">PRUBETH IDE</div><div style="font-family: \'Space Mono\', Consolas, monospace; font-size: 11px; letter-spacing: 3px; color: #38BDF8; margin-top: 12px; font-weight: 600; text-transform: uppercase; animation: holoWatermark 2.8s ease-in-out infinite;">{WATERMARK_TEXT}</div><div style="width: 180px; height: 2px; background: rgba(255, 255, 255, 0.08); margin-top: 24px; border-radius: 2px; overflow: hidden; position: relative;"><div style="position: absolute; top: 0; left: 0; width: 45%; height: 100%; background: linear-gradient(90deg, transparent, #00F0FF, #7059E2, transparent); animation: holoBeamSweep 1.6s ease-in-out infinite;"></div></div>`;',
                        text,
                        flags=re.DOTALL
                    )
                    jpath.write_text(text, encoding="utf-8")
                    print(f"  [UPDATED HOLOGRAPHIC JS] {jpath.name}")

    print("\nBlinking Holographic Loading Screen Complete!")

if __name__ == "__main__":
    apply_blinking_holograph()
