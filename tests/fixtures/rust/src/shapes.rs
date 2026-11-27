pub struct Point {
    pub x: i32,
}

pub struct Line {
    a: Point,
}

impl Point {
    pub fn new(x: i32) -> Point {
        Point { x }
    }

    pub fn origin() -> Point {
        Point::new(0)
    }

    pub fn len(&self) -> i32 {
        1
    }
}

impl Line {
    pub fn new(a: Point) -> Line {
        Line { a }
    }

    pub fn length(&self) -> i32 {
        self.a.length()
    }
}

pub fn shift(p: &Point) -> i32 {
    p.len() + 1
}
