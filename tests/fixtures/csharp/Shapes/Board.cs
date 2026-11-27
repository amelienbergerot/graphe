namespace Shapes
{
    public static class Board
    {
        public static double Total(IShape s)
        {
            var c = new Circle();
            Log(c.ToString());
            return s.Area() + c.R;
        }

        static void Log(string m)
        {
        }
    }

    public class Program
    {
        public static void Main()
        {
            Board.Total(new Square());
        }
    }
}
