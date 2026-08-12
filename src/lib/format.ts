function pad(n: number) {
  return n.toString().padStart(2, '0')
}

export function formatDuration(ms: number) {
  const total = Math.floor(ms / 1000)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${pad(m)}:${pad(s)}`
}
