const starterCode = {
  c: `#include <stdio.h>\n\nint main() {\n    printf("Hello from C!\\n");\n    return 0;\n}`,
  cpp: `#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "Hello from C++!" << endl;\n    return 0;\n}`,
  java: `public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello from Java!");\n    }\n}`,
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

async function executeCode(useDemo = false) {
  runBtn.disabled = true;
  demoBtn.disabled = true;
  statusEl.textContent = useDemo ? "Demo..." : "Running...";
  outputEl.textContent = "Compiling...";

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

    const parts = [];

    if (data.compile_stdout) {
      parts.push("[compile stdout]\n" + data.compile_stdout.trim());
    }
    if (data.compile_stderr) {
      parts.push("[compile stderr]\n" + data.compile_stderr.trim());
    }
    if (data.run_stdout) {
      parts.push("[program stdout]\n" + data.run_stdout.trim());
    }
    if (data.run_stderr) {
      parts.push("[program stderr]\n" + data.run_stderr.trim());
    }
    if (parts.length === 0) {
      parts.push("No output.");
    }

    outputEl.textContent = parts.join("\n\n");
    statusEl.textContent = data.success ? "Success" : data.timed_out ? "Timed out" : "Finished with errors";
  } catch (error) {
    outputEl.textContent = "Request failed: " + error;
    statusEl.textContent = "Request failed";
  } finally {
    runBtn.disabled = false;
    demoBtn.disabled = false;
  }
}

languageEl.addEventListener("change", () => {
  codeEl.value = starterCode[languageEl.value];
  outputEl.textContent = "Language switched.";
});

runBtn.addEventListener("click", () => executeCode(false));
demoBtn.addEventListener("click", () => executeCode(true));

setStarterCode(languageEl.value);
