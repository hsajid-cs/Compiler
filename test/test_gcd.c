// GCD using Euclidean Algorithm
// Uses a do-while loop (the unconventional choice!)

int gcd(int a, int b) {
    // Euclidean algorithm with do-while
    do {
        int temp = b;
        b = a % temp;
        a = temp;
    } while (b != 0);

    return a;
}

int main() {
    int x = 48;
    int y = 18;
    int result = gcd(x, y);
    print(result);
    return 0;
}
