package shapes;

public abstract class Shape {
    public abstract double area();

    public abstract double perimeter();

    public String getName() {
        return "shape";
    }

    public String describe() {
        return getName() + " " + area();
    }
}
