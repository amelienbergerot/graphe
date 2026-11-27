package shapes;

public class Circle extends Shape {
    private final double r;

    public Circle(double r) {
        this.r = r;
    }

    public static Circle unit() {
        return new Circle(1);
    }

    public static Circle create(double r) {
        return new Circle(r);
    }

    @Override
    public double area() {
        return 3.0 * r * r;
    }
}
