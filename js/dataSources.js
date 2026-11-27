const DROPZONE_ACTIVE = "#8ab4ff";
const DROPZONE_IDLE = "#3b4291";

async function loadJsonFile(file, onData) {
  if (!file) return;
  const text = await file.text();
  try {
    onData(JSON.parse(text));
  } catch {
    alert("Invalid JSON file.");
  }
}

export function bindFetchButton(button, onData) {
  button.addEventListener("click", async () => {
    try {
      const res = await fetch("output/summary.json");
      if (!res.ok) throw new Error("Fetch failed");
      const json = await res.json();
      onData(json);
    } catch {
      alert(
        "Could not fetch output/summary.json. Use file picker or drag & drop instead.",
      );
    }
  });
}

export function bindFileInput(input, onData) {
  input.addEventListener("change", (e) =>
    loadJsonFile(e.target.files?.[0], onData),
  );
}

export function bindDropzone(dz, onData) {
  dz.addEventListener("dragover", (e) => {
    e.preventDefault();
    dz.style.borderColor = DROPZONE_ACTIVE;
  });
  dz.addEventListener("dragleave", () => {
    dz.style.borderColor = DROPZONE_IDLE;
  });
  dz.addEventListener("drop", (e) => {
    e.preventDefault();
    dz.style.borderColor = DROPZONE_IDLE;
    loadJsonFile(e.dataTransfer.files?.[0], onData);
  });
}
