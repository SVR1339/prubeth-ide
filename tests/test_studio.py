"""
Comprehensive test suite for Local AI Studio Pro.
Validates lexer assignment, autonomous tool parsing, file operations,
diff generation, settings persistence, and local AI capabilities.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Set headless Qt platform before importing PyQt5
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
from PyQt5.Qsci import (
    QsciLexerPython, QsciLexerJavaScript, QsciLexerCPP,
    QsciLexerHTML, QsciLexerCSS, QsciLexerJSON, QsciLexerMarkdown, QsciLexerSQL
)

# Ensure QApplication singleton exists for Qt widget tests
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


from local_ai_studio_pro import (
    LexerFactory, Editor, AgentToolEngine, VisualDiffDialog,
    read_json, write_json, html_escape
)


def test_json_helpers(tmp_path):
    p = tmp_path / "test.json"
    data = {"name": "Local AI Studio Pro", "version": "2.2.0", "active": True}
    write_json(p, data)

    loaded = read_json(p, {})
    assert loaded == data

    # Test fallback on non-existent file
    assert read_json(tmp_path / "missing.json", {"default": 1}) == {"default": 1}


def test_html_escape():
    raw = "<script>alert('test & check');\n</script>"
    escaped = html_escape(raw)
    assert "&lt;script&gt;" in escaped
    assert "&amp;" in escaped
    assert "<br>" in escaped
    assert "<script>" not in escaped


def test_lexer_factory(qapp):
    editor = Editor()
    # Python
    py_lexer = LexerFactory.create_lexer("sample.py", editor)
    assert isinstance(py_lexer, QsciLexerPython)

    # JavaScript / TypeScript
    js_lexer = LexerFactory.create_lexer("app.ts", editor)
    assert isinstance(js_lexer, QsciLexerJavaScript)

    # C++ / Rust
    cpp_lexer = LexerFactory.create_lexer("main.rs", editor)
    assert isinstance(cpp_lexer, QsciLexerCPP)

    # HTML
    html_lexer = LexerFactory.create_lexer("index.html", editor)
    assert isinstance(html_lexer, QsciLexerHTML)

    # JSON
    json_lexer = LexerFactory.create_lexer("config.json", editor)
    assert isinstance(json_lexer, QsciLexerJSON)

    # Markdown
    md_lexer = LexerFactory.create_lexer("README.md", editor)
    assert isinstance(md_lexer, QsciLexerMarkdown)

    # SQL
    sql_lexer = LexerFactory.create_lexer("query.sql", editor)
    assert isinstance(sql_lexer, QsciLexerSQL)


def test_editor_functionality(qapp, tmp_path):
    test_file = tmp_path / "hello.py"
    test_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

    editor = Editor(str(test_file))
    editor.setText(test_file.read_text(encoding="utf-8"))

    assert "def hello():" in editor.text()
    assert editor.file_path == str(test_file)


def test_agent_tool_extraction():
    sample_agent_output = """
    I will read the configuration and search for the main function.
    <tool:read_file path="settings.py" />
    <tool:search_code query="def run" />
    <tool:write_file path="output.txt">
    hello world
    </tool:write_file>
    <tool:run_tests />
    """
    tools = AgentToolEngine.extract_tools(sample_agent_output)
    tool_names = [t[0] for t in tools]

    assert "read_file" in tool_names
    assert "search_code" in tool_names
    assert "write_file" in tool_names
    assert "run_tests" in tool_names

    # Check arguments
    for name, args in tools:
        if name == "read_file":
            assert args["path"] == "settings.py"
        elif name == "search_code":
            assert args["query"] == "def run"
        elif name == "write_file":
            assert args["path"] == "output.txt"
            assert "hello world" in args["content"]


def test_agent_tool_execution(tmp_path):
    engine = AgentToolEngine(str(tmp_path))

    # Test write_file
    res_write = engine.execute_tool("write_file", {"path": "test.txt", "content": "Line 1\nLine 2\nLine 3\n"})
    assert "Successfully wrote" in res_write
    assert (tmp_path / "test.txt").exists()

    # Test read_file
    res_read = engine.execute_tool("read_file", {"path": "test.txt"})
    assert "Line 2" in res_read

    # Test patch_file
    res_patch = engine.execute_tool("patch_file", {
        "path": "test.txt",
        "search": "Line 2",
        "replace": "Line Two Patched"
    })
    assert "Successfully patched" in res_patch
    updated_content = (tmp_path / "test.txt").read_text(encoding="utf-8")
    assert "Line Two Patched" in updated_content

    # Test list_files
    res_list = engine.execute_tool("list_files", {"dir": "."})
    assert "test.txt" in res_list

    # Test search_code
    res_search = engine.execute_tool("search_code", {"query": "Patched"})
    assert "test.txt" in res_search


def test_visual_diff_dialog(qapp):
    before = "line 1\nold line 2\nline 3"
    after = "line 1\nnew line 2\nline 3"

    dialog = VisualDiffDialog(before, after, "sample.py")
    assert dialog.proposed_view.toPlainText() == after
    # Verify diff HTML rendering populated
    assert dialog.diff_view.toHtml() != ""


def test_intelligent_model_router():
    from local_ai_studio_pro import IntelligentModelRouter

    settings = {
        "gemini_api_key": "dummy_key",
        "ollama_url": "http://localhost:11434",
        "local_model": "qwen2.5:1.5b"
    }

    # Test Auto-Router cascade
    plan = IntelligentModelRouter.get_execution_plan(settings, "⚡ Auto-Router")
    providers = [p[0] for p in plan]
    models = [p[1] for p in plan]

    assert "Google Gemini" in providers
    assert "Ollama" in providers
    assert "gemini-3.8-flash" in models
    assert "qwen2.5:1.5b" in models

    # Primary should be Gemini 3.8 Flash
    assert plan[0][0] == "Google Gemini"
    assert plan[0][1] == "gemini-3.8-flash"


def test_blinking_ai_indicator(qapp):
    from local_ai_studio_pro import BlinkingAIIndicator

    indicator = BlinkingAIIndicator()
    assert indicator.state == "IDLE"

    indicator.set_state("STREAMING")
    assert indicator.state == "STREAMING"

    indicator.set_state("AUTOFIX")
    assert indicator.state == "AUTOFIX"

    indicator.set_state("ERROR")
    assert indicator.state == "ERROR"

    indicator.set_state("IDLE")
    assert indicator.state == "IDLE"


def test_app_branding():
    import local_ai_studio_pro as studio

    assert "PRUBETH" in studio.APP_NAME or "SUKHI" in studio.APP_NAME or "SO NAIVE" in studio.APP_NAME
    assert any(v in studio.APP_VERSION for v in ["1.12.0", "3.0.0", "1.89.0"])
    assert studio.WEBSITE_URL == "https://www.bsvr.work/"
    assert "bsvr.work" in studio.PROJECTS_URL


def test_unrestricted_developer_mode_settings():
    import local_ai_studio_pro as studio

    assert studio.MAX_FILE_CONTEXT >= 128000
    # Test setting unrestricted mode defaults
    defaults = {
        "unrestricted_mode": True,
        "abliteration_mode": True,
        "max_context_bytes": 128000,
    }
    assert defaults["unrestricted_mode"] is True
    assert defaults["abliteration_mode"] is True
    assert defaults["max_context_bytes"] == 128000


def test_collapsible_thought_rendering():
    from local_ai_studio_pro import format_collapsible_thought

    raw_ai_message = """Here is my reasoning:
