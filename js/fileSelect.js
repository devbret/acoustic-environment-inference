export function populateFileSelect(select, results) {
  select.innerHTML = "";
  results.forEach((r, i) => {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = r.basename || r.file || `Item ${i + 1}`;
    select.appendChild(opt);
  });
}
