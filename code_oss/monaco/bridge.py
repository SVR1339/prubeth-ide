"""
PRUBETH IDE — Code-OSS Monaco Editor Bridge
Provides Monaco editor HTML templates with custom Obsidian Slate theme, inline diff lens, and ghost text.
"""
from typing import Optional


class MonacoEditorBridge:
    """Renders self-contained Monaco editor workbench instances."""

    @staticmethod
    def generate_html(
        initial_code: str = "def hello():\n    print('PRUBETH Monaco Core')\n",
        language: str = "python",
        file_name: str = "sample.py",
        read_only: bool = False
    ) -> str:
        """Generates self-contained HTML hosting Monaco editor with Obsidian theme."""
        escaped_code = initial_code.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>PRUBETH Monaco Editor — {file_name}</title>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      background: #090c13;
      overflow: hidden;
      font-family: 'Segoe UI', -apple-system, sans-serif;
    }}
    #editor-container {{
      width: 100%;
      height: calc(100% - 30px);
    }}
    #editor-header {{
      height: 30px;
      background: #0d101a;
      border-bottom: 1px solid #1e2438;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 12px;
      font-size: 11px;
      color: #8fa0b8;
    }}
    .tag {{
      background: #141824;
      border: 1px solid #1e2438;
      padding: 2px 6px;
      border-radius: 4px;
      color: #00F0FF;
      font-family: monospace;
    }}
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs/loader.min.js"></script>
</head>
<body>
  <div id="editor-header">
    <div><b>PRUBETH Monaco Core</b> · {file_name}</div>
    <div class="tag">Language: {language} | Code-OSS v3.0.0</div>
  </div>
  <div id="editor-container"></div>

  <script>
    require.config({{ paths: {{ 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' }} }});
    require(['vs/editor/editor.main'], function() {{
      monaco.editor.defineTheme('obsidian-slate', {{
        base: 'vs-dark',
        inherit: true,
        rules: [
          {{ token: '', background: '090c13' }},
          {{ token: 'keyword', foreground: 'C084FC', fontStyle: 'bold' }},
          {{ token: 'identifier', foreground: 'F1F5F9' }},
          {{ token: 'string', foreground: '34D399' }},
          {{ token: 'number', foreground: 'F59E0B' }},
          {{ token: 'comment', foreground: '64748B', fontStyle: 'italic' }}
        ],
        colors: {{
          'editor.background': '#090c13',
          'editor.foreground': '#F1F5F9',
          'editor.lineHighlightBackground': '#141824',
          'editorCursor.foreground': '#00F0FF',
          'editorWhitespace.foreground': '#1E2438',
          'editorIndentGuide.background': '#1E2438',
          'editorIndentGuide.activeBackground': '#3B82F6',
          'editorLineNumber.foreground': '#475569',
          'editorLineNumber.activeForeground': '#00F0FF'
        }}
      }});

      window.editor = monaco.editor.create(document.getElementById('editor-container'), {{
        value: `{escaped_code}`,
        language: '{language}',
        theme: 'obsidian-slate',
        readOnly: {'true' if read_only else 'false'},
        automaticLayout: true,
        fontSize: 13,
        fontFamily: "'Cascadia Code', 'JetBrains Mono', Consolas, monospace",
        fontLigatures: true,
        minimap: {{ enabled: true }},
        scrollBeyondLastLine: false,
        cursorSmoothCaretAnimation: "on"
      }});
    }});
  </script>
</body>
</html>"""
