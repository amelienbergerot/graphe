export default class Builder {
  build(z) {
    return this.add(z)
  }

  add(z) {
    this.sum = z
    return this
  }
}
