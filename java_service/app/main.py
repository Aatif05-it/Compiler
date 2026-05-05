from __future__ import annotations

import pathlib
import subprocess
import tempfile
import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Java Compiler Service")


class JavaRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50_000)
    stdin: str = Field(default="", max_length=10_000)


class JavaResponse(BaseModel):
    compile_stdout: str = ""
    compile_stderr: str = ""
    run_stdout: str = ""
    run_stderr: str = ""
    timed_out: bool = False
    success: bool = False


def _run(cmd: list[str], cwd: str, timeout: int = 5) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, input=None, capture_output=True, timeout=timeout, check=False)


def _java_compile_command() -> list[str]:
    # Conservative flags for low-memory environments
    return [
        "javac",
        "-J-Xms8m",
        "-J-Xmx64m",
        "-J-XX:ReservedCodeCacheSize=16m",
        "-J-XX:+UseSerialGC",
        "Main.java",
    ]


def _java_run_command() -> list[str]:
    return [
        "java",
        "-Xms8m",
        "-Xmx64m",
        "-XX:ReservedCodeCacheSize=16m",
        "-XX:+UseSerialGC",
        "Main",
    ]


@app.post("/api/run_java", response_model=JavaResponse)
def run_java(payload: JavaRequest) -> JavaResponse:
    try:
        with tempfile.TemporaryDirectory(prefix="java-sandbox-") as tmp:
            src = pathlib.Path(tmp) / "Main.java"
            src.write_text(payload.code, encoding="utf-8")

            compile_result = _run(_java_compile_command(), cwd=tmp, timeout=10)
            if compile_result.returncode != 0:
                return JavaResponse(compile_stdout=compile_result.stdout, compile_stderr=compile_result.stderr, success=False)

            run_result = _run(_java_run_command(), cwd=tmp, timeout=5)

            return JavaResponse(
                compile_stdout=compile_result.stdout,
                compile_stderr=compile_result.stderr,
                run_stdout=run_result.stdout,
                run_stderr=run_result.stderr,
                success=run_result.returncode == 0,
            )

    except subprocess.TimeoutExpired:
        return JavaResponse(compile_stderr="Execution timed out.", timed_out=True, success=False)
    except FileNotFoundError:
        return JavaResponse(compile_stderr="JDK not installed in this container.", success=False)
    except Exception as exc:  # pragma: no cover - generic guard
        return JavaResponse(compile_stderr=f"Internal error: {exc}", success=False)
