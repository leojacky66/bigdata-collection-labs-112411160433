# 实验三分步练习

[打开练习本](qqmail_lab03_practice.ipynb) · [查看正式实验报告](实验报告-Playwright版.md)

这份练习本覆盖两个阶段。先用 Playwright 扫码进入 QQ 邮箱，再逐格练习字段定位、读取发件人卡片、采集 10 封、写入 CSV 和核对样本。

## 在 Mac 上开始

使用 macOS 14 或更新版本。先检查终端里的 `python3 --version`。课程环境使用 Python 3.12，Mac 也可以用这个版本。[Playwright 系统要求](https://playwright.dev/python/docs/intro#system-requirements) · [Python for macOS](https://www.python.org/downloads/macos/)

在 GitHub 仓库首页点 **Code → Download ZIP** 并解压。打开「终端」，切到解压后的 `lab03` 文件夹。可以先输入 `cd `（含空格），再把 Finder 中的 `lab03` 文件夹拖进终端并回车。

第一次安装时逐行执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install jupyterlab ipykernel playwright pandas
python -m playwright install chromium
jupyter lab
```

浏览器打开 JupyterLab 后，选择 `qqmail_lab03_practice.ipynb`，内核选择 **Python 3**。第 2 格会打开 Mac 本机的 Chromium 窗口，到第 5 步时用手机 QQ 在那个窗口扫码。以后在同一目录执行 `source .venv/bin/activate` 和 `jupyter lab` 即可。[JupyterLab 安装说明](https://jupyterlab.readthedocs.io/en/stable/getting_started/installation.html) · [Playwright 浏览器安装说明](https://playwright.dev/python/docs/browsers#install-browsers)

## 换电脑后怎么接着学

当前接续点是 **第 11 步（一）：按 ID 找回邮件并设置滚动位置**。新电脑的 Jupyter 内核需要重新创建浏览器、页面和字段变量。先按顺序运行第 1～10 步，在第 5 步扫码确认，然后继续第 11 步。一次运行一个代码格，便于看到每一步输出。

在 Windows 课程 Docker 中，把练习本放在 `workspace/lab03/`，从课程可视化入口启动。练习本会自动找到同级的 `L07_L08_visual`，Chromium 画面显示在 noVNC。

练习生成的原始 CSV 保存在本地 `private_data/practice/`。GitHub 上的练习本已清空运行输出。请把原始 CSV、登录凭据和含私人邮件内容的截图留在本机。
