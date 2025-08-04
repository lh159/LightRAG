#!/bin/bash

# LightRAG标签系统 - 腾讯云服务器部署脚本
# 使用方法: bash deploy_tencent_cloud.sh

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户，建议使用普通用户部署"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 更新系统
update_system() {
    log_info "更新系统包..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get upgrade -y
    elif command -v yum &> /dev/null; then
        sudo yum update -y
    else
        log_error "不支持的包管理器"
        exit 1
    fi
    log_success "系统更新完成"
}

# 安装基础依赖
install_basic_deps() {
    log_info "安装基础依赖..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3 python3-pip python3-venv git curl wget nginx supervisor
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3 python3-pip git curl wget nginx supervisor
    fi
    
    log_success "基础依赖安装完成"
}

# 创建项目目录
create_project_dir() {
    log_info "创建项目目录..."
    
    PROJECT_DIR="/opt/lightrag"
    sudo mkdir -p $PROJECT_DIR
    sudo chown $USER:$USER $PROJECT_DIR
    
    log_success "项目目录创建完成: $PROJECT_DIR"
    echo $PROJECT_DIR
}

# 克隆代码
clone_code() {
    local project_dir=$1
    log_info "克隆代码到服务器..."
    
    cd $project_dir
    if [ -d ".git" ]; then
        log_info "检测到现有Git仓库，拉取最新代码..."
        git pull origin main
    else
        git clone https://github.com/lh159/LightRAG.git .
    fi
    
    log_success "代码克隆完成"
}

# 创建虚拟环境
setup_virtual_env() {
    local project_dir=$1
    log_info "创建Python虚拟环境..."
    
    cd $project_dir
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    log_success "虚拟环境创建完成"
}

# 安装Python依赖
install_python_deps() {
    local project_dir=$1
    log_info "安装Python依赖..."
    
    cd $project_dir
    source venv/bin/activate
    
    # 安装依赖
    pip install -r requirements.txt
    
    log_success "Python依赖安装完成"
}

# 配置环境变量
setup_environment() {
    local project_dir=$1
    log_info "配置环境变量..."
    
    cd $project_dir
    
    # 创建环境变量文件
    cat > .env << EOF
# LightRAG环境配置
FLASK_ENV=production
FLASK_APP=web.app
OPENAI_API_KEY=sk-2e4c8701d3e048b794939a432ab956ab
DEEPSEEK_API_KEY=sk-2e4c8701d3e048b794939a432ab956ab
EOF
    
    log_success "环境变量配置完成"
}

# 创建数据库
setup_database() {
    local project_dir=$1
    log_info "初始化数据库..."
    
    cd $project_dir
    source venv/bin/activate
    
    # 运行数据库初始化
    python3 -c "
from app.utils.database import DatabaseManager
db_manager = DatabaseManager()
print('数据库初始化完成')
"
    
    log_success "数据库初始化完成"
}

# 创建管理员用户
create_admin_user() {
    local project_dir=$1
    log_info "创建管理员用户..."
    
    cd $project_dir
    source venv/bin/activate
    
    python3 -c "
from app.utils.database import DatabaseManager
db_manager = DatabaseManager()
result = db_manager.create_user('admin', 'admin123', 'admin@lightrag.com')
if result['success']:
    print('管理员用户创建成功')
    print('用户名: admin')
    print('密码: admin123')
else:
    print('管理员用户创建失败:', result['error'])
"
    
    log_success "管理员用户创建完成"
}

# 配置Nginx
setup_nginx() {
    local project_dir=$1
    log_info "配置Nginx..."
    
    # 创建Nginx配置文件
    sudo tee /etc/nginx/sites-available/lightrag << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias $project_dir/web/static;
        expires 30d;
    }
}
EOF
    
    # 启用站点
    sudo ln -sf /etc/nginx/sites-available/lightrag /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # 测试配置
    sudo nginx -t
    
    # 重启Nginx
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    log_success "Nginx配置完成"
}

