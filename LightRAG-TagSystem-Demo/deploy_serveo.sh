#!/bin/bash
# LightRAG系统 - Serveo一键部署脚本（最简单方案）

echo "⚡ 使用Serveo部署LightRAG系统..."
echo "🔥 这是最简单的内网穿透方案，无需安装任何软件！"

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

# 清理可能存在的进程
echo "🧹 清理旧进程..."
pkill -f "python.*run_demo" 2>/dev/null || true
pkill -f "ssh.*serveo" 2>/dev/null || true
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

# 创建Serveo隧道
echo "🌐 创建Serveo隧道..."
echo "⚠️  正在连接serveo.net，请稍候..."

# 使用自定义域名
ssh -o StrictHostKeyChecking=no -R lightrag:80:localhost:5000 serveo.net &
SERVEO_PID=$!

# 等待连接建立
sleep 5

echo ""
echo "🎉 ================================="
echo "✅ 部署完成！"
echo "================================="
echo "📱 本地访问: http://127.0.0.1:5000"
echo "🌐 公网访问: https://lightrag.serveo.net"
echo "⚠️  如果自定义域名被占用，会分配随机域名"
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
echo "   Serveo PID: $SERVEO_PID"
echo ""

echo "按 Ctrl+C 或 Enter 键停止服务..."

# 设置清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill $FLASK_PID 2>/dev/null || true
    kill $SERVEO_PID 2>/dev/null || true
    
    # 等待进程结束
    sleep 2
    
    # 强制杀死如果还在运行
    pkill -f "python.*run_demo" 2>/dev/null || true
    pkill -f "ssh.*serveo" 2>/dev/null || true
    
    echo "✅ 服务已停止"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 等待用户输入
read

# 执行清理
cleanup 