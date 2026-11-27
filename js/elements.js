export function queryElements() {
  return {
    fileSelect: document.getElementById("fileSelect"),
    metaPanel: document.getElementById("metaPanel"),
    btnFetch: document.getElementById("btnFetch"),
    fileInput: document.getElementById("fileInput"),
    dropzone: document.getElementById("dropzone"),
    fitNetwork: document.getElementById("fitNetwork"),

    pipelineVersion: document.getElementById("pipelineVersion"),
    totalFiles: document.getElementById("totalFiles"),
    totalMatches: document.getElementById("totalMatches"),
    threshold: document.getElementById("threshold"),

    ovName: document.getElementById("ovName"),
    ovDur: document.getElementById("ovDur"),
    ovScene: document.getElementById("ovScene"),
    ovHum: document.getElementById("ovHum"),
    ovTags: document.getElementById("ovTags"),
    ovHash: document.getElementById("ovHash"),
    ovSize: document.getElementById("ovSize"),
    ovMtime: document.getElementById("ovMtime"),
  };
}
