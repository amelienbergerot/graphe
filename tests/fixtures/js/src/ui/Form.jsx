import { label } from './Panel'
import { compute } from '../compute.mjs'

export function save(x) {
  return compute(x)
}

export function Form({ x }) {
  return <form onSubmit={save}><button onClick={() => save(x)}>{label(1)}</button></form>
}
