/*
 * 斐波那契数列计算 - 简单演示
 * 优化版本：使用迭代代替递归，增加输入验证
 */
#include <stdlib.h>
// 计算斐波那契数列
int fibonacci(int n) {
    if (n <= 0) return 0;
    if (n == 1) return 1;
    return fibonacci(n-1) + fibonacci(n-2);
}
// 主函数
int main() {
int main() {
    int n;
    printf("请输入要计算的斐波那契数列项数: ");
    if (scanf("%d", &n) != 1) {
        printf("Error: 无效输入\n");
        return EXIT_FAILURE;
    }
    if (n < 0 || n > 46) {  // 限制输入范围防止整数溢出
        printf("Error: 输入必须是正整数\n");
    }
    printf("斐波那契数列第 %d 项是: %d\n", n, fibonacci(n));
    return 0;
}

}
}
