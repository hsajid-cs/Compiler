// Scope testing
// Variables with the same name in different scopes should not conflict

int main() {
    int x = 1;

    if (x == 1) {
        int x = 100;   // new scope — this is a different 'x'
        print(x);       // should refer to the inner x (100)
    }

    print(x);           // should refer to the outer x (1)

    // Nested blocks
    {
        int y = 42;
        {
            int y = 99;  // shadows the outer y
            print(y);    // 99
        }
        print(y);        // 42
    }

    // For loop variable scoping
    int i = 999;
    for (int i = 0; i < 3; i = i + 1) {
        print(i);        // 0, 1, 2
    }
    print(i);            // 999 — for-loop 'i' is in its own scope

    return 0;
}
