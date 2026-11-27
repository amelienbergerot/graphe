import { reserve } from '../lib/water'

export function label(n: number): string {
  return `${reserve(n)} mm`
}

export function Panel({ rain }: { rain: number }) {
  return <p>{label(rain)}</p>
}
