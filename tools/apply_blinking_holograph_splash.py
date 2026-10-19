import os
import re
import base64
from pathlib import Path
from PIL import Image
from io import BytesIO

ROOT = Path(__file__).resolve().parent.parent

TARGETS = [
    Path(r"E:\PRUBETH IDE\resources\app"),
    Path(r"c:\Users\asus\heretic-work\VSCode-win32-x64\resources\app"),
    Path(r"C:\Users\asus\AppData\Local\Programs\PRUBETH IDE\resources\app"),
]

WATERMARK_TEXT = "DONT HIRE ROBOTS - JUST USE IT"

# Load optimized 256x256 base64 PNGs of official PRUBETH hexagonal neural processor logo
def get_optimized_b64(img_path):
    im = Image.open(img_path).resize((256, 256), Image.Resampling.LANCZOS)
    buf = BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")

DARK_B64 = get_optimized_b64(ROOT / "assets" / "logo_dark.png")
LIGHT_B64 = get_optimized_b64(ROOT / "assets" / "logo_light.png")

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
					0%, 100% {{ opacity: 0.96; }}
					48% {{ opacity: 0.96; }}
					50% {{ opacity: 0.75; }}
					52% {{ opacity: 1.0; }}
					54% {{ opacity: 0.88; }}
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
						opacity: 0.55;
						letter-spacing: 3px;
					}}
					50% {{
						opacity: 0.85;
						letter-spacing: 3.5px;
					}}
				}}
				@keyframes holoBeamSweep {{
					0% {{ transform: translateX(-100%); }}
					100% {{ transform: translateX(100%); }}
				}}
				.holo-monolith-container {{
					position: relative;
					width: 144px;
					height: 144px;
					display: flex;
					align-items: center;
					justify-content: center;
					animation: holoPulse 3s ease-in-out infinite, holoBlink 4.5s ease-in-out infinite;
				}}
				.holo-emblem-dark {{
					display: block;
					width: 132px;
					height: 132px;
					object-fit: contain;
					filter: drop-shadow(0 0 18px rgba(0, 240, 255, 0.65)) drop-shadow(0 0 36px rgba(112, 89, 226, 0.5));
				}}
				.holo-emblem-light {{
					display: none;
					width: 132px;
					height: 132px;
					object-fit: contain;
					filter: drop-shadow(0 4px 14px rgba(37, 99, 235, 0.4));
				}}
				.holo-orbit-ring {{
					position: absolute;
					inset: -14px;
					border-radius: 50%;
					border: 1.5px dashed rgba(0, 240, 255, 0.5);
					animation: holoSpin 16s linear infinite;
				}}
				.holo-orbit-ring-outer {{
					position: absolute;
					inset: -28px;
					border-radius: 50%;
					border: 1px dotted rgba(112, 89, 226, 0.4);
					animation: holoSpinReverse 24s linear infinite;
				}}
				@media (prefers-color-scheme: light) {{
					#monaco-parts-splash.prubeth-holograph-splash {{
						background: radial-gradient(circle at 50% 45%, #FFFFFF 0%, #F1F5F9 70%, #E2E8F0 100%) !important;
					}}
					.holo-emblem-dark {{
						display: none !important;
					}}
					.holo-emblem-light {{
						display: block !important;
					}}
					.holo-title-text {{
						color: #0F172A !important;
						text-shadow: 0 0 10px rgba(37, 99, 235, 0.25), 0 0 20px rgba(99, 102, 241, 0.2) !important;
					}}
					.holo-watermark-text {{
						color: #0284C7 !important;
					}}
					.holo-orbit-ring {{
						border-color: rgba(37, 99, 235, 0.5) !important;
					}}
					.holo-orbit-ring-outer {{
						border-color: rgba(99, 102, 241, 0.4) !important;
					}}
					.holo-beam-track {{
						background: rgba(0, 0, 0, 0.08) !important;
					}}
				}}
			</style>

			<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative;">
				<!-- Official PRUBETH Hexagonal Neural Processor Monolith with Quantum Particle Orbit Rings -->
				<div class="holo-monolith-container">
					<div class="holo-orbit-ring-outer"></div>
					<div class="holo-orbit-ring"></div>
					<img class="holo-emblem-dark" src="data:image/png;base64,{DARK_B64}" width="132" height="132" alt="PRUBETH" />
					<img class="holo-emblem-light" src="data:image/png;base64,{LIGHT_B64}" width="132" height="132" alt="PRUBETH" />
				</div>

				<!-- Holographic Title -->
				<div class="holo-title-text" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 26px; font-weight: 800; letter-spacing: 4px; margin-top: 32px; animation: holoTextGlow 2.8s ease-in-out infinite;">
					PRUBETH
				</div>

				<!-- Holographic Creator Signature Watermark -->
				<div class="holo-watermark-text" style="font-family: 'Space Mono', Consolas, 'Courier New', monospace; font-size: 11px; color: #38BDF8; margin-top: 12px; font-weight: 600; text-transform: uppercase; animation: holoWatermark 2.8s ease-in-out infinite;">
					{WATERMARK_TEXT}
				</div>

				<!-- Quantum Loading Beam -->
				<div class="holo-beam-track" style="width: 180px; height: 2px; background: rgba(255, 255, 255, 0.08); margin-top: 24px; border-radius: 2px; overflow: hidden; position: relative;">
					<div style="position: absolute; top: 0; left: 0; width: 45%; height: 100%; background: linear-gradient(90deg, transparent, #00F0FF, #7059E2, transparent); animation: holoBeamSweep 1.6s ease-in-out infinite;"></div>
				</div>
			</div>
		</div>
	</body>"""

def apply_blinking_holograph():
    print("=" * 70)
    print("APPLYING OFFICIAL PRUBETH HEXAGONAL NEURAL MONOLITH SPLASH SCREEN")
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

        print("  [SAFE] Skipping runtime innerHTML injection to maintain TrustedHTML CSP compliance.")

    print("\nOfficial PRUBETH Splash Screen Injection Complete!")

if __name__ == "__main__":
    apply_blinking_holograph()
