import { zoneFromCode as zone } from './zones.mjs'
import Builder from './builder.mjs'

export function compute(dpe) {
  const b = new Builder()
  b.build(zone(dpe.code))
  return total(b)
}

const total = (b) => b.sum
