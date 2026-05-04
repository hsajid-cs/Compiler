// Intentional errors — each should produce a friendly error message

int main() {
    // Error 1: undeclared variable
    x = 10;

    // Error 2: type mismatch (assigning float to int)
    int a = 3.14;

    // Error 3: calling function with wrong number of args
    int b = gcd(1, 2, 3);

    // Error 4: redeclaring a variable in the same scope
    int c = 5;
    int c = 10;

    return 0;
}
