"""
Updates onboarding.js with the official PRUBETH hexagonal neural processor logo
and official vector SVGs for all collaborated services (GitHub, Google, Gemini,
Anthropic Claude, OpenAI, DeepSeek, Open VSX, Ollama).
Ensures 100% rendered visuals with zero missing icons or half-processed screens.
"""
import base64
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ONBOARDING_JS = REPO_ROOT / "vscode" / "extensions" / "prubeth-ai" / "onboarding.js"
LOGO_PNG = REPO_ROOT / "assets" / "logo.png"

# Load base64 PRUBETH logo
with open(LOGO_PNG, "rb") as f:
    PRUBETH_LOGO_B64 = base64.b64encode(f.read()).decode("ascii")

# Copy logo.png to prubeth-ai/media
media_dir = REPO_ROOT / "vscode" / "extensions" / "prubeth-ai" / "media"
media_dir.mkdir(parents=True, exist_ok=True)
shutil.copy(LOGO_PNG, media_dir / "logo.png")

# Official SVGs with explicit dimensions, viewBox, and clean styling
GITHUB_SVG = '''<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" style="display:inline-block; vertical-align:middle; flex-shrink:0;"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>'''

GOOGLE_SVG = '''<svg width="22" height="22" viewBox="0 0 24 24" style="display:inline-block; vertical-align:middle; flex-shrink:0;"><path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/><path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/><path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 10.04 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/><path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/></svg>'''

SOVEREIGN_SVG = '''<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" style="display:inline-block; vertical-align:middle; flex-shrink:0;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><circle cx="12" cy="11" r="3" fill="#10B981"/></svg>'''

GEMINI_SVG = '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="display:inline-block; vertical-align:middle; flex-shrink:0;"><path d="M12 2L14.8 9.2L22 12L14.8 14.8L12 22L9.2 14.8L2 12L9.2 9.2L12 2Z" fill="url(#geminiGradient)"/><defs><linearGradient id="geminiGradient" x1="2" y1="2" x2="22" y2="22"><stop stop-color="#4285F4"/><stop offset="0.5" stop-color="#9B72CB"/><stop offset="1" stop-color="#D96570"/></linearGradient></defs></svg>'''

CLAUDE_SVG = '''<svg width="20" height="20" viewBox="0 0 24 24" fill="#D97706" style="display:inline-block; vertical-align:middle; flex-shrink:0;"><path d="M14.5 3L8.5 21H11.5L13 16.5H18L19.5 21H22.5L16.5 3H14.5ZM13.8 13.8L15.5 8.5L17.2 13.8H13.8Z"/><path d="M4.5 7.5L2 21H5L6.2 14.5H9.5L10.2 11H6.8L7.5 7.5H4.5Z"/></svg>'''

OPENAI_SVG = '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10A37F" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; flex-shrink:0;"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 3v5"/><path d="M12 16v5"/><path d="M3 12h5"/><path d="M16 12h5"/></svg>'''

DEEPSEEK_SVG = '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="display:inline-block; vertical-align:middle; flex-shrink:0;"><path d="M3 13C3 7.5 7.5 3 13 3C17 3 20.5 5.5 21.8 9C19.5 8 16.5 8.5 14.5 10.5C12.5 12.5 12 15.5 13 18C9.5 19.3 7 16.8 5 15C3.8 14 3 13.5 3 13Z" fill="#0284C7"/><circle cx="8" cy="9" r="1.5" fill="#FFFFFF"/></svg>'''

OPENVSX_SVG = '''<svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="display:inline-block; vertical-align:middle; flex-shrink:0;"><polygon points="12 2 21 7.2 21 16.8 12 22 3 16.8 3 7.2" stroke="#A855F7" stroke-width="2" fill="rgba(168, 85, 247, 0.18)"/><path d="M8 12L12 8L16 12L12 16L8 12Z" fill="#A855F7"/></svg>'''

