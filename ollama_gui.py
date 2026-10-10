"""
[STANDALONE COMPANION] Local AI Companion Chat — Lightweight Ollama Assistant
NOTE: For the full-featured SO NAIVE IDE (v3.0.0 Horizon Edition), run local_ai_studio_pro.py.
Features: Real-time streaming token generation, automatic model discovery,
system persona presets, copy-to-clipboard, and performance throughput metrics.
"""
import sys
import threading
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import requests

OLLAMA_BASE = "http://localhost:11434"

SYSTEM_PROMPTS = {
    "Code Assistant": "You are an expert programming assistant. Provide precise, clean, idiomatic code with clear explanations.",
    "System Architect": "You are a senior software architect. Analyze system designs, scalability, trade-offs, and design patterns.",
    "Concise / Fast": "Provide direct, ultra-concise answers with minimal fluff.",
    "Creative / Brainstorm": "Help brainstorm creative concepts, naming ideas, and architectural approaches."
}


class OllamaChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local AI Companion — Streaming Assistant")
        self.root.geometry("860x680")
        self.root.minsize(580, 440)
        self.root.configure(bg="#0e131f")

        self.models = []
        self.current_stream_cancel = False

        self._build_ui()
        self._load_models_async()

    def _build_ui(self):
        # Header Toolbar
        top_bar = tk.Frame(self.root, bg="#141a29", padx=12, pady=10)
        top_bar.pack(fill=tk.X)

        lbl_title = tk.Label(top_bar, text="Local AI Companion", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#141a29")
        lbl_title.pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(top_bar, text="Model:", font=("Segoe UI", 10), fg="#a0b2cc", bg="#141a29").pack(side=tk.LEFT)
        self.model_combo = ttk.Combobox(top_bar, width=18, state="readonly")
        self.model_combo.pack(side=tk.LEFT, padx=6)

        tk.Label(top_bar, text="Persona:", font=("Segoe UI", 10), fg="#a0b2cc", bg="#141a29").pack(side=tk.LEFT, padx=(10, 0))
        self.persona_combo = ttk.Combobox(top_bar, values=list(SYSTEM_PROMPTS.keys()), width=16, state="readonly")
        self.persona_combo.current(0)
        self.persona_combo.pack(side=tk.LEFT, padx=6)

        self.btn_refresh = tk.Button(top_bar, text="⟳", font=("Segoe UI", 9, "bold"), bg="#1c2538", fg="#dce7fa", bd=1, command=self._load_models_async)
        self.btn_refresh.pack(side=tk.LEFT, padx=4)

        self.lbl_conn = tk.Label(top_bar, text="● Connecting…", font=("Segoe UI", 9, "bold"), fg="#ffcb6b", bg="#141a29")
        self.lbl_conn.pack(side=tk.RIGHT)

        # Chat Transcript Area
        self.chat = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Cascadia Code", 10),
            bg="#080c14",
            fg="#dce7fa",
            insertbackground="#5aa7ff",
            padx=14,
            pady=14,
            bd=0,
            highlightthickness=1,
            highlightbackground="#1c283c"
        )
        self.chat.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Message Tags
        self.chat.tag_config("user", foreground="#5aa7ff", font=("Segoe UI", 10, "bold"))
        self.chat.tag_config("ai", foreground="#75e09f", font=("Segoe UI", 10, "bold"))
        self.chat.tag_config("body", foreground="#dce7fa", font=("Cascadia Code", 10))
        self.chat.tag_config("sys", foreground="#61748f", font=("Segoe UI", 9, "italic"))

        # Input Area
        bottom = tk.Frame(self.root, bg="#0e131f", padx=12, pady=8)
        bottom.pack(fill=tk.X)

        self.entry = tk.Text(
            bottom,
            height=3,
            font=("Segoe UI", 10),
            bg="#131a29",
            fg="#ffffff",
            insertbackground="#5aa7ff",
            bd=1,
            relief=tk.SOLID,
            wrap=tk.WORD
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.entry.bind("<Control-Return>", self.send_message)

        btn_box = tk.Frame(bottom, bg="#0e131f")
        btn_box.pack(side=tk.RIGHT)

        self.btn_send = tk.Button(btn_box, text="Send\n(Ctrl+Enter)", font=("Segoe UI", 9, "bold"), bg="#186036", fg="#ffffff", bd=0, padx=12, pady=6, command=self.send_message)
        self.btn_send.pack(fill=tk.X, pady=(0, 4))

        self.btn_clear = tk.Button(btn_box, text="Clear Chat", font=("Segoe UI", 8), bg="#222f46", fg="#dce7fa", bd=0, command=self.clear_chat)
        self.btn_clear.pack(fill=tk.X)

        # Status Footer
        footer = tk.Frame(self.root, bg="#101622", padx=12, pady=4)
        footer.pack(fill=tk.X)

        self.status = tk.Label(footer, text="Ready", font=("Segoe UI", 9), fg="#8fa4c2", bg="#101622", anchor="w")
        self.status.pack(side=tk.LEFT)

        self.stats_lbl = tk.Label(footer, text="", font=("Segoe UI", 9), fg="#75e09f", bg="#101622", anchor="e")
        self.stats_lbl.pack(side=tk.RIGHT)

        self._append_text("System", "Welcome to Local AI Companion. Ollama streaming is enabled.", "sys")
        self.entry.focus_set()

    def _append_text(self, sender, text, tag="body"):
        self.chat.configure(state=tk.NORMAL)
        if sender:
            self.chat.insert(tk.END, f"\n{sender}\n", tag if tag in ("user", "ai", "sys") else "user")
        self.chat.insert(tk.END, f"{text}\n", "body" if tag != "sys" else "sys")
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _load_models_async(self):
        self.lbl_conn.configure(text="● Checking…", fg="#ffcb6b")
        threading.Thread(target=self._fetch_models, daemon=True).start()

    def _fetch_models(self):
        try:
            r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", []) if m.get("name")]
            self.root.after(0, self._on_models_loaded, models)
        except Exception:
            self.root.after(0, self._on_models_failed)

    def _on_models_loaded(self, models):
        self.models = models or ["qwen2.5:1.5b"]
        self.model_combo["values"] = self.models
        if self.models:
            self.model_combo.current(0)
        self.lbl_conn.configure(text="● Online", fg="#75e09f")
        self.status.configure(text=f"Connected to Ollama ({len(self.models)} model(s) available)")

    def _on_models_failed(self):
        self.model_combo["values"] = ["qwen2.5:1.5b"]
        self.model_combo.set("qwen2.5:1.5b")
        self.lbl_conn.configure(text="● Offline", fg="#ff8585")
        self.status.configure(text="Ollama is unreachable. Please verify Ollama is running.")

    def clear_chat(self):
        self.chat.configure(state=tk.NORMAL)
        self.chat.delete("1.0", tk.END)
        self.chat.configure(state=tk.DISABLED)
        self._append_text("System", "Chat history cleared.", "sys")

    def send_message(self, event=None):
        prompt = self.entry.get("1.0", tk.END).strip()
        if not prompt:
            return "break"

        self.entry.delete("1.0", tk.END)
        self._append_text("You", prompt, "user")

        model = self.model_combo.get() or "qwen2.5:1.5b"
        persona = self.persona_combo.get()
        system = SYSTEM_PROMPTS.get(persona, "")

        self.btn_send.configure(state=tk.DISABLED)
        self.status.configure(text=f"Generating with {model}…")
        self.stats_lbl.configure(text="")

        threading.Thread(target=self._stream_response, args=(model, system, prompt), daemon=True).start()
        return "break"

    def _stream_response(self, model, system, prompt):
        start_time = time.time()
        token_count = 0
        self.root.after(0, self._start_ai_entry)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.2}
        }

        try:
            with requests.post(f"{OLLAMA_BASE}/api/chat", json=payload, stream=True, timeout=(6, 180)) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    chunk = requests.compat.json.loads(line.decode("utf-8"))
                    text = chunk.get("message", {}).get("content", "")
                    if text:
                        token_count += 1
                        self.root.after(0, self._insert_chunk, text)
                    if chunk.get("done"):
                        break

            elapsed = max(0.001, time.time() - start_time)
            rate = token_count / elapsed
            self.root.after(0, self._finish_ai_entry, token_count, rate)
        except Exception as ex:
            self.root.after(0, self._fail_ai_entry, str(ex))

    def _start_ai_entry(self):
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "\nAI Copilot\n", "ai")
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _insert_chunk(self, chunk):
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, chunk, "body")
        self.chat.configure(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _finish_ai_entry(self, count, rate):
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, "\n")
        self.chat.configure(state=tk.DISABLED)
        self.btn_send.configure(state=tk.NORMAL)
        self.status.configure(text="Ready")
        self.stats_lbl.configure(text=f"{count} tokens | {rate:.1f} tok/s")
        self.entry.focus_set()

    def _fail_ai_entry(self, err):
        self._append_text("System", f"Ollama error: {err}", "sys")
        self.btn_send.configure(state=tk.NORMAL)
        self.status.configure(text="Generation failed")
        self.entry.focus_set()


if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaChatApp(root)
    root.mainloop()
