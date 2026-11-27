mod shapes;

use shapes::{Line, Point};

fn main() {
    let o = Point::origin();
    let l = Line::new(Point::new(1));
    let n = l.length() + Point::length(&o);
    let v: Vec<i32> = Vec::new();
    shapes::shift(&o);
}
