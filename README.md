# Clash 订阅转换器

这是一个用于处理、合并和过滤多个代理服务订阅链接的工具，最终生成一个可用的 Clash 配置文件。

## 功能特点

- 自动合并多个订阅链接
- 自动过滤广告和无用节点信息
- 集成 subconverter，无需单独启动服务
- 支持自定义过滤规则
- 跨平台支持（Windows/Linux/macOS）

## 安装

1. 克隆仓库：
   ```
   git clone https://github.com/你的用户名/clash_sub_converter.git
   cd clash_sub_converter
   ```

2. 安装依赖：
   ```
   pip install requests pyyaml
   ```

## 使用方法

1. 创建一个名为 `links.txt` 的文件，每行一个订阅链接：
   ```
   https://example.com/link1
   https://example.com/link2
   ```

2. 运行脚本：
   ```
   python clash_sub_converter.py
   ```

   也可以指定其他链接文件：
   ```
   python clash_sub_converter.py my_links.txt
   ```

3. 生成的配置文件将保存为 `merged_config.yaml`

## 配置说明

在 `clash_sub_converter.py` 中，你可以修改以下配置：

- `OUTPUT_FILE`: 输出的配置文件名
- `TARGET_TYPE`: 目标配置类型
- `DEFAULT_LINKS_FILE`: 默认的订阅链接文件
- `FILTER_KEYWORDS`: 要过滤的关键词列表
- `FILTER_PATTERNS`: 要过滤的正则表达式模式

## 过滤规则

脚本会过滤掉包含以下内容的节点：
1. 包含广告关键词的节点（如"剩余流量"、"官网"等）
2. 匹配正则表达式的节点
3. 包含过多特殊字符的节点

你可以根据需要在脚本中修改 `FILTER_KEYWORDS` 和 `FILTER_PATTERNS` 列表。

## 注意事项

- 本需要本地运行 subconverter 服务（默认在 http://127.0.0.1:25500/sub）
- 首次运行时可能需要允许防火墙访问

## 许可证

MIT 
