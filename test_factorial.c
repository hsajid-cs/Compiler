// Factorial — iterative version using a for loop

int factorial(int n) {
    int result = 1;
    int i;
    for (i = 1; i <= n; i = i + 1) {
        result = result * i;
    }
    return result;
}

int main() {
    int n = 7;
    int f = factorial(n);
    print(f);
    return 0;
}
