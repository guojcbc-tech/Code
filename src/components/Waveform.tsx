type Props = {
  levels: number[]
  active: boolean
}

export function Waveform({ levels, active }: Props) {
  return (
    <div className={`wave ${active ? 'wave--active' : ''}`} aria-hidden="true">
      {levels.map((level, i) => (
        <span
          key={i}
          className="wave__bar"
          style={{
            transform: `scaleY(${active ? Math.max(0.12, level) : 0.12})`,
            animationDelay: `${i * 40}ms`,
          }}
        />
      ))}
    </div>
  )
}
