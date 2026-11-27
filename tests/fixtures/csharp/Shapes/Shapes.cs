namespace Shapes
{
    public interface IShape
    {
        double Area();
    }

    public class Circle : IShape
    {
        public double R { get; set; }

        public double Area()
        {
            return 3.0 * R * R;
        }

        public override string ToString()
        {
            return "circle";
        }
    }

    public class Square : IShape
    {
        public double Side;

        public double Area()
        {
            return Side * Side;
        }
    }
}
