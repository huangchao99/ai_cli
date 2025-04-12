#!/bin/bash
# 示例脚本 - 展示 AI CLI 工具的各种用法

# 确保示例目录存在
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

echo "===== AI CLI 工具使用示例 ====="
echo 

# 检查 ai 工具是否在 PATH 中
if ! command -v ai &>/dev/null; then
    # 尝试使用相对路径
    AI_CMD="../bin/ai"
    if [ ! -x "$AI_CMD" ]; then
        echo "错误: 找不到 ai 命令。请先安装或确保脚本在正确的目录中运行。"
        exit 1
    fi
else
    AI_CMD="ai"
fi

echo "使用命令: $AI_CMD"
echo

# 示例 1: 基本问答
echo "=== 示例 1: 基本问答 ==="
echo "命令: $AI_CMD \"介绍下 Linux 的 open 系统调用\""
echo "提示: 按 Ctrl+C 跳过当前示例"
read -p "按回车键继续..." 
$AI_CMD "介绍下 Linux 的 open 系统调用"
echo 

# 示例 2: 通过管道传入内容
echo "=== 示例 2: 通过管道传入内容 ==="
echo "命令: cat example.c | $AI_CMD \"解释这段代码的问题，并提出改进建议\""
echo "提示: 按 Ctrl+C 跳过当前示例"
read -p "按回车键继续..." 
cat example.c | $AI_CMD "解释这段代码的问题，并提出改进建议"
echo

# 示例 3: 重定向输出
echo "=== 示例 3: 重定向输出 ==="
echo "命令: $AI_CMD \"生成一个更高效的斐波那契数列计算函数\" > improved_fibonacci.c"
echo "提示: 按 Ctrl+C 跳过当前示例"
read -p "按回车键继续..." 
$AI_CMD "使用迭代方法生成一个更高效的斐波那契数列计算C函数" > improved_fibonacci.c
echo "输出已保存至 improved_fibonacci.c"
cat improved_fibonacci.c
echo

# 示例 4: 修改模式
echo "=== 示例 4: 修改模式 ==="
echo "命令: $AI_CMD -m example.c \"优化这个斐波那契数列程序，提高性能并修复问题\""
echo "提示: 按 Ctrl+C 跳过当前示例"
echo "注意: 在交互选项中，您可以选择接受、拒绝、编辑或拆分应用修改。"
read -p "按回车键继续..." 
cp -f example.c example_backup.c  # 备份原文件以便恢复
$AI_CMD -m example.c "优化这个斐波那契数列程序，提高性能并修复问题"
echo
echo "原始文件已备份为 example_backup.c"

# 示例 5: 查询余额
echo
echo "=== 示例 5: 查询账户余额 ==="
echo "命令: $AI_CMD -b"
echo "提示: 按 Ctrl+C 跳过当前示例"
read -p "按回车键继续..." 
$AI_CMD -b
echo

echo "===== 示例运行完毕 ====="
echo "您可以在 README.md 中找到更多使用说明和高级特性。"
