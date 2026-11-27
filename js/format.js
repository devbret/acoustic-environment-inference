export function fmtHz(v) {
  return v == null ? "—" : `${(+v).toFixed(1)} Hz`;
}

export function fmtNum(v) {
  return v == null ? "—" : (+v).toFixed(2);
}

export function fmtBytes(b) {
  if (b == null) return "—";
  const u = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  let n = +b;
  while (n >= 1024 && i < u.length - 1) {
    n /= 1024;
    i++;
  }
  return `${n.toFixed(1)} ${u[i]}`;
}
