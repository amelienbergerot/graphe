export function reserve(rain: number): number {
  return rain
}

export class Gauge {
  level(rain: number): number {
    return reserve(rain)
  }
}

export function measure(g) {
  return g.level(1)
}
