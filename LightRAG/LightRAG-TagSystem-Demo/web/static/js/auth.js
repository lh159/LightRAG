// 认证页面JavaScript
let currentTab = 'login';

function switchTab(tab) {
    currentTab = tab;
    
    // 更新按钮状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // 切换表单显示
    if (tab === 'login') {
        document.getElementById('loginForm').style.display = 'block';
        document.getElementById('registerForm').style.display = 'none';
    } else {
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('registerForm').style.display = 'block';
    }
    
    // 清除消息
    clearMessage();
}

// 验证手机号格式
function validatePhoneNumber(phone) {
    const phoneRegex = /^1[3-9]\d{9}$/;
    return phoneRegex.test(phone);
}

// 快速登录（仅手机号）
async function quickLogin() {
    const phoneInput = document.getElementById('loginPhone');
    const phone = phoneInput.value.trim();
    
    if (!phone) {
        showMessage('请输入手机号', 'error');
        return;
    }
    
    if (!validatePhoneNumber(phone)) {
        showMessage('请输入正确的手机号格式', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/quick-login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ phone_number: phone })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 保存token和用户信息
            localStorage.setItem('auth_token', result.token);
            localStorage.setItem('user_info', JSON.stringify(result.user));
            
            if (result.user.is_admin) {
                // 管理员用户，询问进入哪个界面
                const choice = confirm('您是管理员用户，是否进入管理员看板？\n\n点击"确定"进入管理员看板\n点击"取消"进入普通用户界面');
                showMessage('管理员登录成功！', 'success');
                setTimeout(() => {
                    if (choice) {
                        window.location.href = '/admin';
                    } else {
                        window.location.href = '/';
                    }
                }, 1000);
            } else {
                showMessage('登录成功！', 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            }
        } else {
            showMessage(result.error, 'error');
        }
    } catch (error) {
        showMessage('快速登录失败，请重试', 'error');
    }
}

function showMessage(message, type = 'success') {
    const messageEl = document.getElementById('message');
    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
}

function clearMessage() {
    const messageEl = document.getElementById('message');
    messageEl.textContent = '';
    messageEl.className = 'message';
}

// 登录表单处理
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const phone = formData.get('phone_number').trim();
    const password = formData.get('password').trim();
    
    // 验证手机号格式
    if (!validatePhoneNumber(phone)) {
        showMessage('请输入正确的手机号格式', 'error');
        return;
    }
    
    const data = {
        phone_number: phone,
        password: password || undefined
    };
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(`欢迎${result.user.is_admin ? '管理员' : ''}用户，登录成功！`, 'success');
            
            // 保存token和用户信息
            localStorage.setItem('auth_token', result.token);
            localStorage.setItem('user_info', JSON.stringify(result.user));
            
            // 根据用户角色跳转
            setTimeout(() => {
                if (result.user.is_admin) {
                    window.location.href = '/admin';
                } else {
                    window.location.href = '/';
                }
            }, 1000);
        } else {
            showMessage(result.error, 'error');
        }
    } catch (error) {
        showMessage('登录失败，请重试', 'error');
    }
});

// 注册表单处理
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const phone = formData.get('phone_number').trim();
    const password = formData.get('password').trim();
    const confirmPassword = formData.get('confirmPassword').trim();
    const username = formData.get('username').trim();
    const email = formData.get('email').trim();
    
    // 验证手机号格式
    if (!validatePhoneNumber(phone)) {
        showMessage('请输入正确的手机号格式', 'error');
        return;
    }
    
    // 如果设置了密码，验证密码一致性
    if (password && password !== confirmPassword) {
        showMessage('两次输入的密码不一致', 'error');
        return;
    }
    
    const data = {
        phone_number: phone,
        password: password || undefined,
        username: username || undefined,
        email: email || undefined
    };
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(`注册成功！欢迎${result.user.is_admin ? '管理员' : ''}用户`, 'success');
            
            // 保存token和用户信息
            localStorage.setItem('auth_token', result.token);
            localStorage.setItem('user_info', JSON.stringify(result.user));
            
            // 根据用户角色跳转
            setTimeout(() => {
                if (result.user.is_admin) {
                    window.location.href = '/admin';
                } else {
                    window.location.href = '/';
                }
            }, 1000);
        } else {
            showMessage(result.error, 'error');
        }
    } catch (error) {
        showMessage('注册失败，请重试', 'error');
    }
});

// 监听注册密码输入，动态显示确认密码字段
document.getElementById('registerPassword').addEventListener('input', function() {
    const confirmGroup = document.getElementById('confirmPasswordGroup');
    if (this.value.trim()) {
        confirmGroup.style.display = 'block';
        document.getElementById('confirmPassword').required = true;
    } else {
        confirmGroup.style.display = 'none';
        document.getElementById('confirmPassword').required = false;
        document.getElementById('confirmPassword').value = '';
    }
}); 