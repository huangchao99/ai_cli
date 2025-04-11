# AI 命令行工具

一个基于 DeepSeek API 的极简 AI 命令行工具，支持 macOS 和 Linux。

## 设计原则

本工具遵循以下设计原则：

1. **Unix 哲学**：专注文本流处理，完全支持管道和重定向
2. **最小惊异原则**：交互模式符合开发者直觉，操作简单明了

## 功能特点

- 使用 DeepSeek API（默认使用 deepseek-chat 模型）
- 支持 macOS 和 Linux
- 支持基本模式（直接提问、管道输入、重定向输出）
- 支持修改模式（类似 git conflict 格式展示变更）
- 流式输出（实时显示 AI 回复）
- Vim 集成支持

## 安装

### 前提条件

- Python 3.6 或以上版本
- DeepSeek API 密钥（从 [DeepSeek 开发者平台](https://platform.deepseek.com/) 获取）

### 安装步骤

1. 克隆或下载本项目
2. 确保依赖项已安装：

```bash
pip install requests
```

3. 设置环境变量或配置文件以存储 API 密钥：

```bash
# Linux/macOS
export DEEPSEEK_API_KEY="your-api-key-here"

# Windows
set DEEPSEEK_API_KEY=your-api-key-here
```

或者通过交互式命令进行配置：

```bash
./bin/ai --configure
```

4. 将 `bin` 目录添加到您的 PATH 中，或者创建符号链接：

```bash
# 创建符号链接到 /usr/local/bin（需要管理员权限）
sudo ln -s "$(pwd)/bin/ai" /usr/local/bin/ai

# 或者将目录添加到 PATH（添加到您的 .bashrc 或 .zshrc 文件中）
export PATH="$PATH:/path/to/ai-cli/bin"
```

## 基本用法

### 直接提问

```bash
ai "介绍下 Linux 的 open 系统调用"
```

### 使用管道传递输入

```bash
cat example.c | ai "请解释这份代码"
```

### 重定向输出到文件

```bash
ai "生成计算斐波那契数列的 C 代码" > fibo.c
```

### 组合管道和重定向

```bash
cat readme.txt | ai "翻译成英文" > translation.txt
```

## 修改模式

修改模式用于修改现有文件，并以类似 git conflict 的方式显示变更。

### 基本用法

```bash
ai -m readme.md "翻译成中文"
ai --modify main.c "修改其中的 bug"
```

### 带有提示的修改

```bash
ai -m src/utils.py -p "优化异常处理"
```

### 交互选项

修改模式会以差异对比的方式显示建议的修改，并提供以下交互选项：

1. **接受修改**：应用所有建议的修改
2. **拒绝**：放弃所有修改
3. **编辑**：使用默认编辑器（通过 EDITOR 环境变量设置）编辑建议的修改
4. **拆分应用**：逐个检查并选择应用哪些修改块

### 示例输出

```
--- src/utils.py (原始版本)
+++ src/utils.py (AI建议)
@@ -12,6 +12,7 @@
 def process_data(data):
     try:
         validate(data)
+    except ValidationError as e:
+        logger.error(f"数据校验失败: {e}")
     except Exception as e:
-        print("Error:", e)
+        raise ProcessingError("数据处理异常") from e
     finally:
         cleanup()

交互选项:
[1] 接受修改   [2] 拒绝   [3] 编辑   [4] 拆分应用
[?] 请选择操作 (默认1): 
```

## Vim 集成

可以在 Vim 中使用命令行工具修改选中的代码块：

```vim
:'<,'>!ai -m "优化这段代码"
```

将此命令添加到 `.vimrc` 文件中可以创建一个方便的快捷键：

```vim
" 定义ai命令，传递选中的文本
vnoremap <leader>ai :!ai<space>
" 定义修改模式命令，修改选中的文本
vnoremap <leader>aim :!ai -m<space>
```

## 高级配置

### 配置文件位置

配置文件存储在：
- Linux/macOS: `~/.config/ai-cli/config.json`
- Windows: `%APPDATA%\ai-cli\config.json`

### 可配置选项

- `api_key`: DeepSeek API密钥
- `model`: 使用的模型名称
- `history_size`: 历史记录大小

### 环境变量

- `DEEPSEEK_API_KEY`: 可以通过环境变量设置 API 密钥
- `EDITOR`: 用于修改模式编辑功能的默认编辑器

## 故障排除

### API 密钥问题

如果收到 API 密钥错误，请确保：
1. 已正确设置 API 密钥（通过环境变量或配置文件）
2. API 密钥有效且未过期

### 网络问题

如果遇到网络连接问题：
1. 检查网络连接是否正常
2. 确认防火墙未阻止连接
3. 如果使用代理，请确保代理设置正确

### 文件编码问题

如果遇到文件编码问题：
1. 确保输入文件使用 UTF-8 编码
2. 对于非 UTF-8 编码文件，可能需要先转换编码

## 开发与贡献

### 项目结构

```
ai-cli/
  ├── bin/
  │   └── ai            # 主可执行文件
  └── src/
      ├── api.py        # DeepSeek API 客户端
      ├── config.py     # 配置管理
      ├── modify.py     # 修改模式实现
      └── utils.py      # 工具函数
```

### 扩展模型支持

要添加对新模型的支持，请修改 `api.py` 文件中的默认模型列表。

## 许可证

[设定适当的许可证]

## 致谢

- DeepSeek 提供的强大 API 服务
- 所有贡献者和测试者
