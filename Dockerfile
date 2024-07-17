# 使用官方的 Python 基础镜像
FROM python:3.12

# 设置工作目录
WORKDIR /app

# 将 requirements.txt 复制到容器中
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将当前目录中的所有文件复制到工作目录中
COPY . .

# 设置环境变量，确保 Python 输出是可以直接查看的
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 指定运行命令（根据你的项目实际情况修改）
CMD ["python", "lab.py"]
