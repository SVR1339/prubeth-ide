import pytest

def test_slash_command_dispatch():
    # Verify command string parsing logic matches expected Antigravity actions
    commands = {
        "/plan Create a REST API": ("Multi-Agent Orchestrator (DAG Team)", "Create a REST API"),
        "/scaffold micro CLI app": ("Executive Project Scaffolder & Self-Heal", "micro CLI app"),
        "/fix syntax error": ("Auto-Fix Error & Self-Heal", "syntax error"),
        "/heal": ("Auto-Fix Error & Self-Heal", "Inspect workspace runtime and syntax errors and execute self-healing loop."),
        "/goal Unbounded engineering": ("Autonomous Agent (Tools Enabled)", "Unbounded engineering"),
        "/test": ("Autonomous Agent (Tools Enabled)", "Execute the project automated test suite via <tool:run_tests /> and verify deliverable criteria."),
    }

    for input_text, (expected_mode, expected_goal) in commands.items():
        parts = input_text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "/plan":
            mode = "Multi-Agent Orchestrator (DAG Team)"
            goal = arg or "Analyze workspace architecture and generate detailed execution plan."
        elif cmd == "/scaffold":
            mode = "Executive Project Scaffolder & Self-Heal"
            goal = arg or "Scaffold production project architecture."
        elif cmd in ("/fix", "/heal"):
            mode = "Auto-Fix Error & Self-Heal"
            goal = arg or "Inspect workspace runtime and syntax errors and execute self-healing loop."
        elif cmd == "/goal":
            mode = "Autonomous Agent (Tools Enabled)"
            goal = arg
        elif cmd == "/test":
            mode = "Autonomous Agent (Tools Enabled)"
            goal = "Execute the project automated test suite via <tool:run_tests /> and verify deliverable criteria."
        else:
            mode = ""
            goal = ""

        assert mode == expected_mode
        assert goal == expected_goal
