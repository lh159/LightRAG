#!/bin/bash
# LightRAG系统 - Cloudflare Tunnel一键部署脚本（推荐方案）

echo "🌟 使用Cloudflare Tunnel部署LightRAG系统..."
echo "🔥 这是最稳定的免费内网穿透方案！"

# 检查当前目录
if [ ! -f "run_demo.py" ]; then
    echo "❌ 错误: 请在LightRAG-TagSystem-Demo目录中运行此脚本"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "lightrag_env" ]; then
    echo "❌ 错误: 未找到虚拟环境lightrag_env"
    exit 1
fi

# 检查并安装cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "📦 安装cloudflared..."
    if command -v brew &> /dev/null; then
        brew install cloudflared
    else
        echo "正在下载cloudflared..."
        curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz -o /tmp/cloudflared.tgz
        tar -xzf /tmp/cloudflared.tgz -C /tmp/
        sudo mv /tmp/cloudflared /usr/local/bin/
        chmod +x /usr/local/bin/cloudflared
    fi
    
    if ! command -v cloudflared &> /dev/null; then
        echo "❌ cloudflared安装失败"
        exit 1
    fi
    echo "✅ cloudflared安装成功"
fi

# 清理可能存在的进程
echo "🧹 清理旧进程..."
pkill -f "python.*run_demo" 2>/dev/null || true
pkill -f "cloudflared.*tunnel" 2>/dev/null || true
sleep 2

# 启动Flask应用
echo "📱 启动Flask应用..."
source lightrag_env/bin/activate
python run_demo.py &
FLASK_PID=$!
echo "Flask PID: $FLASK_PID"

# 等待Flask启动
echo "⏳ 等待Flask启动..."
sleep 8

# 检查Flask是否成功启动
if ! curl -s http://127.0.0.1:5000/ > /dev/null; then
    echo "❌ Flask启动失败"
    kill $FLASK_PID 2>/dev/null || true
    exit 1
fi
echo "✅ Flask启动成功"

# 创建Cloudflare隧道
echo "🌐 创建Cloudflare隧道..."
echo "⚠️  正在建立隧道，请稍候..."

cloudflared tunnel --url http://localhost:5000 > /tmp/cloudflare.log 2>&1 &
CF_PID=$!

# 等待隧道建立并获取URL
echo "⏳ 等待隧道建立..."
sleep 10

# 从日志中提取URL
PUBLIC_URL=""
for i in {1..10}; do
    if [ -f /tmp/cloudflare.log ]; then
        PUBLIC_URL=$(grep -o 'https://[^[:space:]]*\.trycloudflare\.com' /tmp/cloudflare.log | head -1)
        if [ -n "$PUBLIC_URL" ]; then
            break
        fi
    fi
    sleep 2
done

echo ""
echo "🎉 ================================="
echo "✅ 部署完成！"
echo "================================="
echo "📱 本地访问: http://127.0.0.1:5000"
if [ -n "$PUBLIC_URL" ]; then
    echo "🌐 公网访问: $PUBLIC_URL"
else
    echo "🌐 公网访问: 请查看上方输出的cloudflare地址"
fi
echo "⚠️  Cloudflare隧道无需点击警告页面，直接访问"
echo "================================="
echo ""

echo "💡 使用说明:"
echo "   1. 使用管理员账户登录: admin / admin123"
echo "   2. 或使用测试账户: testuser / testpass123"
echo "   3. 在聊天界面与AI助手对话"
echo "   4. 观察用户画像的实时更新"
echo ""

echo "🔧 进程信息:"
echo "   Flask PID: $FLASK_PID"
echo "   Cloudflare PID: $CF_PID"
echo ""

echo "按 Ctrl+C 或 Enter 键停止服务..."

# 设置清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill $FLASK_PID 2>/dev/null || true
    kill $CF_PID 2>/dev/null || true
    
    # 等待进程结束
    sleep 2
    
    # 强制杀死如果还在运行
    pkill -f "python.*run_demo" 2>/dev/null || true
    pkill -f "cloudflared.*tunnel" 2>/dev/null || true
    
    # 清理临时文件
    rm -f /tmp/cloudflare.log
    
    echo "✅ 服务已停止"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 等待用户输入
read

# 执行清理
cleanup 