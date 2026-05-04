const starterCode = {
  c: `#include <stdio.h>

int main() {
    printf("Hello from C!\\n");
    return 0;
}`,
  cpp: `#include <iostream>
using namespace std;

int main() {
    cout << "Hello from C++!" << endl;
    return 0;
}`,
  java: `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Java!");
    }
}`,
};

const languageEl = document.getElementById("language");
const codeEl = document.getElementById("code");
const stdinEl = document.getElementById("stdin");
const runBtn = document.getElementById("runBtn");
const demoBtn = document.getElementById("demoBtn");
const outputEl = document.getElementById("output");
const statusEl = document.getElementById("status");

function setStarterCode(language) {
  if (!codeEl.value.trim()) {
    codeEl.value = starterCode[language];
  }
}

function updateStatus(text, type = "default") {
  statusEl.textContent = text;
  statusEl.className = "status-badge " + type;
}

async function executeCode(useDemo = false) {
  runBtn.disabled = true;
  demoBtn.disabled = true;
  updateStatus("Running...", "running");
  outputEl.textContent = "Compiling and executing...";

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        language: languageEl.value,
        code: codeEl.value,
        stdin: stdinEl.value,
        demo: useDemo,
      }),
    });

    const data = await response.json();

    // Build output display
    const parts = [];

    if (data.compile_stdout) {
      parts.push("[Compile Output]\n" + data.compile_stdout.trim());
    }
    if (data.compile_stderr) {
      parts.push("[Compile Errors]\n" + data.compile_stderr.trim());
    }
    if (data.run_stdout) {
      parts.push("[Program Output]\n" + data.run_stdout.trim());
    }
    if (data.run_stderr) {
      parts.push("[Program Errors]\n" + data.run_stderr.trim());
    }
    if (parts.length === 0) {
      parts.push("(No output)");
    }

    outputEl.textContent = parts.join("\n\n");

    if (data.success) {
      updateStatus("Success ✓", "success");
    } else if (data.timed_out) {
      updateStatus("Timeout ⏱", "error");
    } else {
      updateStatus("Error ✗", "error");
    }
  } catch (error) {
    outputEl.textContent = "Request Failed: " + error.message;
    updateStatus("Failed ✗", "error");
  } finally {
    runBtn.disabled = false;
    demoBtn.disabled = false;
  }
}

// Event Listeners
languageEl.addEventListener("change", () => {
  codeEl.value = starterCode[languageEl.value];
  outputEl.textContent = "Language switched. Click Run or Demo.";
  updateStatus("Ready", "default");
});

runBtn.addEventListener("click", () => executeCode(false));
demoBtn.addEventListener("click", () => executeCode(true));

// Keyboard shortcut: Ctrl+Enter or Cmd+Enter to run
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    executeCode(false);
  }
});

// Initialize
setStarterCode(languageEl.value);
updateStatus("Ready", "default");