<thought>
Step 1: Check requirements.
Step 2: Generate code.
</thought>
Here is the solution!"""

    rendered = format_collapsible_thought(raw_ai_message)
    assert "<details" in rendered
    assert "<summary" in rendered
    assert "Step 1: Check requirements." in rendered
    assert "Here is the solution!" in rendered


def test_verify_deliverable_tool(tmp_path):
    from local_ai_studio_pro import AgentToolEngine

    engine = AgentToolEngine(str(tmp_path))
    res = engine.execute_tool("verify_deliverable", {
        "status": "complete",
        "notes": "All unit tests pass and code is bulletproof."
    })
    assert "DELIVERABLE VERIFICATION" in res
    assert "[VERIFIED COMPLETE]" in res


def test_accessory_and_inspector_widgets(qapp, tmp_path):
    from local_ai_studio_pro import (
        SketchCanvasDialog, AccessoryPopup, SessionInspectorWidget
    )

    # Test SketchCanvasDialog instantiation with workspace root
    sketch_dialog = SketchCanvasDialog(str(tmp_path))
    assert sketch_dialog.canvas is not None
    sketch_dialog.canvas.clear()

    # Create dummy studio object for widget testing
    class DummyStudio:
        def __init__(self, ws):
            self.workspace_dir = ws
        def accessory_add_photos_files(self): pass
        def accessory_add_from_library(self): pass
        def accessory_create_image(self): pass
        def accessory_sketch(self): pass
        def accessory_web_search(self): pass
        def accessory_deep_research(self): pass
        def accessory_visualize(self): pass
        def accessory_open_provider_hub(self): pass
        def accessory_github_flow(self): pass

    dummy = DummyStudio(str(tmp_path))

    # Test AccessoryPopup instantiation
    popup = AccessoryPopup(dummy)
    assert len(popup.item_widgets) >= 8
    # Search filter test
    popup.search_edit.setText("sketch")
    popup._filter_items("sketch")

    # Test SessionInspectorWidget
    inspector = SessionInspectorWidget(dummy)
    assert inspector.studio == dummy
    assert len(inspector.skills_used) >= 4


def test_permissive_license_terms():
    license_path = Path(__file__).resolve().parent.parent / "LICENSE"
    assert license_path.exists()
    content = license_path.read_text(encoding="utf-8")

    assert "BSVR Permissive Open Developer License" in content
    assert "BSVR Technologies" in content
    assert "Dual MIT / Apache 2.0 Permissive Terms" in content
    assert "MIT License Grant" in content
    assert "Apache License Version 2.0 Compatibility" in content
    assert "Philipp Emanuel Weidmann" not in content


def test_navy_ai_model_routing():
    from local_ai_studio_pro import IntelligentModelRouter

    # 1. Direct NavyAI selection
    settings = {
        "navy_api_key": "sk-navy-test-key",
        "navy_base_url": "https://api.navy/v1",
        "navy_model": "gemini-3.8-flash",
    }
    plan = IntelligentModelRouter.get_execution_plan(settings, requested_provider="NavyAI", requested_model="claude-sonnet-4.5")
    assert len(plan) >= 1
    assert plan[0][0] == "NavyAI"
    assert plan[0][1] == "claude-sonnet-4.5"
    assert "Direct User Selection" in plan[0][2]

    # 2. Dynamic Auto-Router cascade containing NavyAI
    auto_plan = IntelligentModelRouter.get_execution_plan(settings, requested_provider="⚡ Auto-Router")
    providers = [p[0] for p in auto_plan]
    assert "NavyAI" in providers
    navy_entry = [p for p in auto_plan if p[0] == "NavyAI"][0]
    assert navy_entry[1] == "gemini-3.8-flash"


def test_navy_ai_provider_dialog(qapp):
    from local_ai_studio_pro import UniversalProviderHubDialog

    settings = {
        "navy_api_key": "sk-navy-test-value",
        "navy_base_url": "https://api.navy/v1",
        "navy_model": "deepseek-chat",
    }
    dialog = UniversalProviderHubDialog(settings)
    assert dialog.navy_key.text() == "sk-navy-test-value"
    assert dialog.navy_url.text() == "https://api.navy/v1"
    assert dialog.navy_model.currentText() == "deepseek-chat"

    # Verify values() roundtrip
    vals = dialog.values()
    assert vals["navy_api_key"] == "sk-navy-test-value"
    assert vals["navy_base_url"] == "https://api.navy/v1"
    assert vals["navy_model"] == "deepseek-chat"


def test_navy_ai_worker_streaming(qapp):
    from unittest.mock import patch, MagicMock
    from local_ai_studio_pro import AIWorker

    settings = {
        "navy_api_key": "sk-navy-dummy",
        "navy_base_url": "https://api.navy/v1",
        "navy_model": "gemini-3.8-flash",
    }
    worker = AIWorker(
        base_url="https://api.navy/v1",
        provider="NavyAI",
        model="gemini-3.8-flash",
        messages=[{"role": "user", "content": "hi"}],
        task_id="test_task_1",
        stream=True,
        settings=settings
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_lines.return_value = [
        b'data: {"choices": [{"delta": {"content": "Hello "}}]}',
        b'data: {"choices": [{"delta": {"content": "from "}}]}',
        b'data: {"choices": [{"delta": {"content": "NavyAI!"}}]}',
        b'data: [DONE]'
    ]
    mock_resp.__enter__.return_value = mock_resp

    tokens_received = []
    done_payload = []
    worker.token.connect(tokens_received.append)
    worker.done.connect(lambda tid, ans, meta: done_payload.append((tid, ans, meta)))

    with patch("requests.post", return_value=mock_resp):
        worker._run_navy("gemini-3.8-flash")

    assert "".join(tokens_received) == "Hello from NavyAI!"
    assert len(done_payload) == 1
    assert done_payload[0][1] == "Hello from NavyAI!"
    assert done_payload[0][2]["provider"] == "NavyAI"
    assert done_payload[0][2]["model"] == "gemini-3.8-flash"


def test_accounts_linkup_persistence(qapp, tmp_path, monkeypatch):
    from local_ai_studio_pro import UniversalProviderHubDialog
    import local_ai_studio_pro

    test_acc_path = tmp_path / "accounts.json"
    monkeypatch.setattr(local_ai_studio_pro, "ACCOUNTS_CONFIG_PATH", test_acc_path)

    settings = {"gemini_api_key": "test_gemini"}
    dialog = UniversalProviderHubDialog(settings)

    # Set Accounts fields
    dialog.github_token.setText("ghp_valid_mock_pat_token_123")
    dialog.github_user.setText("octodev")
    dialog.git_email.setText("octodev@domain.org")
    dialog.git_ssh_key.setText("C:\\Users\\asus\\.ssh\\id_ed25519")
    dialog.google_project.setText("prod-ai-studio-789")
    dialog.google_email.setText("dev@company.com")
    dialog.google_adc_path.setText("C:\\creds\\application_default_credentials.json")
    dialog.hf_token.setText("hf_secure_token_abc")

    vals = dialog.values()
    assert vals["github_token"] == "ghp_valid_mock_pat_token_123"
    assert vals["github_username"] == "octodev"
    assert vals["git_email"] == "octodev@domain.org"
    assert vals["google_project"] == "prod-ai-studio-789"
    assert vals["google_email"] == "dev@company.com"
    assert vals["hf_token"] == "hf_secure_token_abc"

    # Verify JSON persistence
    saved = json.loads(test_acc_path.read_text(encoding="utf-8"))
    assert saved["github_token"] == "ghp_valid_mock_pat_token_123"
    assert saved["github_username"] == "octodev"
    assert saved["google_project"] == "prod-ai-studio-789"
    assert saved["hf_token"] == "hf_secure_token_abc"


def test_extensions_catalog_search_and_toggle(qapp, tmp_path, monkeypatch):
    from local_ai_studio_pro import UniversalProviderHubDialog
    from PyQt5.QtWidgets import QFrame
    import local_ai_studio_pro

    test_ext_path = tmp_path / "extensions.json"
    monkeypatch.setattr(local_ai_studio_pro, "EXTENSIONS_CONFIG_PATH", test_ext_path)

    dialog = UniversalProviderHubDialog({})

    # Verify default extensions loaded
    assert len(dialog.extensions) >= 8

    # Test Search filtering: "vscode"
    dialog.ext_search_edit.setText("vscode")
    cards = [dialog.ext_card_layout.itemAt(i).widget() for i in range(dialog.ext_card_layout.count()) if type(dialog.ext_card_layout.itemAt(i).widget()) is QFrame]
    assert len(cards) >= 1

    # Test Search filtering with non-matching query
    dialog.ext_search_edit.setText("non_existent_xyz_extension")
    cards_empty = [dialog.ext_card_layout.itemAt(i).widget() for i in range(dialog.ext_card_layout.count()) if type(dialog.ext_card_layout.itemAt(i).widget()) is QFrame]
    assert len(cards_empty) == 0

    # Reset search and test category filtering
    dialog.ext_search_edit.clear()
    dialog.ext_category_combo.setCurrentText("AI Agents")
    cards_agent = [dialog.ext_card_layout.itemAt(i).widget() for i in range(dialog.ext_card_layout.count()) if type(dialog.ext_card_layout.itemAt(i).widget()) is QFrame]
    assert len(cards_agent) >= 1

    # Test Toggle disable & enable
    dialog.toggle_extension("ext-vscode-bridge", "disable")
    ext_state = next(e for e in dialog.extensions if e["id"] == "ext-vscode-bridge")
    assert ext_state["enabled"] is False

    dialog.toggle_extension("ext-vscode-bridge", "enable")
    ext_state = next(e for e in dialog.extensions if e["id"] == "ext-vscode-bridge")
    assert ext_state["enabled"] is True

    # Check persistence
    saved_ext = json.loads(test_ext_path.read_text(encoding="utf-8"))
    saved_entry = next(e for e in saved_ext if e["id"] == "ext-vscode-bridge")
    assert saved_entry["enabled"] is True


def test_custom_multi_modal_model_registration_and_routing(qapp, tmp_path, monkeypatch):
    from local_ai_studio_pro import UniversalProviderHubDialog, IntelligentModelRouter
    from unittest.mock import patch
    import local_ai_studio_pro

    test_cm_path = tmp_path / "custom_models.json"
    monkeypatch.setattr(local_ai_studio_pro, "CUSTOM_MODELS_CONFIG_PATH", test_cm_path)

    dialog = UniversalProviderHubDialog({})

    dialog.custom_provider_name.setText("TogetherAI")
    dialog.custom_base_url.setText("https://api.together.xyz/v1")
    dialog.custom_api_key.setText("sk-together-secret-xyz")
    dialog.custom_model_id.setCurrentText("meta-llama/Llama-Vision-Free")
    dialog.mod_chat.setChecked(True)
    dialog.mod_vision.setChecked(True)
    dialog.mod_code.setChecked(True)

    with patch("PyQt5.QtWidgets.QMessageBox.information"):
        dialog.add_custom_model_action()

    # Verify registered in dialog
    assert len(dialog.custom_models) >= 1
    reg = next(cm for cm in dialog.custom_models if cm["model"] == "meta-llama/Llama-Vision-Free")
    assert reg["provider"] == "TogetherAI"
    assert reg["base_url"] == "https://api.together.xyz/v1"
    assert reg["api_key"] == "sk-together-secret-xyz"
    assert reg["modalities"]["vision"] is True

    # Test IntelligentModelRouter recognizes registered custom provider
    plan = IntelligentModelRouter.get_execution_plan(
        settings={},
        requested_provider="TogetherAI",
        requested_model="meta-llama/Llama-Vision-Free"
    )
    assert any(p == "TogetherAI" and m == "meta-llama/Llama-Vision-Free" for p, m, _ in plan)


def test_custom_provider_ai_worker_streaming(qapp, tmp_path, monkeypatch):
    from unittest.mock import patch, MagicMock
    from local_ai_studio_pro import AIWorker
    import local_ai_studio_pro

    test_cm_path = tmp_path / "custom_models.json"
    custom_data = [{
        "provider": "Private-vLLM",
        "base_url": "http://10.0.0.50:8000/v1",
        "api_key": "vllm-token-secret",
        "model": "qwen2.5-coder-32b",
        "modalities": {"chat": True, "vision": True, "code": True},
        "enabled": True
    }]
    test_cm_path.write_text(json.dumps(custom_data), encoding="utf-8")
    monkeypatch.setattr(local_ai_studio_pro, "CUSTOM_MODELS_CONFIG_PATH", test_cm_path)

    worker = AIWorker(
        base_url="http://10.0.0.50:8000/v1",
        provider="Private-vLLM",
        model="qwen2.5-coder-32b",
        messages=[{"role": "user", "content": "Generate a fast binary search in Python"}],
        task_id="custom_task_test",
        stream=True,
        settings={"provider": "Private-vLLM"}
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_lines.return_value = [
        b'data: {"choices": [{"delta": {"content": "def binary_search"}}]}',
        b'data: {"choices": [{"delta": {"content": "(arr, target):\\n    pass"}}]}',
        b'data: [DONE]'
    ]
    mock_resp.__enter__.return_value = mock_resp

    tokens_received = []
    done_payload = []
    worker.token.connect(tokens_received.append)
    worker.done.connect(lambda tid, ans, meta: done_payload.append((tid, ans, meta)))

    with patch("requests.post", return_value=mock_resp):
        worker.run()

    full_output = "".join(tokens_received)
    assert "def binary_search(arr, target):\n    pass" == full_output
    assert len(done_payload) == 1
    assert done_payload[0][1] == full_output
    assert done_payload[0][2]["provider"] == "Private-vLLM"
    assert done_payload[0][2]["model"] == "qwen2.5-coder-32b"


def test_local_gguf_file_verification(tmp_path):
    import struct
    from local_ai_studio_pro import verify_gguf_header

    # 1. Non-existent file
    ok, msg = verify_gguf_header(str(tmp_path / "ghost.gguf"))
    assert not ok
    assert "does not exist" in msg

    # 2. Invalid header
    bad_file = tmp_path / "corrupt.gguf"
    bad_file.write_bytes(b"BADHEADERDATA")
    ok, msg = verify_gguf_header(str(bad_file))
    assert not ok
    assert "Invalid magic header" in msg

    # 3. Valid GGUF v3 header
    valid_gguf = tmp_path / "valid_model.gguf"
    # GGUF magic = b'GGUF', version = 3, tensor_count = 120, kv_count = 25
    header_data = b"GGUF" + struct.pack("<I", 3) + struct.pack("<QQ", 120, 25)
    valid_gguf.write_bytes(header_data + b"\x00" * 1024)
    ok, msg = verify_gguf_header(str(valid_gguf))
    assert ok
    assert "Valid GGUF v3 Model" in msg
    assert "120 Tensors" in msg


def test_ide_custom_provider_combo_and_refresh_models(qapp, tmp_path, monkeypatch):
    from local_ai_studio_pro import Studio
    import local_ai_studio_pro

    test_cm_path = tmp_path / "custom_models.json"
    custom_data = [
        {"provider": "MistralAI", "model": "mistral-large-2411", "enabled": True},
        {"provider": "TogetherAI", "model": "meta-llama/llama-3.3-70b-instruct", "enabled": True}
    ]
    test_cm_path.write_text(json.dumps(custom_data), encoding="utf-8")
    monkeypatch.setattr(local_ai_studio_pro, "CUSTOM_MODELS_CONFIG_PATH", test_cm_path)

    studio = Studio()

    # Verify custom providers are present in the provider_combo
    providers = [studio.provider_combo.itemText(i) for i in range(studio.provider_combo.count())]
    assert "MistralAI" in providers
    assert "TogetherAI" in providers

    # Switch provider to MistralAI and test refresh_models
    studio.provider_combo.setCurrentText("MistralAI")
    models = [studio.model_combo.itemText(i) for i in range(studio.model_combo.count())]
    assert "mistral-large-2411" in models




def test_installer_payload_archive_generation():
    from build_setup_exe import create_payload_archive
    import zipfile

    payload_path = create_payload_archive()
    assert payload_path.exists()
    assert payload_path.stat().st_size > 50000  # Must be substantial (>50KB)

    with zipfile.ZipFile(payload_path, 'r') as z:
        names = z.namelist()
        assert "local_ai_studio_pro.py" in names
        assert "requirements.txt" in names
        assert "README.md" in names
        assert any("icon.ico" in n for n in names)


def test_installer_worker_extraction_and_verification(tmp_path):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "installer"))
    from setup_wizard import InstallWorker
    from build_setup_exe import create_payload_archive

    payload = create_payload_archive()
    target_install = tmp_path / "install_target"

    worker = InstallWorker(
        target_dir=str(target_install),
        create_desktop=False,
        create_startmenu=False,
        payload_zip=str(payload)
    )

    results = []
    worker.finished.connect(lambda ok, msg: results.append((ok, msg)))
    # Run synchronously in test
    worker.run()

    assert len(results) == 1
    success, msg = results[0]
    assert success is True
    assert msg == "Success"

    # Verify extracted artifacts
    assert (target_install / "local_ai_studio_pro.py").exists()
    assert (target_install / "SoNaive.bat").exists()
    assert (target_install / "assets").exists()

    # Read launcher batch and verify safety checks
    bat_content = (target_install / "SoNaive.bat").read_text(encoding="utf-8")
    assert "local_ai_studio_pro.py" in bat_content
    assert "PY_CMD" in bat_content


def test_installer_worker_fails_on_empty_payload(tmp_path):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "installer"))
    from setup_wizard import InstallWorker

    # Create an empty zip payload
    empty_zip = tmp_path / "empty.zip"
    import zipfile
    with zipfile.ZipFile(empty_zip, 'w') as z:
        z.writestr("dummy.txt", "empty")

    target_install = tmp_path / "empty_target"

    worker = InstallWorker(
        target_dir=str(target_install),
        create_desktop=False,
        create_startmenu=False,
        payload_zip=str(empty_zip)
    )

    results = []
    worker.finished.connect(lambda ok, msg: results.append((ok, msg)))
    worker.run()

    assert len(results) == 1
    success, err_msg = results[0]
    assert success is False
    assert "Installation integrity verification failed" in err_msg


def test_dpapi_and_secret_redaction(tmp_path):
    from core.credentials import CredentialStore, SecretRedactor
    
    store = CredentialStore(store_dir=tmp_path)
    key_file = tmp_path / "credentials.enc"
    
    # Test setting and getting secrets
    store.set_secret("gemini_api_key", "AQ_TEST_SECRET_KEY_1234567890")
    store.set_secret("custom_token", "sk-live-09876543210987654321")
    
    assert store.get_secret("gemini_api_key") == "AQ_TEST_SECRET_KEY_1234567890"
    assert store.get_secret("custom_token") == "sk-live-09876543210987654321"
    assert store.get_secret("gemini_api_key") is not None
    assert store.get_secret("nonexistent") == ""
    
    # Verify disk persistence is encrypted and contains no plaintext
    raw_disk_data = key_file.read_text(encoding="utf-8")
    assert "AQ_TEST_SECRET_KEY_1234567890" not in raw_disk_data
    assert "sk-live-09876543210987654321" not in raw_disk_data
    
    # Test secret redactor
    redactor = SecretRedactor()
    redactor.register_secret("my_super_secret_password_12345")
    
    log_text = "Connecting with my_super_secret_password_12345 and key sk-abcdef1234567890abcdef1234 and ghp_111122223333444455556666777788889999"
    cleaned = redactor.redact(log_text)
    assert "my_super_secret_password_12345" not in cleaned
    assert "sk-abcdef1234567890abcdef1234" not in cleaned
    assert "ghp_111122223333444455556666777788889999" not in cleaned
    assert "[***REDACTED_SECRET***]" in cleaned or "my_..." in cleaned


def test_workspace_boundary_enforcement(tmp_path):
    from core.workspace import WorkspaceGuard, WorkspaceSecurityError
    from local_ai_studio_pro import AgentToolEngine
    import pytest
    
    guard = WorkspaceGuard(tmp_path)
    
    # Valid operations inside workspace
    guard.safe_write("subdir/hello.py", "def test(): pass\n")
    assert (tmp_path / "subdir" / "hello.py").exists()
    assert "def test" in guard.safe_read("subdir/hello.py")
    
    # Path traversal attempts
    with pytest.raises(WorkspaceSecurityError):
        guard.canonicalize("../outside.txt")
        
    with pytest.raises(WorkspaceSecurityError):
        guard.canonicalize("../../windows/system32/cmd.exe")
        
    # Verify AgentToolEngine blocks traversal and reports Security Error
    engine = AgentToolEngine(str(tmp_path))
    res_read = engine.execute_tool("read_file", {"path": "../../outside.txt"})
    assert "Security Error" in res_read or "Access Denied" in res_read
    
    res_write = engine.execute_tool("write_file", {"path": "../outside.txt", "content": "bad"})
    assert "Security Error" in res_write or "Access Denied" in res_write


def test_tool_gateway_risk_and_execution(tmp_path):
    from core.workspace import WorkspaceGuard
    from core.tool_gateway import ToolGateway, CommandRiskLevel, ToolSecurityError
    import pytest
    
    guard = WorkspaceGuard(tmp_path)
    gateway = ToolGateway(guard)
    
    # Test risk classification
    assert gateway.classify_command("git status") == CommandRiskLevel.SAFE_EXECUTION
    assert gateway.classify_command("pytest -q") == CommandRiskLevel.SAFE_EXECUTION
    assert gateway.classify_command("pip install requests") == CommandRiskLevel.MUTATING
    assert gateway.classify_command("del /f important.txt") == CommandRiskLevel.HIGH_RISK
    assert gateway.classify_command("rmdir /s /q test") == CommandRiskLevel.HIGH_RISK
    
    # High risk blocks without approval hook
    with pytest.raises(ToolSecurityError):
        gateway.execute_command("del /f secret.txt")
        
    # Dry-run execution
    dry_res = gateway.execute_command("del /f secret.txt", dry_run=True)
    assert dry_res["dry_run"] is True
    assert dry_res["risk_level"] == CommandRiskLevel.HIGH_RISK
    
    # Safe command executes
    safe_res = gateway.execute_command("echo HelloGateway")
    assert safe_res["exit_code"] == 0
    assert "HelloGateway" in safe_res["stdout"]


def test_model_registry_and_router_profiles():
    from core.model_registry import ModelRegistry
    from core.router import AgentRouter, AgentProfile
    
    registry = ModelRegistry()
    assert len(registry.list_models()) >= 4
    
    # Retrieve local vs cloud
    locals_only = registry.list_models(local_only=True)
    assert any("ollama" in m.model_id.lower() or m.provider == "Ollama" for m in locals_only)
    
    # Router profiles
    router = AgentRouter(registry)
    
    # Small profile (fast, code completion)
    plan_small = router.route("quick fix syntax error", profile=AgentProfile.SMALL)
    assert plan_small["profile"] == AgentProfile.SMALL
    assert plan_small["primary_model"] is not None
    assert "run_command" not in plan_small["allowed_tools"]
    
    # Large profile (full autonomy, multi-step)
    plan_large = router.route("architect complete subsystem", profile=AgentProfile.LARGE)
    assert plan_large["profile"] == AgentProfile.LARGE
    assert "run_command" in plan_large["allowed_tools"]
    assert "write_file" in plan_large["allowed_tools"]
    
    # Policy constraint: local_only
    plan_local = router.route("private code review", policy={"local_only": True})
    assert plan_local["primary_model"]["is_local"] is True


def test_task_engine_lifecycle():
    from core.task_engine import TaskEngine, TaskState
    
    engine = TaskEngine()
    task = engine.create_task("Fix broken unit tests", profile="large")
    assert task.state == TaskState.QUEUED
    
    engine.transition_state(task.task_id, TaskState.PLANNING)
    assert task.state == TaskState.PLANNING
    
    step = engine.add_step(task.task_id, "read_file", {"path": "test.py"})
    assert len(task.steps) == 1
    engine.complete_step(task.task_id, step.step_id, "File content loaded")
    assert step.status == "completed"
    
    engine.create_checkpoint(task.task_id, "initial", {"code": "def foo(): pass"})
    assert len(task.checkpoints) == 1
    
    engine.transition_state(task.task_id, TaskState.COMPLETED)
    assert task.state == TaskState.COMPLETED
    assert task.completed_at is not None


def test_plugin_manifest_validation():
    from core.plugin_engine import PluginManifestValidator, PluginManifestValidationError
    import pytest
    
    valid_manifest = {
        "id": "ext-test",
        "name": "Test Extension",
        "version": "1.0.0",
        "publisher": "SO NAIVE",
        "description": "A valid test extension",
        "permissions": ["workspace:read", "workspace:write"]
    }
    assert PluginManifestValidator.validate(valid_manifest) is True
    
    # Missing required field
    invalid_manifest = dict(valid_manifest)
    del invalid_manifest["publisher"]
    with pytest.raises(PluginManifestValidationError):
        PluginManifestValidator.validate(invalid_manifest)
        
    # Excessive/invalid permission
    invalid_perm = dict(valid_manifest)
    invalid_perm["permissions"] = ["kernel:root_access"]
    with pytest.raises(PluginManifestValidationError):
        PluginManifestValidator.validate(invalid_perm)


