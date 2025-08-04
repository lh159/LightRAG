#!/bin/bash
# LightRAG系统 - Ngrok自动化部署脚本

echo "🚀 启动LightRAG系统与Ngrok隧道..."

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

# 检查ngrok
if ! command -v ngrok &> /dev/null; then
    echo "❌ 错误: 未安装ngrok"
    echo "💡 请先安装ngrok: brew install ngrok"
    exit 1
fi

# 清理可能存在的进程
echo "🧹 清理旧进程..."
pkill -f "python.*run_demo" 2>/dev/null || true
pkill -f "ngrok http" 2>/dev/null || true
sleep 2

# 1. 启动Flask应用
echo "📱 启动Flask应用..."
source lightrag_env/bin/activate
python run_demo.py &
FLASK_PID=$!
echo "Flask PID: $FLASK_PID"

# 2. 等待Flask启动
echo "⏳ 等待Flask启动..."
sleep 8

# 3. 检查Flask是否成功启动
if ! curl -s http://127.0.0.1:5000/ > /dev/null; then
    echo "❌ Flask启动失败"
    kill $FLASK_PID 2>/dev/null || true
    exit 1
fi
echo "✅ Flask启动成功"

# 4. 启动ngrok隧道
echo "🌐 启动Ngrok隧道..."
ngrok http 5000 --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
echo "Ngrok PID: $NGROK_PID"

# 5. 等待ngrok启动
echo "⏳ 等待Ngrok启动..."
sleep 8

# 6. 获取公网URL
echo "🔗 获取公网访问地址..."
max_attempts=5
attempt=1

while [ $attempt -le $max_attempts ]; do
    PUBLIC_URL=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('tunnels') and len(data['tunnels']) > 0:
        print(data['tunnels'][0]['public_url'])
    else:
        print('')
except:
    print('')
" 2>/dev/null)

    if [ -n "$PUBLIC_URL" ] && [ "$PUBLIC_URL" != "" ]; then
        break
    fi
    
    echo "⏳ 尝试获取URL... ($attempt/$max_attempts)"
    sleep 3
    attempt=$((attempt + 1))
done

# 7. 显示部署结果
echo ""
echo "🎉 ================================="
echo "✅ 部署完成！"
echo "================================="
echo "📱 本地访问: http://127.0.0.1:5000"
if [ -n "$PUBLIC_URL" ] && [ "$PUBLIC_URL" != "" ]; then
    echo "🌐 公网访问: $PUBLIC_URL"
    echo "⚠️  首次访问需要点击ngrok警告页面的'Visit Site'"
else
    echo "❌ 无法获取公网URL，请检查ngrok状态"
fi
echo "🎛️  Ngrok控制台: http://127.0.0.1:4040"
echo "================================="
echo ""

# 8. 显示使用说明
echo "💡 使用说明:"
echo "   1. 使用管理员账户登录: admin / admin123"
echo "   2. 或使用测试账户: testuser / testpass123"
echo "   3. 在聊天界面与AI助手对话"
echo "   4. 观察用户画像的实时更新"
echo ""

# 9. 显示进程信息
echo "🔧 进程信息:"
echo "   Flask PID: $FLASK_PID"
echo "   Ngrok PID: $NGROK_PID"
echo ""

# 10. 等待用户输入后清理
echo "按 Ctrl+C 或 Enter 键停止服务..."

# 设置清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill $FLASK_PID 2>/dev/null || true
    kill $NGROK_PID 2>/dev/null || true
    
    # 等待进程结束
    sleep 2
    
    # 强制杀死如果还在运行
    pkill -f "python.*run_demo" 2>/dev/null || true
    pkill -f "ngrok http" 2>/dev/null || true
    
    echo "✅ 服务已停止"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 等待用户输入
read

# 执行清理
cleanup 