"""
Local Ollama & AI Diagnostics Benchmark Tool.
Tests Ollama API reachability, enumerates available models, benchmarks
streaming token generation throughput (tokens/sec), and inspects CUDA GPU acceleration.
"""
import sys
import time
import requests

OLLAMA_BASE = "http://localhost:11434"

def inspect_hardware():
    print("=" * 60)
    print("1. HARDWARE & ACCELERATION DIAGNOSTICS")
    print("=" * 60)
    try:
        import torch
        cuda_ok = torch.cuda.is_available()
        print(f"CUDA Available:   {cuda_ok}")
        if cuda_ok:
            print(f"Device Name:      {torch.cuda.get_device_name(0)}")
            print(f"CUDA Version:     {torch.version.cuda}")
            print(f"Device Count:     {torch.cuda.device_count()}")
        else:
            print("Note: Running on CPU (no CUDA acceleration detected)")
    except ImportError:
        print("PyTorch not installed; skipping CUDA device query.")
    print()


def inspect_ollama():
    print("=" * 60)
    print("2. OLLAMA SERVICE & MODEL INVENTORY")
    print("=" * 60)
    try:
        ver_resp = requests.get(f"{OLLAMA_BASE}/api/version", timeout=4)
        ver_resp.raise_for_status()
        version = ver_resp.json().get("version", "unknown")
        print(f"Ollama Service:   ONLINE (v{version})")
    except Exception as ex:
        print(f"ERROR: Cannot connect to Ollama at {OLLAMA_BASE}")
        print(f"Detail: {ex}")
        print("Please ensure Ollama application is running.")
        sys.exit(1)

    try:
        tags_resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        tags_resp.raise_for_status()
        models = tags_resp.json().get("models", [])
        print(f"Installed Models: {len(models)}")
        for m in models:
            name = m.get("name")
            size_mb = m.get("size", 0) / (1024 * 1024)
            details = m.get("details", {})
            param_size = details.get("parameter_size", "unknown")
            quant = details.get("quantization_level", "unknown")
            print(f"  • {name:<20} Size: {size_mb:>7.1f} MB | Params: {param_size} | Quant: {quant}")
        return [m.get("name") for m in models]
    except Exception as ex:
        print(f"Failed to query model tags: {ex}")
        return []


def benchmark_model(model_name):
    print("\n" + "=" * 60)
    print(f"3. STREAMING BENCHMARK: {model_name}")
    print("=" * 60)

    prompt = "Explain in three clear bullet points what a Python virtual environment does and why developers use it."
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": 0.2, "num_predict": 128}
    }

    print(f"Prompt: {prompt}")
    print("Streaming tokens:\n")

    start_time = time.time()
    first_token_time = None
    token_count = 0
    full_response = ""

    try:
        with requests.post(f"{OLLAMA_BASE}/api/generate", json=payload, stream=True, timeout=(5, 120)) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                chunk = requests.compat.json.loads(line.decode("utf-8"))
                text = chunk.get("response", "")
                if text:
                    if first_token_time is None:
                        first_token_time = time.time()
                    token_count += 1
                    full_response += text
                    print(text, end="", flush=True)
                if chunk.get("done"):
                    break
        print("\n")
    except Exception as ex:
        print(f"\nGeneration error: {ex}")
        return

    total_time = time.time() - start_time
    ttft = (first_token_time - start_time) if first_token_time else 0
    generation_time = total_time - ttft
    tok_per_sec = (token_count / generation_time) if generation_time > 0 else 0

    print("-" * 60)
    print("BENCHMARK METRICS:")
    print(f"  Total Tokens:           {token_count}")
    print(f"  Time to First Token:    {ttft:.3f} s")
    print(f"  Total Generation Time:  {total_time:.3f} s")
    print(f"  Generation Throughput:  {tok_per_sec:.2f} tokens/sec")
    print("-" * 60)


if __name__ == "__main__":
    inspect_hardware()
    models = inspect_ollama()
    target_model = "qwen2.5:1.5b" if "qwen2.5:1.5b" in models else (models[0] if models else "qwen2.5:1.5b")
    benchmark_model(target_model)
