# Contact Manager · 通讯录管理系统

这是 Software Engineering（FZU–MU）课程的 Extreme Programming 项目。用户可以在浏览器中维护自己的通讯录，整理常用联系人，并通过 Excel 批量导入和导出。

## 功能

- 注册、登录和退出。每个账号有独立的通讯录。
- 新增、查看、编辑和删除联系人，支持备注及多条联系方式。界面支持电话、邮箱、地址、QQ、微信和个人网站。
- 收藏或取消收藏，并通过「我的收藏」查看常用联系人。
- 导入和导出 `.xlsx` 文件。导入失败时，页面会显示可用的行号、列名和错误原因。导出的文件可重新导入。

## 技术栈

前端使用 Vue 3 和 Vite，后端使用 Python 和 Flask。Vite 在本地开发时将 `/api` 请求转发到 Flask。后端用 SQLite 保存账号及联系人数据，用 openpyxl 处理 Excel 文件。

## 在 Windows 上运行

安装 Git、Python 3.13 和 Node.js 22.12 或更新版本。项目已使用 Python 3.13 和 Node.js 24 进行本地验证。下面的命令使用 PowerShell。

```powershell
git clone https://github.com/EthanChen251/832401103_832401105_ExtremeProgramming.git
cd 832401103_832401105_ExtremeProgramming
```

先打开一个 PowerShell 窗口，在仓库根目录执行以下命令启动 Flask。

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app contact_manager run --host 127.0.0.1 --port 5000
```

保持后端运行，再打开一个 PowerShell 窗口，在仓库根目录启动前端。

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

若锁文件中的 npm 镜像无法连接，可在 `frontend` 目录改用 npm 官方源安装同一批锁定版本。

```powershell
npm.cmd ci --registry=https://registry.npmjs.org/ --replace-registry-host=registry.npmmirror.com
```

打开 [本地通讯录](http://127.0.0.1:5173/)，点击「创建新账号」并注册。账号和联系人数据库会按需创建在 `backend/instance/` 下，重新启动应用后仍可使用。

需要构建前端时，在 `frontend` 目录运行 `npm.cmd run build`，生成的文件位于 `frontend/dist/`。

## Excel 导入导出

第一次批量导入可以先点击「导出 Excel」取得带表头的文件，再填入联系人。工作表名为 `Contacts`，每个联系人占一行。同一类别有多个值时，在单元格内换行。填写电话号码前请把对应列设为文本，以保留前导零和加号。完整表头和校验规则见 [API 与数据格式](API_SPEC.md)。

## 项目文档

- [API 与数据格式](API_SPEC.md)
- [项目计划书（中文）](docs/XP_Contact_Manager_Project_Plan_CN.md)
- [Project Plan (English)](docs/XP_Contact_Manager_Project_Plan_EN.md)
