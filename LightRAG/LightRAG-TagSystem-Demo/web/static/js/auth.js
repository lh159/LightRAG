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
    const data = {
        username: formData.get('username'),
        password: formData.get('password')
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
            showMessage('登录成功，正在跳转...', 'success');
            
            // 保存token
            localStorage.setItem('auth_token', result.token);
            
            // 跳转到主页
            setTimeout(() => {
                window.location.href = '/';
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
    const password = formData.get('password');
    const confirmPassword = formData.get('confirmPassword');
    
    if (password !== confirmPassword) {
        showMessage('两次输入的密码不一致', 'error');
        return;
    }
    
    const data = {
        username: formData.get('username'),
        password: password,
        email: formData.get('email') || null
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
            showMessage('注册成功，正在跳转...', 'success');
            
            // 保存token
            localStorage.setItem('auth_token', result.token);
            
            // 跳转到主页
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            showMessage(result.error, 'error');
        }
    } catch (error) {
        showMessage('注册失败，请重试', 'error');
    }
}); 