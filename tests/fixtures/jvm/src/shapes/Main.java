package shapes;

public class Main {
    public static void main(String[] args) {
        Shape s = Circle.unit();
        Shape c = Circle.create(2);
        Shape q = Square.of(3);
        double a = s.area() + c.area();
        String n = q.getName() + s.describe();
    }
}
