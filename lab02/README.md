# 实验二：房源采集与 MySQL 存储

本次实际取得教学站10页、600条原始记录；按8个字段去重后保存498条。CSV与MySQL全部字段已核对，独立重跑新增0条。

- [实验报告](REPORT.md)
- [已执行的 Notebook](anjuke.ipynb)
- [房源 CSV](data/houseinfo.csv)
- [真实在线采集清单](data/collection_summary.json)
- [入库核对记录](data/import_verification.json)

## 运行

先安装 `requirements.txt` 中的 Python 依赖，并在 MySQL 执行 `01_mysql_stage1.sql`。本次运行平台为 macOS，本机 MySQL 地址 `127.0.0.1:3306`；若在教师 Docker 的 Jupyter 中运行，应把数据库主机设为课程服务名 `mysql`。

打开 `anjuke.ipynb` 可回放保存的真实在线HTML并核对CSV、MySQL。密码通过 `LAB02_MYSQL_PASSWORD` 或交互输入提供，文件不保存密码。

在线获取使用官方 Firecrawl CLI，安装方式为 `npm install -g firecrawl-cli`。然后运行 `python fetch_firecrawl.py`；如命令未在PATH，可用环境变量 `FIRECRAWL_COMMAND` 指定。程序沿下一页采集，遇验证、异常或上限停止，确认末页后才保存完整CSV。

使用已归档的响应可运行 `python fetch_firecrawl.py --replay`，不重复访问网站。回放清单单独写入 `data/replay_summary.json`，不会改写原始在线采集清单。

入库运行 `python import_houseinfo.py`，按8字段防重复，不清空现有表。这里处理课堂单人顺序运行；未提供并发写入保证。

## 结果图片说明

第一阶段两张图片来自真实 MySQL 终端。其余图片是已执行 Notebook 单元的HTML导出页面截图，代码、输出保持对应，并用红框标出代码；这些导出图不能称为IDE或MySQL终端界面截图。尚未补充浏览器 Copy selector 操作图及第三阶段 MySQL终端界面图，详见报告。
