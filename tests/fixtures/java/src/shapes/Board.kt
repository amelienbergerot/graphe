package shapes

class Board {
    companion object {
        fun create(): Board {
            return Board()
        }
    }

    fun place(s: Shape): Double {
        return s.area()
    }
}

fun fill(): Double {
    val b = Board.create()
    return b.place(Circle.unit())
}