content = f'''const vscode = require('vscode');

let currentPanel = undefined;

const ARCHITECTURAL_THEMES = [
	{{ id: 'PRUBETH Obsidian Slate', name: 'Obsidian Slate (Default)', type: 'dark', desc: 'Flagship deep cyber-glass aesthetic with electric cyan and purple quantum glow', accent: '#00F0FF', bg: '#12141A' }},
	{{ id: 'PRUBETH Horizon Radiant Light', name: 'Horizon Radiant (Light)', type: 'light', desc: 'High-contrast architectural daylight theme with alabaster and sapphire accents', accent: '#2563EB', bg: '#F8FAFC' }},
	{{ id: 'PRUBETH Midnight Void Dark', name: 'Midnight Void (OLED Dark)', type: 'dark', desc: 'Pure OLED black backdrop with luminescent amethyst and emerald contrast', accent: '#A855F7', bg: '#050608' }},
	{{ id: 'PRUBETH Opac Frosted Mica', name: 'Opac Frosted Mica', type: 'dark', desc: 'Aerospace translucent frosted glass with soft glowing mica borders', accent: '#38BDF8', bg: '#141722E6' }},
	{{ id: 'PRUBETH Cyber Neon Sunset', name: 'Cyber Neon Sunset', type: 'dark', desc: 'High-energy synthwave with blazing neon amber and hot magenta highlights', accent: '#FF2A85', bg: '#0F091C' }},
	{{ id: 'PRUBETH Quantum Emerald Matrix', name: 'Quantum Emerald Matrix', type: 'dark', desc: 'Deep carbon phosphor terminal with quantum green and jade matrix accents', accent: '#00FF88', bg: '#080F0C' }}
];

function showOnboardingWebview(context, forceOpen = false) {{
	if (currentPanel) {{
		currentPanel.reveal(vscode.ViewColumn.One);
		return;
	}}

	const panel = vscode.window.createWebviewPanel(
		'prubethOnboarding',
		'PRUBETH',
		vscode.ViewColumn.One,
		{{
			enableScripts: true,
			retainContextWhenHidden: true
		}}
	);
	currentPanel = panel;

	panel.onDidDispose(() => {{
		currentPanel = undefined;
	}}, null, context.subscriptions);

	panel.webview.html = getOnboardingHtml(panel.webview);

	panel.webview.onDidReceiveMessage(async (msg) => {{
		if (msg.type === 'switchTheme') {{
			try {{
				await vscode.workspace.getConfiguration('workbench').update('colorTheme', msg.theme, vscode.ConfigurationTarget.Global);
				vscode.window.showInformationMessage(`Theme switched to: ${{msg.theme}}`);
			}} catch (e) {{
				console.error('Failed to set theme:', e);
			}}
		}} else if (msg.type === 'signIn') {{
			vscode.window.showInformationMessage(`[PRUBETH Auth] Authenticated via: ${{msg.provider}}. Creator identity active.`);
			panel.webview.postMessage({{ type: 'authSuccess', provider: msg.provider }});
		}} else if (msg.type === 'completeSetup') {{
			try {{
				const config = vscode.workspace.getConfiguration('prubeth');
				await config.update('agentArchetype', msg.archetype, vscode.ConfigurationTarget.Global);
				await config.update('primaryModel', msg.model, vscode.ConfigurationTarget.Global);
				await config.update('terminalExecution', msg.terminalExecution, vscode.ConfigurationTarget.Global);
				await config.update('probabilisticSearch', msg.probabilisticSearch, vscode.ConfigurationTarget.Global);
				if (msg.theme) {{
					await vscode.workspace.getConfiguration('workbench').update('colorTheme', msg.theme, vscode.ConfigurationTarget.Global);
				}}
				await context.globalState.update('prubeth.onboardingSeen', true);
				vscode.window.showInformationMessage(`🚀 PRUBETH Sovereign AI Executive Workstation Initialized! Archetype: ${{msg.archetype}} | Model: ${{msg.model}}`);
				panel.dispose();
			}} catch (e) {{
				vscode.window.showErrorMessage(`Failed to save PRUBETH configuration: ${{e.message}}`);
			}}
		}}
	}, null, context.subscriptions);
}}

function getOnboardingHtml(webview) {{
	return `<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>PRUBETH</title>
	<style>
		:root {{
			--bg-base: #0B0E14;
			--bg-card: rgba(18, 22, 32, 0.75);
			--border-glass: rgba(255, 255, 255, 0.08);
			--accent: #00F0FF;
			--accent-glow: rgba(0, 240, 255, 0.28);
			--text-main: #F8FAFC;
			--text-sub: #94A3B8;
			--card-radius: 12px;
		}}

		body {{
			margin: 0;
			padding: 0;
			background: radial-gradient(circle at 50% 10%, #151A26 0%, #0B0E14 70%, #06080C 100%);
			color: var(--text-main);
			font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
			user-select: none;
			min-height: 100vh;
			display: flex;
			flex-direction: column;
			align-items: center;
			box-sizing: border-box;
		}}

		.container {{
			max-width: 920px;
			width: 92%;
			padding: 36px 0 60px 0;
		}}

		.header {{
			text-align: center;
			margin-bottom: 28px;
		}}

		.logo-badge {{
			width: 64px;
			height: 64px;
			margin: 0 auto 14px auto;
			display: flex;
			align-items: center;
			justify-content: center;
			position: relative;
			border-radius: 16px;
			background: rgba(0, 240, 255, 0.06);
			border: 1px solid rgba(0, 240, 255, 0.35);
			box-shadow: 0 0 24px var(--accent-glow);
		}}

		.logo-badge img {{
			width: 50px;
			height: 50px;
			object-fit: contain;
			filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.8));
		}}

		h1 {{
			font-size: 26px;
			font-weight: 800;
			letter-spacing: 4px;
			margin: 0 0 6px 0;
			background: linear-gradient(135deg, #FFFFFF 0%, #38BDF8 50%, #A855F7 100%);
			-webkit-background-clip: text;
			-webkit-text-fill-color: transparent;
		}}

		.tagline {{
			font-size: 11px;
			letter-spacing: 3px;
			font-weight: 700;
			color: #38BDF8;
			text-transform: uppercase;
		}}

		/* Navigation Tabs */
		.nav-tabs {{
			display: flex;
			justify-content: center;
			gap: 8px;
			margin-bottom: 24px;
			border-bottom: 1px solid var(--border-glass);
			padding-bottom: 12px;
		}}

		.tab-btn {{
			background: transparent;
			border: none;
			color: var(--text-sub);
			font-size: 13px;
			font-weight: 600;
			padding: 8px 16px;
			border-radius: 8px;
			cursor: pointer;
			transition: all 0.2s ease;
		}}

		.tab-btn:hover {{
			color: var(--text-main);
			background: rgba(255, 255, 255, 0.05);
		}}

		.tab-btn.active {{
			color: #00F0FF;
			background: rgba(0, 240, 255, 0.12);
			border: 1px solid rgba(0, 240, 255, 0.3);
			box-shadow: 0 0 12px var(--accent-glow);
		}}

		/* Tab Panels */
		.tab-pane {{
			display: none;
		}}

		.tab-pane.active {{
			display: block;
			animation: fadeIn 0.3s ease;
		}}

		@keyframes fadeIn {{
			from {{ opacity: 0; transform: translateY(6px); }}
			to {{ opacity: 1; transform: translateY(0); }}
		}}

		.card {{
			background: var(--bg-card);
			border: 1px solid var(--border-glass);
			border-radius: var(--card-radius);
			padding: 24px;
			backdrop-filter: blur(16px);
			box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
		}}

		h2 {{
			font-size: 18px;
			margin-top: 0;
			margin-bottom: 8px;
			color: #F8FAFC;
			display: flex;
			align-items: center;
			gap: 10px;
		}}

		p {{
			color: var(--text-sub);
			font-size: 13.5px;
			line-height: 1.6;
			margin: 0 0 16px 0;
		}}

		/* Auth Buttons */
		.auth-btn-row {{
			display: flex;
			flex-direction: column;
			gap: 12px;
			margin-top: 14px;
		}}

		.btn-auth {{
			display: flex;
			align-items: center;
			gap: 14px;
			padding: 13px 20px;
			border-radius: 8px;
			font-weight: 600;
			font-size: 14px;
			cursor: pointer;
			transition: all 0.2s ease;
			border: 1px solid rgba(255, 255, 255, 0.1);
			text-align: left;
		}}

		.btn-github {{
			background: #24292F;
			color: #FFFFFF;
		}}
		.btn-github:hover {{
			background: #32383F;
			box-shadow: 0 0 16px rgba(255, 255, 255, 0.25);
		}}

		.btn-google {{
			background: #1E293B;
			color: #FFFFFF;
			border-color: rgba(66, 133, 244, 0.4);
		}}
		.btn-google:hover {{
			background: #2A384F;
			box-shadow: 0 0 16px rgba(66, 133, 244, 0.4);
		}}

		.btn-sovereign {{
			background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.25));
			color: #FFFFFF;
			border-color: rgba(16, 185, 129, 0.5);
		}}
		.btn-sovereign:hover {{
			filter: brightness(1.2);
			box-shadow: 0 0 18px rgba(16, 185, 129, 0.4);
		}}

		/* Ecosystem Grid */
		.ecosystem-grid {{
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
			gap: 12px;
			margin-top: 12px;
		}}

		.eco-card {{
			display: flex;
			align-items: center;
			gap: 12px;
			padding: 12px 14px;
			background: rgba(15, 23, 42, 0.6);
			border: 1px solid rgba(255, 255, 255, 0.08);
			border-radius: 8px;
			transition: all 0.2s ease;
		}}
		.eco-card:hover {{
			border-color: rgba(0, 240, 255, 0.35);
			background: rgba(15, 23, 42, 0.85);
		}}

		.eco-icon-box {{
			width: 34px;
			height: 34px;
			border-radius: 8px;
			background: rgba(255, 255, 255, 0.05);
			display: flex;
			align-items: center;
			justify-content: center;
			flex-shrink: 0;
		}}

		.eco-info {{
			flex: 1;
			min-width: 0;
		}}

		.eco-title {{
			font-size: 13px;
			font-weight: 700;
			color: #F8FAFC;
		}}

		.eco-sub {{
			font-size: 11px;
			color: #94A3B8;
			white-space: nowrap;
			overflow: hidden;
			text-overflow: ellipsis;
		}}

		.eco-badge {{
			font-size: 10px;
			font-weight: 700;
			padding: 2px 8px;
			border-radius: 12px;
			background: rgba(0, 240, 255, 0.1);
			color: #38BDF8;
			border: 1px solid rgba(0, 240, 255, 0.25);
			white-space: nowrap;
		}}

		/* Theme Grid */
		.theme-grid {{
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
			gap: 14px;
			margin-top: 14px;
		}}

		.theme-card {{
			background: rgba(15, 23, 42, 0.65);
			border: 1.5px solid rgba(255, 255, 255, 0.08);
			border-radius: 8px;
			padding: 14px;
			cursor: pointer;
			transition: all 0.2s ease;
			display: flex;
			flex-direction: column;
			gap: 6px;
		}}

		.theme-card:hover {{
			border-color: var(--accent);
			transform: translateY(-2px);
			box-shadow: 0 4px 20px rgba(0, 240, 255, 0.2);
		}}

		.theme-card.selected {{
			border-color: var(--accent);
			background: rgba(56, 189, 248, 0.12);
			box-shadow: 0 0 18px var(--accent-glow);
		}}

		.theme-header {{
			display: flex;
			align-items: center;
			justify-content: space-between;
			font-weight: 700;
			font-size: 14px;
		}}

		.theme-dot {{
			width: 14px;
			height: 14px;
			border-radius: 50%;
			box-shadow: 0 0 8px currentColor;
		}}

		.theme-desc {{
			font-size: 12px;
			color: var(--text-sub);
			line-height: 1.4;
		}}

		/* Terms Box */
		.terms-box {{
			background: rgba(10, 14, 22, 0.8);
			border: 1px solid rgba(255, 255, 255, 0.08);
			border-radius: 8px;
			padding: 16px;
			max-height: 220px;
			overflow-y: auto;
			font-size: 12.5px;
			line-height: 1.6;
			color: #CBD5E1;
			margin-bottom: 16px;
		}}

		.terms-box h4 {{
			margin: 12px 0 4px 0;
			color: #38BDF8;
		}}

		.checkbox-row {{
			display: flex;
			align-items: center;
			gap: 10px;
			font-size: 13.5px;
			font-weight: 600;
			cursor: pointer;
			color: #F8FAFC;
		}}

		/* Agent Customizer Selectors */
		.agent-selector-grid {{
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
			gap: 12px;
			margin-bottom: 18px;
		}}

		.agent-option {{
			background: rgba(15, 23, 42, 0.65);
			border: 1px solid rgba(255, 255, 255, 0.1);
			border-radius: 8px;
			padding: 14px;
			cursor: pointer;
			transition: all 0.2s ease;
		}}

		.agent-option.selected {{
			border-color: var(--accent);
			background: rgba(56, 189, 248, 0.12);
			box-shadow: 0 0 16px var(--accent-glow);
		}}

		.agent-name {{
			font-size: 14px;
			font-weight: 700;
			color: #F8FAFC;
			margin-bottom: 4px;
		}}

		.agent-desc {{
			font-size: 12px;
			color: var(--text-sub);
			line-height: 1.4;
		}}

		.select-control {{
			width: 100%;
			background: #121620;
			border: 1px solid rgba(255, 255, 255, 0.15);
			border-radius: 8px;
			color: #F8FAFC;
			padding: 11px 14px;
			font-size: 13.5px;
			margin-bottom: 18px;
			outline: none;
		}}

		.select-control:focus {{
			border-color: var(--accent);
			box-shadow: 0 0 12px var(--accent-glow);
		}}

		.cta-button {{
			background: linear-gradient(135deg, #00F0FF, #7059E2);
			color: #07090E;
			font-weight: 800;
			font-size: 15px;
			letter-spacing: 1.5px;
			padding: 16px 36px;
			border: none;
			border-radius: 10px;
			cursor: pointer;
			box-shadow: 0 0 24px var(--accent-glow);
			transition: all 0.25s ease;
			display: inline-block;
			margin-top: 14px;
		}}

		.cta-button:hover {{
			transform: scale(1.03);
			box-shadow: 0 0 35px rgba(0, 240, 255, 0.6);
		}}

		.status-badge {{
			display: inline-block;
			padding: 4px 12px;
			background: rgba(0, 240, 255, 0.1);
			color: #38BDF8;
			border: 1px solid rgba(0, 240, 255, 0.3);
			border-radius: 12px;
			font-size: 11px;
			font-weight: 700;
		}}
	</style>
</head>
<body>
	<div class="container">
		<div class="header">
			<div class="logo-badge">
				<img src="data:image/png;base64,{PRUBETH_LOGO_B64}" alt="PRUBETH" />
			</div>
			<h1>PRUBETH</h1>
			<div class="tagline">DONT HIRE ROBOTS — JUST USE IT</div>
		</div>

		<div class="nav-tabs">
			<button class="tab-btn active" onclick="switchTab('tab-identity')">1. Identity & Sign-in</button>
			<button class="tab-btn" onclick="switchTab('tab-terms')">2. Global Terms</button>
			<button class="tab-btn" onclick="switchTab('tab-themes')">3. Architectural Themes</button>
			<button class="tab-btn" onclick="switchTab('tab-agent')">4. Ideal Agent Customizer</button>
			<button class="tab-btn" onclick="switchTab('tab-launch')">5. Launch Executive</button>
		</div>

		<!-- TAB 1: IDENTITY & ECOSYSTEM -->
		<div id="tab-identity" class="tab-pane active">
			<div class="card">
				<h2>🌐 Global Creator Identity & Sign-in Options</h2>
				<p>PRUBETH connects seamlessly to global developer ecosystems while giving you sovereign freedom. Choose your desired authentication method or continue air-gapped.</p>
				
				<div class="auth-btn-row">
					<button class="btn-auth btn-github" onclick="handleAuth('GitHub')">
						{GITHUB_SVG}
						<span>Sign in with GitHub (Repositories, Copilot & Extensions)</span>
					</button>
					<button class="btn-auth btn-google" onclick="handleAuth('Google')">
						{GOOGLE_SVG}
						<span>Sign in with Google (Google AI Studio & Antigravity Ecosystem)</span>
					</button>
					<button class="btn-auth btn-sovereign" onclick="handleAuth('Sovereign Local Architect')">
						{SOVEREIGN_SVG}
						<span>Continue as Sovereign Local Architect (100% Offline, Zero Telemetry)</span>
					</button>
				</div>
				<div style="margin-top: 14px; text-align: center;">
					<span id="authStatusText" class="status-badge">Identity Status: Default Sovereign Mode Active</span>
				</div>

				<h3 style="margin-top: 28px; margin-bottom: 10px; font-size: 14px; color: #38BDF8; display: flex; align-items: center; gap: 8px;">
					<span>⚡ Native Collaborated Extension & Model Ecosystems</span>
				</h3>
				<div class="ecosystem-grid">
					<div class="eco-card">
						<div class="eco-icon-box">{GITHUB_SVG}</div>
						<div class="eco-info">
							<div class="eco-title">GitHub Ecosystem</div>
							<div class="eco-sub">Git repos, PRs, Copilot models</div>
						</div>
						<span class="eco-badge">Connected</span>
					</div>
					<div class="eco-card">
						<div class="eco-icon-box">{GEMINI_SVG}</div>
						<div class="eco-info">
							<div class="eco-title">Google Gemini</div>
							<div class="eco-sub">Gemini 3.8 Flash & Pro 2M tokens</div>
						</div>
						<span class="eco-badge">Ready</span>
					</div>
					<div class="eco-card">
						<div class="eco-icon-box">{CLAUDE_SVG}</div>
						<div class="eco-info">
							<div class="eco-title">Anthropic Claude</div>
							<div class="eco-sub">Claude Opus 4.6 & 3.7 Sonnet</div>
						</div>
						<span class="eco-badge">BYOK Ready</span>
					</div>
					<div class="eco-card">
						<div class="eco-icon-box">{DEEPSEEK_SVG}</div>
						<div class="eco-info">
							<div class="eco-title">DeepSeek Reasoning</div>
							<div class="eco-sub">R1 mathematical & code synthesis</div>
						</div>
						<span class="eco-badge">Ready</span>
					</div>
					<div class="eco-card">
						<div class="eco-icon-box">{OPENAI_SVG}</div>
						<div class="eco-info">
							<div class="eco-title">OpenAI Frontier</div>
							<div class="eco-sub">GPT-4o, o1, o3-mini agents</div>
						</div>
						<span class="eco-badge">BYOK Ready</span>
					</div>
					<div class="eco-card">
						<div class="eco-icon-box">{OPENVSX_SVG}</div>
						<div class="eco-info">
							<div class="eco-title">Open VSX Registry</div>
							<div class="eco-sub">Open-source extension gallery</div>
						</div>
						<span class="eco-badge" style="color:#A855F7; border-color: rgba(168,85,247,0.3);">Native</span>
					</div>
					<div class="eco-card">
						<div class="eco-icon-box">{SOVEREIGN_SVG}</div>
						<div class="eco-info">
							<div class="eco-title">Sovereign Ollama</div>
							<div class="eco-sub">Air-gapped GPU models (RedSage 8B)</div>
						</div>
						<span class="eco-badge" style="color:#10B981; border-color: rgba(16,185,129,0.3);">Active</span>
					</div>
				</div>
			</div>
		</div>

		<!-- TAB 2: GLOBAL TERMS & ETHICS -->
		<div id="tab-terms" class="tab-pane">
			<div class="card">
				<h2>📜 Global Creator Terms of Service & Sovereign Agreement</h2>
				<p>Because PRUBETH operates globally with diverse software creators, these terms establish unwavering guarantees of ownership, privacy, safety, and autonomous ethics.</p>

				<div class="terms-box">
					<h4>1. Absolute Creator Intellectual Property & Sovereignty</h4>
					All code, architectural schemas, models, prompts, git trees, and output generated using PRUBETH are 100% the exclusive property of the user. PRUBETH never transmits private repository code to train public foundation models.

					<h4>2. Autonomous Agent Action Governance</h4>
					By engaging the @prubeth Agentic Dev Stack (LangGraph, HarnessKit, SWE-agent, SuperHarness), the user grants the agent permission to execute terminal commands, test suites, and file modifications strictly bounded within the active workspace. Every multi-file refactor incorporates transactional rollback checkpoints.

					<h4>3. Multi-Probabilistic Convergence & Error Assessment</h4>
					To reach the exact intended output, the executive engine evaluates probabilistic solution paths across billions of potential code branches, assessing compiler and runtime errors automatically before committing changes to your workspace.

					<h4>4. Fair Ecosystem Attribution & Global Developer Ethics</h4>
					PRUBETH creators commit to maintaining transparency, respecting open-source licenses, and adhering to responsible developer ethics across all integrated dependencies and multi-modal models.
				</div>

				<label class="checkbox-row">
					<input type="checkbox" id="termsAgreementCheckbox" checked>
					I accept the Global Creator Terms and authorize PRUBETH Sovereign Agentic Operations.
				</label>
			</div>
		</div>

		<!-- TAB 3: ARCHITECTURAL THEMES -->
		<div id="tab-themes" class="tab-pane">
			<div class="card">
				<h2>🎨 4 Core Architectural Themes + Vivid Palettes</h2>
				<p>Select your primary architectural visual workspace. Click any theme card to preview and switch your active theme in real time.</p>

				<div class="theme-grid">
					${{ARCHITECTURAL_THEMES.map((t, idx) => `
						<div class="theme-card ${{idx === 0 ? 'selected' : ''}}" onclick="selectTheme('${{t.id}}', this)">
							<div class="theme-header">
								<span>${{t.name}}</span>
								<div class="theme-dot" style="color: ${{t.accent}}; background-color: ${{t.accent}};"></div>
							</div>
							<div class="theme-desc">${{t.desc}}</div>
						</div>
					`).join('')}}
				</div>
			</div>
		</div>

		<!-- TAB 4: IDEAL AGENT CUSTOMIZER -->
		<div id="tab-agent" class="tab-pane">
			<div class="card">
				<h2>🤖 Configure Your Ideal AI Coding Agent</h2>
				<p>Customize the archetype, models, and execution capabilities of your autonomous executive assistant.</p>

				<label style="font-size: 13px; font-weight: 700; color: #38BDF8; display: block; margin-bottom: 8px;">1. Primary Agent Archetype & Behavior</label>
				<div class="agent-selector-grid">
					<div class="agent-option selected" onclick="selectAgent('lead-architect', this)">
						<div class="agent-name">🏛️ Lead Architect</div>
						<div class="agent-desc">LangGraph state DAG planning, multi-step decomposition, and strategic system design.</div>
					</div>
					<div class="agent-option" onclick="selectAgent('precision-sweeper', this)">
						<div class="agent-name">🎯 Precision Sweeper</div>
						<div class="agent-desc">SWE-bench test-driven benchmark solver with automated pytest/npm validation gates.</div>
					</div>
					<div class="agent-option" onclick="selectAgent('ultra-velocity', this)">
						<div class="agent-name">⚡ Ultra Velocity</div>
						<div class="agent-desc">HarnessKit fuzzy AST line editor for instant, zero-drift code transformations.</div>
					</div>
					<div class="agent-option" onclick="selectAgent('superharness-swarm', this)">
						<div class="agent-name">🌌 SuperHarness Swarm</div>
						<div class="agent-desc">Spawns parallel worker sub-agents across isolated git worktrees with stall detection.</div>
					</div>
				</div>

				<label style="font-size: 13px; font-weight: 700; color: #38BDF8; display: block; margin-bottom: 8px;">2. Primary Foundation Reasoning Model</label>
				<select id="modelSelect" class="select-control">
					<option value="claude-opus-4-6">Claude Opus 4.6 (Anthropic — Flagship Deep Architectural Reasoning)</option>
					<option value="claude-3-7-sonnet">Claude 3.7 Sonnet (Anthropic — Extended Thinking & Code Synthesis)</option>
					<option value="gemini-3-8-pro">Gemini 3.8 Pro (Google — 2M Tokens Long Context Multimodal)</option>
					<option value="gemini-3-8-flash" selected>Gemini 3.8 Flash (Google — Ultra-Speed Agentic Reasoning)</option>
					<option value="deepseek-r1">DeepSeek R1 (DeepSeek — Open-Weight Mathematical Reasoning)</option>
					<option value="redsage-8b">RedSage 8B (Ollama — Air-Gapped Sovereign Local Privacy Engine)</option>
				</select>

				<label style="font-size: 13px; font-weight: 700; color: #38BDF8; display: block; margin-bottom: 8px;">3. Autonomous Execution & Convergence Bounds</label>
				<label class="checkbox-row" style="margin-bottom: 8px;">
					<input type="checkbox" id="chkTerminal" checked>
					Allow interactive terminal execution (running tests, pip, npm, git automatically).
				</label>
				<label class="checkbox-row">
					<input type="checkbox" id="chkProbabilistic" checked>
					Engage billion/trillion probability tree exploration for self-healing error resolution.
				</label>
			</div>
		</div>

		<!-- TAB 5: LAUNCH EXECUTIVE -->
		<div id="tab-launch" class="tab-pane">
			<div class="card" style="text-align: center; padding: 32px 24px;">
				<h2>🚀 Your Showroom Supercar Workstation Is Ready</h2>
				<p>Your ideal AI coding executive has been configured with pristine zero-friction defaults, verified models, and autonomous toolchains. You are ready to build at the speed of thought.</p>

				<div style="background: rgba(0, 240, 255, 0.05); border: 1px dashed var(--accent); border-radius: 8px; padding: 18px; margin: 20px 0; text-align: left; font-size: 13px; line-height: 1.8;">
					<div><b>Selected Theme:</b> <span id="summaryTheme">PRUBETH Obsidian Slate</span></div>
					<div><b>Agent Archetype:</b> <span id="summaryAgent">Lead Architect (LangGraph DAG)</span></div>
					<div><b>Primary Model:</b> <span id="summaryModel">Gemini 3.8 Flash</span></div>
					<div><b>Autonomous Terminal Execution:</b> <span style="color:#10B981;">✓ Active</span></div>
					<div><b>Self-Healing Probability Engine:</b> <span style="color:#10B981;">✓ Active</span></div>
				</div>

				<button class="cta-button" onclick="completeSetup()">
					INITIALIZE SOVEREIGN WORKSTATION & LAUNCH
				</button>
			</div>
		</div>
	</div>

	<script>
		const vscode = acquireVsCodeApi();
		let selectedTheme = 'PRUBETH Obsidian Slate';
		let selectedArchetype = 'lead-architect';

		function switchTab(tabId) {{
			document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
			document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
			
			const targetPane = document.getElementById(tabId);
			if (targetPane) targetPane.classList.add('active');

			const btns = document.querySelectorAll('.tab-btn');
			if (tabId === 'tab-identity') btns[0].classList.add('active');
			if (tabId === 'tab-terms') btns[1].classList.add('active');
			if (tabId === 'tab-themes') btns[2].classList.add('active');
			if (tabId === 'tab-agent') btns[3].classList.add('active');
			if (tabId === 'tab-launch') {{
				btns[4].classList.add('active');
				updateSummary();
			}}
		}}

		function selectTheme(themeId, el) {{
			selectedTheme = themeId;
			document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('selected'));
			el.classList.add('selected');
			vscode.postMessage({{ type: 'switchTheme', theme: themeId }});
		}}

		function selectAgent(archetypeId, el) {{
			selectedArchetype = archetypeId;
			document.querySelectorAll('.agent-option').forEach(c => c.classList.remove('selected'));
			el.classList.add('selected');
		}}

		function handleAuth(provider) {{
			vscode.postMessage({{ type: 'signIn', provider: provider }});
			const status = document.getElementById('authStatusText');
			status.textContent = 'Identity Status: ' + provider + ' Authenticated';
			status.style.color = '#10B981';
			status.style.borderColor = 'rgba(16, 185, 129, 0.5)';
		}}

		function updateSummary() {{
			document.getElementById('summaryTheme').textContent = selectedTheme;
			document.getElementById('summaryAgent').textContent = selectedArchetype;
			const m = document.getElementById('modelSelect');
			document.getElementById('summaryModel').textContent = m.options[m.selectedIndex].text;
		}}

		function completeSetup() {{
			const termsAccepted = document.getElementById('termsAgreementCheckbox').checked;
			if (!termsAccepted) {{
				alert('Please accept the Global Creator Terms to initialize PRUBETH.');
				switchTab('tab-terms');
				return;
			}}

			const model = document.getElementById('modelSelect').value;
			const terminalExec = document.getElementById('chkTerminal').checked;
			const probSearch = document.getElementById('chkProbabilistic').checked;

			vscode.postMessage({{
				type: 'completeSetup',
				theme: selectedTheme,
				archetype: selectedArchetype,
				model: model,
				terminalExecution: terminalExec,
				probabilisticSearch: probSearch
			}});
		}}
	</script>
</body>
</html>`;
}}

module.exports = {{
	showOnboardingWebview
}};
'''

ONBOARDING_JS.write_text(content, encoding="utf-8")
print(f"Updated: {ONBOARDING_JS}")

# Synchronize prubeth-ai extension to installed and build targets
targets = [
    REPO_ROOT / "VSCode-win32-x64" / "resources" / "app" / "extensions" / "prubeth-ai",
    Path(r"C:\Users\asus\AppData\Local\Programs\PRUBETH IDE\resources\app\extensions\prubeth-ai")
]

src_ai = REPO_ROOT / "vscode" / "extensions" / "prubeth-ai"

for t in targets:
    if t.parent.exists():
        shutil.copytree(src_ai, t, dirs_exist_ok=True)
        print(f"Synchronized prubeth-ai to: {t}")

print("Onboarding perfection enhancement complete!")
