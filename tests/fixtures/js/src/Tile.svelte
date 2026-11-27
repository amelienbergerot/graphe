<script lang="ts">
  import { reserve, Gauge } from './lib/water'

  const gauge = new Gauge()

  function refresh(p: number) {
    return reserve(p) + gauge.level(p)
  }
</script>

<button onclick={refresh}>{reserve(2)}</button>
