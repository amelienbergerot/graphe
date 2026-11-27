func render(_ shape: Drawable) -> String {
    return shape.draw()
}

func paint() -> String {
    let c = Circle(r: 1)
    let n = c.count()
    let a = c.area()
    return render(c) + String(n) + String(a)
}
