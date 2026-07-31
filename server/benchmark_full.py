"""
Full performance benchmark for CodeForge server.
Tests: startup, project indexing, context building, chat latency, memory.
"""

import time
import sys
import os
sys.path.insert(0, ".")

from app.services.model_manager import ModelManager
from app.services.inference import chat
from app.services.project_scanner import scan_project
from app.services.bm25_search import get_search_engine, invalidate_cache
from app.services.context_builder import build_context
from app.core.config import settings

RESULTS = {}


def benchmark(name: str):
    """Decorator to time a function and store results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            RESULTS[name] = round(elapsed, 3)
            print(f"  {name}: {elapsed:.3f}s")
            return result
        return wrapper
    return decorator


@benchmark("Model loading")
def bench_model_load():
    manager = ModelManager()
    models = manager.list_available_models()
    if not models:
        print("  (no models found - skipping)")
        return None
    manager.load_model(models[0].name)
    return manager


@benchmark("Project scanning (100 files)")
def bench_scan():
    files = scan_project(settings.BASE_DIR, load_content=False)
    print(f"  Files found: {len(files)}")
    return files


@benchmark("BM25 index building")
def bench_index():
    invalidate_cache()
    engine = get_search_engine(str(settings.BASE_DIR), force_rebuild=True)
    print(f"  Documents: {engine.doc_count}, Terms: {len(engine.inverted_index)}")
    return engine


@benchmark("BM25 search")
def bench_search(engine):
    engine.search("model manager load unload")
    engine.search("chat endpoint streaming")
    engine.search("inline completion ghost text")


@benchmark("Context building")
def bench_context():
    build_context("how does the model manager work", str(settings.BASE_DIR))


@benchmark("Chat inference (50 tokens)")
def bench_chat(manager):
    if not manager or not manager.is_loaded():
        print("  (no model loaded - skipping)")
        return
    chat("Write a Python function to add two numbers.", max_tokens=50)


@benchmark("Health check")
def bench_health():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    client.get("/health")
    client.get("/health/diagnostics")


@benchmark("Second search (cached)")
def bench_cached_search():
    engine = get_search_engine(str(settings.BASE_DIR))
    engine.search("model manager load unload")


def main():
    print("=" * 50)
    print("  CodeForge Performance Benchmark")
    print("=" * 50)
    print()

    # Run benchmarks
    manager = bench_model_load()
    bench_scan()
    engine = bench_index()
    bench_search(engine)
    bench_context()
    bench_chat(manager)
    bench_health()
    bench_cached_search()

    # Cleanup
    if manager:
        manager.unload_model()

    # Report
    print()
    print("=" * 50)
    print("  Summary")
    print("=" * 50)
    for name, elapsed in RESULTS.items():
        bar = "█" * min(int(elapsed * 10), 50)
        print(f"  {name:<35} {elapsed:>8.3f}s  {bar}")
    
    total = sum(RESULTS.values())
    print(f"  {'TOTAL':<35} {total:>8.3f}s")
    print()

    # Memory estimate
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 * 1024)
        print(f"  Memory usage: {mem_mb:.0f} MB")
    except ImportError:
        print("  Memory: install psutil for memory reporting")

    print()


if __name__ == "__main__":
    main()