# 配置Supervisor
setup_supervisor() {
    local project_dir=$1
    log_info "配置Supervisor..."
    
    # 创建Supervisor配置文件
    sudo tee /etc/supervisor/conf.d/lightrag.conf << EOF
[program:lightrag]
command=$project_dir/venv/bin/python $project_dir/run_demo.py
directory=$project_dir
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$project_dir/logs/lightrag.log
environment=FLASK_ENV="production"
EOF
    
    # 重新加载配置
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl start lightrag
    
    log_success "Supervisor配置完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        sudo ufw allow 22
        sudo ufw allow 80
        sudo ufw allow 443
        sudo ufw --force enable
    elif command -v firewall-cmd &> /dev/null; then
        sudo firewall-cmd --permanent --add-service=ssh
        sudo firewall-cmd --permanent --add-service=http
        sudo firewall-cmd --permanent --add-service=https
        sudo firewall-cmd --reload
    fi
    
    log_success "防火墙配置完成"
}

# 创建启动脚本
create_startup_script() {
    local project_dir=$1
    log_info "创建启动脚本..."
    
    cat > $project_dir/start.sh << EOF
#!/bin/bash
cd $project_dir
source venv/bin/activate
python run_demo.py
EOF
    
    chmod +x $project_dir/start.sh
    
    log_success "启动脚本创建完成"
}

# 创建停止脚本
create_stop_script() {
    local project_dir=$1
    log_info "创建停止脚本..."
    
    cat > $project_dir/stop.sh << EOF
#!/bin/bash
sudo supervisorctl stop lightrag
EOF
    
    chmod +x $project_dir/stop.sh
    
    log_success "停止脚本创建完成"
}

# 创建重启脚本
create_restart_script() {
    local project_dir=$1
    log_info "创建重启脚本..."
    
    cat > $project_dir/restart.sh << EOF
#!/bin/bash
sudo supervisorctl restart lightrag
EOF
    
    chmod +x $project_dir/restart.sh
    
    log_success "重启脚本创建完成"
}

# 显示部署信息
show_deployment_info() {
    local project_dir=$1
    log_success "🎉 LightRAG标签系统部署完成！"
    
    echo
    echo "📋 部署信息:"
    echo "   项目目录: $project_dir"
    echo "   访问地址: http://$(curl -s ifconfig.me)"
    echo "   管理员账户: admin / admin123"
    echo
    echo "🔧 管理命令:"
    echo "   启动服务: $project_dir/start.sh"
    echo "   停止服务: $project_dir/stop.sh"
    echo "   重启服务: $project_dir/restart.sh"
    echo "   查看日志: sudo supervisorctl tail lightrag"
    echo
    echo "⚠️  安全提醒:"
    echo "   1. 请立即修改管理员密码"
    echo "   2. 配置SSL证书"
    echo "   3. 定期备份数据"
    echo
}

# 主函数
main() {
    echo "🚀 LightRAG标签系统 - 腾讯云服务器部署脚本"
    echo "=========================================="
    
    # 检查root权限
    check_root
    
    # 更新系统
    update_system
    
    # 安装基础依赖
    install_basic_deps
    
    # 创建项目目录
    PROJECT_DIR=$(create_project_dir)
    
    # 克隆代码
    clone_code $PROJECT_DIR
    
    # 设置虚拟环境
    setup_virtual_env $PROJECT_DIR
    
    # 安装Python依赖
    install_python_deps $PROJECT_DIR
    
    # 配置环境变量
    setup_environment $PROJECT_DIR
    
    # 设置数据库
    setup_database $PROJECT_DIR
    
    # 创建管理员用户
    create_admin_user $PROJECT_DIR
    
    # 配置Nginx
    setup_nginx $PROJECT_DIR
    
    # 配置Supervisor
    setup_supervisor $PROJECT_DIR
    
    # 配置防火墙
    setup_firewall $PROJECT_DIR
    
    # 创建管理脚本
    create_startup_script $PROJECT_DIR
    create_stop_script $PROJECT_DIR
    create_restart_script $PROJECT_DIR
    
    # 显示部署信息
    show_deployment_info $PROJECT_DIR
}

# 运行主函数
main "$@" 