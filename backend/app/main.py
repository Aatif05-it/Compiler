from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import tempfile
from typing import Literal

try:
    import resource
except ImportError:  # Windows does not provide the resource module.
    resource = None

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import requests

app = FastAPI(title="Free C/C++/Java Compiler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve frontend files from the repo's top-level `frontend` folder
static_path = pathlib.Path(__file__).resolve().parent.parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=static_path), name="static")


class RunRequest(BaseModel):
    language: Literal["c", "cpp", "java"]
    code: str = Field(min_length=1, max_length=50_000)
    stdin: str = Field(default="", max_length=10_000)
    demo: bool = Field(default=False)


class RunResponse(BaseModel):
    compile_stdout: str = ""
    compile_stderr: str = ""
    run_stdout: str = ""
    run_stderr: str = ""
    timed_out: bool = False
    success: bool = False


def _apply_limits() -> None:
    # Apply strict limits so user code cannot consume excessive resources.
    if resource is None:
        return

    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))


def _run_command(command: list[str], cwd: str, stdin: str = "", timeout: int = 5) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        input=stdin,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        preexec_fn=_apply_limits if os.name != "nt" else None,
    )


def _binary_name(base_name: str) -> str:
    return f".\\{base_name}.exe" if os.name == "nt" else f"./{base_name}"


def _java_compile_command() -> list[str]:
    return [
        "javac",
        "-J-Xms8m",
        "-J-Xmx32m",
        "-J-XX:ReservedCodeCacheSize=8m",
        "-J-XX:+UseSerialGC",
        "Main.java",
    ]


def _java_run_command(class_name: str) -> list[str]:
    return [
        "java",
        "-Xms8m",
        "-Xmx32m",
        "-XX:ReservedCodeCacheSize=8m",
        "-XX:+UseSerialGC",
        class_name,
    ]


@app.get("/")
def home() -> FileResponse:
    return FileResponse(static_path / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/run", response_model=RunResponse)
def run_code(payload: RunRequest) -> RunResponse:
    # Demo mode: return sample output without requiring compilers
    if payload.demo:
        lang_name = "C" if payload.language == "c" else "C++" if payload.language == "cpp" else "Java"
        return RunResponse(
            compile_stdout="",
            compile_stderr="",
            run_stdout=f"Hello from {lang_name}!\n",
            run_stderr="",
            success=True,
        )

    if payload.language == "java":
        java_url = os.getenv("JAVA_SERVICE_URL", "http://localhost:9000/api/run_java")
        try:
            resp = requests.post(java_url, json={"code": payload.code, "stdin": payload.stdin}, timeout=15)
            if resp.status_code != 200:
                return RunResponse(compile_stderr=f"Java service error: HTTP {resp.status_code}", success=False)
            data = resp.json()
            return RunResponse(
                compile_stdout=data.get("compile_stdout", ""),
                compile_stderr=data.get("compile_stderr", ""),
                run_stdout=data.get("run_stdout", ""),
                run_stderr=data.get("run_stderr", ""),
                timed_out=data.get("timed_out", False),
                success=data.get("success", False),
            )
        except requests.RequestException as exc:
            return RunResponse(compile_stderr=f"Failed to contact Java service: {exc}", success=False)

    if shutil.which("gcc") is None or shutil.which("g++") is None:
        return RunResponse(
            compile_stderr="Compiler toolchain not found. Deploy to Render with Docker for real compilation.",
            success=False,
        )

    try:
        with tempfile.TemporaryDirectory(prefix="sandbox-") as tmp:
            if payload.language == "c":
                source = pathlib.Path(tmp) / "main.c"
                source.write_text(payload.code, encoding="utf-8")
                output_name = "main.exe" if os.name == "nt" else "main"
                compile_result = _run_command(["gcc", "main.c", "-O2", "-std=c11", "-o", output_name], cwd=tmp, timeout=10)
                if compile_result.returncode != 0:
                    return RunResponse(
                        compile_stdout=compile_result.stdout,
                        compile_stderr=compile_result.stderr,
                        success=False,
                    )
                run_result = _run_command([_binary_name("main")], cwd=tmp, stdin=payload.stdin, timeout=5)

            elif payload.language == "cpp":
                source = pathlib.Path(tmp) / "main.cpp"
                source.write_text(payload.code, encoding="utf-8")
                output_name = "main.exe" if os.name == "nt" else "main"
                compile_result = _run_command(["g++", "main.cpp", "-O2", "-std=c++17", "-o", output_name], cwd=tmp, timeout=10)
                if compile_result.returncode != 0:
                    return RunResponse(
                        compile_stdout=compile_result.stdout,
                        compile_stderr=compile_result.stderr,
                        success=False,
                    )
                run_result = _run_command([_binary_name("main")], cwd=tmp, stdin=payload.stdin, timeout=5)

            else:
                source = pathlib.Path(tmp) / "Main.java"
                source.write_text(payload.code, encoding="utf-8")
                compile_result = _run_command(_java_compile_command(), cwd=tmp, timeout=10)
                if compile_result.returncode != 0:
                    return RunResponse(
                        compile_stdout=compile_result.stdout,
                        compile_stderr=compile_result.stderr,
                        success=False,
                    )
                run_result = _run_command(_java_run_command("Main"), cwd=tmp, stdin=payload.stdin, timeout=5)

            return RunResponse(
                compile_stdout=compile_result.stdout,
                compile_stderr=compile_result.stderr,
                run_stdout=run_result.stdout,
                run_stderr=run_result.stderr,
                success=run_result.returncode == 0,
            )

    except subprocess.TimeoutExpired:
        return RunResponse(
            compile_stderr="Execution timed out.",
            timed_out=True,
            success=False,
        )
    except FileNotFoundError:
        return RunResponse(
            compile_stderr="Compiler toolchain not found on this machine. Install gcc/g++/JDK or run with Docker.",
            success=False,
        )
    except Exception as exc:
        return RunResponse(
            compile_stderr=f"Internal server error: {exc}",
            success=False,
        )
