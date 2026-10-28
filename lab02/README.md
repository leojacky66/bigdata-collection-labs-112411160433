# 实验二：房源采集与 MySQL 存储

本次实际取得教学站10页、600条原始记录；按8个字段去重后保存498条。CSV与MySQL全部字段已核对，独立重跑新增0条。

- [实验报告](REPORT.md)
- [已执行的 Notebook](anjuke.ipynb)
- [已执行的截图证据补充 Notebook](截图证据补充.ipynb)
- [房源 CSV](data/houseinfo.csv)
- [真实在线采集清单](data/collection_summary.json)
- [入库核对记录](data/import_verification.json)

## 运行

先安装 `requirements.txt` 中的 Python 依赖，并在 MySQL 执行 `01_mysql_stage1.sql`。本次运行平台为 macOS，本机 MySQL 地址 `127.0.0.1:3306`；若在教师 Docker 的 Jupyter 中运行，应把数据库主机设为课程服务名 `mysql`。

打开 `anjuke.ipynb` 可回放保存的真实在线HTML并核对CSV、MySQL。密码通过 `LAB02_MYSQL_PASSWORD` 或交互输入提供，文件不保存密码。

`截图证据补充.ipynb`直接读取现有函数源码，展示真实文件名与行号，并核验归档、CSV及三条样本。它只读查询MySQL，不修改数据；分页单元读取原在线请求日志，不重新联网采集。

在线获取使用官方 Firecrawl CLI，安装方式为 `npm install -g firecrawl-cli`。然后运行 `python fetch_firecrawl.py`；如命令未在PATH，可用环境变量 `FIRECRAWL_COMMAND` 指定。程序沿下一页采集，遇验证、异常或上限停止，确认末页后才保存完整CSV。

使用已归档的响应可运行 `python fetch_firecrawl.py --replay`，不重复访问网站。回放清单单独写入 `data/replay_summary.json`，不会改写原始在线采集清单。

入库运行 `python import_houseinfo.py`，按8字段防重复，不清空现有表。这里处理课堂单人顺序运行；未提供并发写入保证。

## 结果图片说明

报告在对应步骤插入17张图片：

- `01—02`：第一阶段真实MySQL终端表结构与入库前0条。
- `03—06、10—13`：已执行Notebook单元的HTML导出页面截图，包含代码框选、原日志读取、CSV回读和三样本八字段核对。
- `14—15`：学生提供的浏览器开发者工具截图，展示房源父容器、标题和选择器匹配结果。第14张后加红框，原图存于 `evidence/14_selector_nodes_original.png`。
- `16—17`：正式CSV在WPS中的表头、数据及末尾行号。第1行为表头，第2—499行为498条数据，第500行起为空。
- `18—20`：2026-10-28学生实际执行的MySQL终端截图，分别展示`USE / SHOW TABLES / DESCRIBE`、`COUNT(*) AS after_count`得到498、八字段`ORDER BY id LIMIT 5`。第三张因终端宽度换行，保留原图内容。

### 本次三张MySQL终端截图

1. [数据库、表和字段结构](images/18_mysql_terminal_schema.png)
2. [入库后498条记录](images/19_mysql_terminal_count.png)
3. [前5条房源的8个字段](images/20_mysql_terminal_samples.png)

原`07—09`的Workbench截图仍保存在images目录，报告对应位置已改为终端截图。完整在线批次入库前236条的历史终端图未留存，对应数值保留原运行记录；本次截图核对当前结果。
