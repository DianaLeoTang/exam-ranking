# exam-ranking
# 公共卫生考研成绩排名系统 — 部署说明

## 文件结构

```
exam_ranking/
├── app.py          # Flask 后端
├── nginx.conf      # Nginx 配置参考
├── README.md       # 本文件
└── static/
    └── index.html  # 前端页面
```

---

## 本地开发（Conda 环境）

创建并激活同名 conda 环境：

```bash
# 创建环境
conda create -n exam-ranking python=3 -y

# 激活环境
conda activate exam-ranking

# 安装依赖
pip install flask flask-cors

# 运行
python app.py
```

---

## 第一步：上传文件到服务器

用 FTP 或 scp 把整个 exam_ranking 文件夹上传到服务器，例如放在 /var/www/exam_ranking/

```bash
scp -r exam_ranking/ root@你的服务器IP:/var/www/
```

---

## 第二步：安装 Python 依赖

```bash
cd /var/www/exam_ranking
pip3 install flask flask-cors gunicorn
```

---

## 第三步：修改管理员密码

打开 app.py，找到这一行改成自己的密码：

```python
ADMIN_PASSWORD = 'pku2024'   # ← 改这里
```

---

## 第四步：用 systemd 让程序后台运行（开机自启）

创建服务文件：
```bash
nano /etc/systemd/system/examranking.service
```

写入以下内容（注意修改路径）：
```ini
[Unit]
Description=Exam Ranking App
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/exam_ranking
ExecStart=gunicorn -w 2 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
systemctl daemon-reload
systemctl enable examranking
systemctl start examranking
systemctl status examranking   # 确认 active (running)
```

---

## 第五步：配置 Nginx

```bash
# 安装 Nginx（如果还没装）
apt install nginx   # Ubuntu
# 或
yum install nginx   # CentOS

# 复制配置文件
cp /var/www/exam_ranking/nginx.conf /etc/nginx/sites-available/examranking
ln -s /etc/nginx/sites-available/examranking /etc/nginx/sites-enabled/

# 修改配置里的域名
nano /etc/nginx/sites-available/examranking

# 测试 + 重启
nginx -t
systemctl restart nginx
```

---

## 第六步：开放防火墙端口

```bash
# 阿里云/腾讯云还需要在控制台安全组里开放 80 端口
ufw allow 80    # Ubuntu 本机防火墙
```

---

## 第七步（可选）：配置 HTTPS

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d 你的域名.com
```

Certbot 会自动修改 Nginx 配置并续期证书，完成后访问 https://你的域名.com 即可。

---

## 常用维护命令

```bash
# 查看运行状态
systemctl status examranking

# 重启服务
systemctl restart examranking

# 查看日志
journalctl -u examranking -f

# 数据库文件位置（SQLite）
/var/www/exam_ranking/scores.db

# 手动备份数据
cp /var/www/exam_ranking/scores.db ~/scores_backup_$(date +%Y%m%d).db
```

---

## 数据说明

- 所有用户提交的成绩写入 `scores.db`（SQLite 文件）
- 页面每 30 秒自动刷新一次排名
- 删除记录需要输入管理员密码
- 建议定期备份 scores.db 文件
