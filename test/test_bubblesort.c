// Bubble Sort
// Sorts an array of 5 integers using bubble sort

int main() {
    int arr[5];

    // Initialize array with unsorted values
    arr[0] = 64;
    arr[1] = 34;
    arr[2] = 25;
    arr[3] = 12;
    arr[4] = 22;

    int n = 5;
    int i = 0;

    // Bubble sort: nested loops
    while (i < n - 1) {
        int j = 0;
        while (j < n - i - 1) {
            if (arr[j] > arr[j + 1]) {
                // Swap arr[j] and arr[j+1]
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
            j = j + 1;
        }
        i = i + 1;
    }

    // Print sorted array
    int k = 0;
    while (k < n) {
        print(arr[k]);
        k = k + 1;
    }

    return 0;
}
