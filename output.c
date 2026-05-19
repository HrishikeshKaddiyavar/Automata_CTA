#include <stdio.h>

int main() {
    int f, i, n;
    printf("Enter n: ");
    scanf("%d", &n);
    f = 1;
    i = 1;
    while (i <= n) {
        f = f * i;
        i = i + 1;
    }
    printf("Factorial of %d is %d\n", n, f);
    return 0;
}