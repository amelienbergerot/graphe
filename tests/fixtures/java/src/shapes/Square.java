package shapes;

public class Square extends Shape {
    private final double side;

    public Square(double side) {
        this.side = side;
    }

    public static Square create(double side) {
        return new Square(side);
    }

    public static Square of(double side) {
        return new Square(side);
    }

    @Override
    public double area() {
        return side * side;
    }

    @Override
    public double perimeter() {
        return 4 * side;
    }
}
