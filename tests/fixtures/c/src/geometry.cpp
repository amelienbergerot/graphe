#include "util.h"

struct Shape {
    virtual double area() = 0;
};

class Circle : public Shape {
public:
    double area() { return 3.0 * r * r; }
    int size() { return 1; }
    double r;
};

class Square : public Shape {
public:
    double area() { return s * s; }
    double s;
};

namespace geo {
double scale(double k) { return k; }
}

double total(Circle& c, Square* q) {
    int n = clamp(-1);
    double a = c.area() + q->area();
    int m = c.size();
    Circle* d = new Circle();
    return a + n + m + geo::scale(2.0);
}
