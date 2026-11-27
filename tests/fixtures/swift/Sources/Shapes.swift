protocol Drawable {
    func draw() -> String
}

struct Circle: Drawable {
    var r: Double

    func draw() -> String {
        return "circle"
    }

    func area() -> Double {
        return 3.0 * r * r
    }

    func count() -> Int {
        return 1
    }
}

struct Square: Drawable {
    var side: Double

    func draw() -> String {
        return "square"
    }

    var area: Double {
        return side * side
    }
}
