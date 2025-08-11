// 管理员看板JavaScript
let currentSection = 'overview';
let usersData = [];
let filteredUsers = [];
let currentPage = 1;
const usersPerPage = 10;

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    checkAdminAuth();
    initializeDashboard();
    loadDashboardData();
});

// 检查管理员权限
function checkAdminAuth() {
    const token = localStorage.getItem('auth_token');
    const userInfoStr = localStorage.getItem('user_info');
    
    console.log('Token:', token);
    console.log('User info string:', userInfoStr);
    
    if (!token) {
        alert('请先登录');
        window.location.href = '/login';
        return;
    }
    
    let userInfo = {};
    try {
        userInfo = JSON.parse(userInfoStr || '{}');
        console.log('Parsed user info:', userInfo);
    } catch (e) {
        console.error('Failed to parse user info:', e);
        alert('用户信息异常，请重新登录');
        localStorage.clear();
        window.location.href = '/login';
        return;
    }
    
    // 检查管理员权限 - 支持多种判断方式
    const isAdmin = userInfo.is_admin === true || 
                   userInfo.role === 'admin' || 
                   userInfo.phone_number === '19802025320';
    
    console.log('Is admin check:', {
        'userInfo.is_admin': userInfo.is_admin,
        'userInfo.role': userInfo.role,
        'userInfo.phone_number': userInfo.phone_number,
        'final isAdmin': isAdmin
    });
    
    if (!isAdmin) {
        alert('需要管理员权限访问此页面');
        window.location.href = '/login';
        return;
    }
    
    // 显示当前管理员信息
    const adminName = userInfo.username || userInfo.phone_number || '管理员';
    const adminElement = document.getElementById('currentAdmin');
    if (adminElement) {
        adminElement.textContent = adminName;
    }
}

// 初始化看板
function initializeDashboard() {
    // 绑定侧边栏菜单事件
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', function() {
            const section = this.getAttribute('data-section');
            switchSection(section);
        });
    });
    
    // 绑定搜索事件
    document.getElementById('userSearch').addEventListener('input', function() {
        filterUsers();
    });
}

// 切换页面区域
function switchSection(section) {
    // 更新菜单状态
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${section}"]`).classList.add('active');
    
    // 更新内容区域
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
    });
    document.getElementById(`${section}-section`).classList.add('active');
    
    // 更新页面标题
    const titles = {
        'overview': '系统总览',
        'users': '用户管理',
        'tags': '标签分析',
        'analytics': '数据分析'
    };
    document.getElementById('pageTitle').textContent = titles[section];
    
    currentSection = section;
    
    // 根据区域加载相应数据
    switch(section) {
        case 'overview':
            loadOverviewData();
            break;
        case 'users':
            loadUsersData();
            break;
        case 'tags':
            loadTagsData();
            break;
        case 'analytics':
            loadAnalyticsData();
            break;
    }
}

// 加载看板数据
async function loadDashboardData() {
    await loadOverviewData();
}

// 加载总览数据
async function loadOverviewData() {
    try {
        const token = localStorage.getItem('auth_token');
        
        // 获取统计数据
        const statsResponse = await fetch('/api/user/admin/statistics', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            updateStatsCards(statsData.statistics);
            updateCharts(statsData.statistics);
        } else {
            console.error('Failed to load statistics');
        }
    } catch (error) {
        console.error('Error loading overview data:', error);
    }
}

// 更新统计卡片
function updateStatsCards(stats) {
    document.getElementById('totalUsers').textContent = stats.total_users || 0;
    document.getElementById('adminCount').textContent = stats.admin_count || 0;
    document.getElementById('dailyActive').textContent = stats.daily_active || 0;
    
    // 计算总标签数
    const totalTags = Object.values(stats.tag_statistics || {}).reduce((sum, count) => sum + count, 0);
    document.getElementById('totalTags').textContent = totalTags;
}

// 更新图表
function updateCharts(stats) {
    updateTagDistributionChart(stats.tag_statistics || {});
    updateUserActivityChart();
}

// 更新标签分布图表
function updateTagDistributionChart(tagStats) {
    const ctx = document.getElementById('tagDistributionChart').getContext('2d');
    
    // 销毁现有图表
    if (window.tagChart) {
        window.tagChart.destroy();
    }
    
    const labels = Object.keys(tagStats);
    const data = Object.values(tagStats);
    const colors = [
        '#3498db', '#e74c3c', '#f39c12', '#27ae60',
        '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
    ];
    
    window.tagChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// 更新用户活跃度图表
function updateUserActivityChart() {
    const ctx = document.getElementById('userActivityChart').getContext('2d');
    
    // 销毁现有图表
    if (window.activityChart) {
        window.activityChart.destroy();
    }
    
    // 模拟最近7天的数据
    const labels = [];
    const data = [];
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }));
        data.push(Math.floor(Math.random() * 20) + 5);
    }
    
    window.activityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '活跃用户数',
                data: data,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// 加载用户数据
async function loadUsersData() {
    try {
        const token = localStorage.getItem('auth_token');
        console.log('Token from localStorage:', token ? token.substring(0, 20) + '...' : 'null');
        
        if (!token) {
            console.error('No auth token found');
            return;
        }
        
        const response = await fetch('/api/user/admin/users', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('Users data received:', data);
            usersData = data.users;
            filteredUsers = [...usersData];
            renderUsersTable();
            renderPagination();
        } else {
            const errorData = await response.text();
            console.error('Failed to load users data:', response.status, errorData);
        }
    } catch (error) {
        console.error('Error loading users data:', error);
    }
}

// 渲染用户表格
function renderUsersTable() {
    const tbody = document.getElementById('usersTableBody');
    const start = (currentPage - 1) * usersPerPage;
    const end = start + usersPerPage;
    const pageUsers = filteredUsers.slice(start, end);
    
    tbody.innerHTML = pageUsers.map(user => `
        <tr>
            <td>${user.phone_number}</td>
            <td>${user.username || '未设置'}</td>
            <td>
                <span class="role-badge role-${user.role}">
                    ${user.role === 'admin' ? '管理员' : '普通用户'}
                </span>
            </td>
            <td>${formatDate(user.created_at)}</td>
            <td>${user.last_login ? formatDate(user.last_login) : '从未登录'}</td>
            <td>
                <span class="status-badge status-${user.is_active ? 'active' : 'inactive'}">
                    ${user.is_active ? '活跃' : '非活跃'}
                </span>
            </td>
            <td>
                <button class="action-btn" onclick="viewUserDetail('${user.phone_number}')">
                    查看详情
                </button>
            </td>
        </tr>
    `).join('');
}

// 渲染分页
function renderPagination() {
    const totalPages = Math.ceil(filteredUsers.length / usersPerPage);
    const pagination = document.getElementById('usersPagination');
    
    let paginationHTML = '';
    
    // 上一页
    if (currentPage > 1) {
        paginationHTML += `<button class="page-btn" onclick="changePage(${currentPage - 1})">上一页</button>`;
    }
    
    // 页码
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
    }
    
    // 下一页
    if (currentPage < totalPages) {
        paginationHTML += `<button class="page-btn" onclick="changePage(${currentPage + 1})">下一页</button>`;
    }
    
    pagination.innerHTML = paginationHTML;
}

// 切换页面
function changePage(page) {
    currentPage = page;
    renderUsersTable();
    renderPagination();
}

// 筛选用户
function filterUsers() {
    const searchTerm = document.getElementById('userSearch').value.toLowerCase();
    const roleFilter = document.getElementById('roleFilter')?.value || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    
    filteredUsers = usersData.filter(user => {
        const matchesSearch = user.phone_number.toLowerCase().includes(searchTerm) ||
                            (user.username && user.username.toLowerCase().includes(searchTerm));
        
        const matchesRole = !roleFilter || user.role === roleFilter;
        
        const matchesStatus = !statusFilter || 
                            (statusFilter === 'active' && user.is_active) ||
                            (statusFilter === 'inactive' && !user.is_active);
        
        return matchesSearch && matchesRole && matchesStatus;
    });
    
    currentPage = 1;
    renderUsersTable();
    renderPagination();
}

// 切换筛选面板
function toggleFilters() {
    const panel = document.getElementById('filterPanel');
    panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
}

// 应用筛选
function applyFilters() {
    filterUsers();
}

// 查看用户详情
async function viewUserDetail(phoneNumber) {
    try {
        const token = localStorage.getItem('auth_token');
        
        const response = await fetch(`/api/user/admin/users/${phoneNumber}/profile`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            showUserDetailModal(data.user);
        } else {
            alert('获取用户详情失败');
        }
    } catch (error) {
        console.error('Error loading user detail:', error);
        alert('获取用户详情失败');
    }
}

// 显示用户详情模态框
function showUserDetailModal(user) {
    const modal = document.getElementById('userDetailModal');
    const content = document.getElementById('userDetailContent');
    
    let tagsHTML = '';
    if (user.tags && Object.keys(user.tags).length > 0) {
        tagsHTML = Object.entries(user.tags).map(([dimension, tags]) => `
            <div class="tag-dimension">
                <h4>${dimension}</h4>
                <div class="tags-list">
                    ${tags.map(tag => `
                        <span class="tag-item" title="置信度: ${tag.confidence}">
                            ${tag.tag_name} (${(tag.confidence * 100).toFixed(1)}%)
                        </span>
                    `).join('')}
                </div>
            </div>
        `).join('');
    } else {
        tagsHTML = '<p class="no-tags">暂无标签数据</p>';
    }
    
    content.innerHTML = `
        <div class="user-detail">
            <div class="user-basic-info">
                <h3>基本信息</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <label>手机号:</label>
                        <span>${user.phone_number}</span>
                    </div>
                    <div class="info-item">
                        <label>用户名:</label>
                        <span>${user.username || '未设置'}</span>
                    </div>
                    <div class="info-item">
                        <label>邮箱:</label>
                        <span>${user.email || '未设置'}</span>
                    </div>
                    <div class="info-item">
                        <label>角色:</label>
                        <span class="role-badge role-${user.role}">
                            ${user.role === 'admin' ? '管理员' : '普通用户'}
                        </span>
                    </div>
                    <div class="info-item">
                        <label>状态:</label>
                        <span class="status-badge status-${user.is_active ? 'active' : 'inactive'}">
                            ${user.is_active ? '活跃' : '非活跃'}
                        </span>
                    </div>
                    <div class="info-item">
                        <label>注册时间:</label>
                        <span>${formatDate(user.created_at)}</span>
                    </div>
                    <div class="info-item">
                        <label>最后登录:</label>
                        <span>${user.last_login ? formatDate(user.last_login) : '从未登录'}</span>
                    </div>
                </div>
            </div>
            
            <div class="user-tags">
                <h3>用户标签</h3>
                ${tagsHTML}
            </div>
        </div>
        
        <style>
            .user-detail { padding: 10px 0; }
            .user-basic-info, .user-tags { margin-bottom: 25px; }
            .user-basic-info h3, .user-tags h3 { 
                color: #2c3e50; 
                margin-bottom: 15px; 
                border-bottom: 2px solid #3498db; 
                padding-bottom: 5px; 
            }
            .info-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 15px; 
            }
            .info-item { 
                display: flex; 
                flex-direction: column; 
                gap: 5px; 
            }
            .info-item label { 
                font-weight: 600; 
                color: #7f8c8d; 
                font-size: 12px; 
            }
            .tag-dimension { 
                margin-bottom: 20px; 
            }
            .tag-dimension h4 { 
                color: #34495e; 
                margin-bottom: 10px; 
            }
            .tags-list { 
                display: flex; 
                flex-wrap: wrap; 
                gap: 8px; 
            }
            .tag-item { 
                background: #ecf0f1; 
                padding: 5px 10px; 
                border-radius: 15px; 
                font-size: 12px; 
                color: #2c3e50; 
                border-left: 3px solid #3498db; 
            }
            .no-tags { 
                color: #7f8c8d; 
                font-style: italic; 
                text-align: center; 
                padding: 20px; 
            }
        </style>
    `;
    
    modal.style.display = 'block';
}

// 关闭模态框
function closeModal() {
    document.getElementById('userDetailModal').style.display = 'none';
}

// 加载标签数据
async function loadTagsData() {
    console.log('Loading detailed tags data...');
    
    try {
        const token = localStorage.getItem('auth_token');
        
        if (!token) {
            console.error('No auth token found for tags');
            return;
        }
        
        // 获取详细标签分析数据
        const response = await fetch('/api/user/admin/tags/analysis', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Tags analysis data received:', data);
            renderDetailedTagsAnalysis(data.analysis);
        } else {
            console.error('Failed to load tags data:', response.status);
            // 回退到简单统计
            const statsResponse = await fetch('/api/user/admin/statistics', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (statsResponse.ok) {
                const statsData = await statsResponse.json();
                renderTagStats(statsData.statistics.tag_statistics || {});
            }
        }
        
    } catch (error) {
        console.error('Error loading tags data:', error);
        renderTagsError();
    }
}

// 渲染标签统计
function renderTagStats(tagStats) {
    const container = document.getElementById('tagStatsList');
    
    if (Object.keys(tagStats).length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #7f8c8d; font-style: italic;">暂无标签数据</p>';
        return;
    }
    
    container.innerHTML = Object.entries(tagStats)
        .sort(([,a], [,b]) => b - a)
        .map(([dimension, count]) => `
            <div class="tag-stat-item">
                <span class="tag-name">${dimension}</span>
                <span class="tag-count">${count}</span>
            </div>
        `).join('');
}

// 渲染详细标签分析
function renderDetailedTagsAnalysis(analysis) {
    if (!analysis || !analysis.dimensions) {
        renderTagsError();
        return;
    }
    
    // 更新标签统计概览
    const statsContainer = document.getElementById('tagStatsList');
    if (statsContainer) {
        const dimensionStats = Object.entries(analysis.dimensions).map(([name, data]) => ({
            name,
            count: data.total_tags
        }));
        
        statsContainer.innerHTML = dimensionStats.map(stat => `
            <div class="tag-stat-item">
                <span class="tag-name">${stat.name}</span>
                <span class="tag-count">${stat.count}</span>
            </div>
        `).join('');
    }
    
    // 渲染详细的维度分析
    renderDimensionDetails(analysis.dimensions);
    
    // 渲染标签云
    renderTagCloud(analysis.tag_cloud);
    
    // 渲染置信度分布
    renderConfidenceDistribution(analysis.confidence_distribution);
    
    // 渲染用户画像摘要
    renderUserProfilesSummary(analysis.user_profiles);
}

// 渲染维度详情
function renderDimensionDetails(dimensions) {
    const container = document.querySelector('#tags-section .content-area');
    if (!container) return;
    
    // 创建详细分析区域
    let detailsContainer = document.getElementById('dimensionDetails');
    if (!detailsContainer) {
        detailsContainer = document.createElement('div');
        detailsContainer.id = 'dimensionDetails';
        detailsContainer.className = 'dimension-details';
        container.appendChild(detailsContainer);
    }
    
    const dimensionEntries = Object.entries(dimensions);
    
    detailsContainer.innerHTML = `
        <h3>📊 维度详细分析</h3>
        <div class="dimensions-grid">
            ${dimensionEntries.map(([name, data]) => `
                <div class="dimension-card">
                    <div class="dimension-header">
                        <h4>${name}</h4>
                        <div class="dimension-stats">
                            <span class="stat">标签数: ${data.total_tags}</span>
                            <span class="stat">用户数: ${data.users}</span>
                            <span class="stat">平均置信度: ${(data.avg_confidence || 0).toFixed(2)}</span>
                        </div>
                    </div>
                    <div class="dimension-tags">
                        ${data.tags.slice(0, 5).map(tag => `
                            <div class="tag-item">
                                <div class="tag-info">
                                    <span class="tag-name">${tag.name}</span>
                                    <span class="tag-confidence">${tag.confidence.toFixed(2)}</span>
                                </div>
                                <div class="tag-user">用户: ${tag.username}</div>
                                ${tag.evidence ? `<div class="tag-evidence">${tag.evidence}</div>` : ''}
                            </div>
                        `).join('')}
                        ${data.tags.length > 5 ? `<div class="more-tags">还有 ${data.tags.length - 5} 个标签...</div>` : ''}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// 渲染标签云
function renderTagCloud(tagCloud) {
    const container = document.querySelector('#tags-section .content-area');
    if (!container || !tagCloud.length) return;
    
    let cloudContainer = document.getElementById('tagCloud');
    if (!cloudContainer) {
        cloudContainer = document.createElement('div');
        cloudContainer.id = 'tagCloud';
        cloudContainer.className = 'tag-cloud-container';
        container.appendChild(cloudContainer);
    }
    
    cloudContainer.innerHTML = `
        <h3>☁️ 标签云</h3>
        <div class="tag-cloud">
            ${tagCloud.map(tag => `
                <span class="cloud-tag" style="font-size: ${Math.min(24, 12 + tag.count * 2)}px">
                    ${tag.name} (${tag.count})
                </span>
            `).join('')}
        </div>
    `;
}

// 渲染置信度分布
function renderConfidenceDistribution(distribution) {
    const container = document.querySelector('#tags-section .content-area');
    if (!container) return;
    
    let distContainer = document.getElementById('confidenceDistribution');
    if (!distContainer) {
        distContainer = document.createElement('div');
        distContainer.id = 'confidenceDistribution';
        distContainer.className = 'confidence-distribution';
        container.appendChild(distContainer);
    }
    
    const total = Object.values(distribution).reduce((sum, count) => sum + count, 0);
    
    distContainer.innerHTML = `
        <h3>📈 置信度分布</h3>
        <div class="confidence-chart">
            ${Object.entries(distribution).map(([range, count]) => {
                const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;
                return `
                    <div class="confidence-bar">
                        <div class="bar-label">${range}</div>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: ${percentage}%"></div>
                        </div>
                        <div class="bar-value">${count} (${percentage}%)</div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

// 渲染用户画像摘要
function renderUserProfilesSummary(profiles) {
    const container = document.querySelector('#tags-section .content-area');
    if (!container || !Object.keys(profiles).length) return;
    
    let profilesContainer = document.getElementById('userProfilesSummary');
    if (!profilesContainer) {
        profilesContainer = document.createElement('div');
        profilesContainer.id = 'userProfilesSummary';
        profilesContainer.className = 'user-profiles-summary';
        container.appendChild(profilesContainer);
    }
    
    const profileEntries = Object.entries(profiles);
    
    profilesContainer.innerHTML = `
        <h3>👥 用户画像摘要</h3>
        <div class="profiles-grid">
            ${profileEntries.map(([phone, profile]) => `
                <div class="profile-card">
                    <div class="profile-header">
                        <h4>${profile.username}</h4>
                        <span class="profile-phone">${phone}</span>
                        <span class="profile-role ${profile.role}">${profile.role === 'admin' ? '管理员' : '用户'}</span>
                    </div>
                    <div class="profile-stats">
                        <span>标签数: ${profile.total_tags}</span>
                        <span>平均置信度: ${profile.avg_confidence.toFixed(2)}</span>
                    </div>
                    <div class="profile-dimensions">
                        ${Object.entries(profile.tags_by_dimension).map(([dim, tags]) => `
                            <div class="profile-dimension">
                                <strong>${dim}</strong>: ${tags.slice(0, 2).map(tag => tag.name).join(', ')}
                                ${tags.length > 2 ? ` (+${tags.length - 2}个)` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// 渲染标签错误信息
function renderTagsError() {
    const container = document.getElementById('tagStatsList');
    if (container) {
        container.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <span>暂无标签数据或加载失败</span>
            </div>
        `;
    }
}

// 加载分析数据
async function loadAnalyticsData() {
    console.log('Loading analytics data...');
    
    try {
        const token = localStorage.getItem('auth_token');
        
        if (!token) {
            console.error('No auth token found for analytics');
            return;
        }
        
        // 获取用户统计数据
        const statsResponse = await fetch('/api/user/admin/statistics', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            console.log('Analytics data received:', statsData);
            renderAnalyticsCharts(statsData);
        } else {
            console.error('Failed to load analytics data:', statsResponse.status);
        }
        
    } catch (error) {
        console.error('Error loading analytics data:', error);
    }
}

// 渲染分析图表
function renderAnalyticsCharts(data) {
    // 用户增长趋势图（模拟数据）
    renderUserGrowthChart(data);
    
    // 标签使用热度图
    renderTagHeatMap(data);
}

// 渲染用户增长图表
function renderUserGrowthChart(data) {
    const chartContainer = document.querySelector('#userGrowthChart');
    if (!chartContainer) return;
    
    const stats = data.statistics || {};
    
    chartContainer.innerHTML = `
        <div class="chart-placeholder">
            <h4>用户增长趋势</h4>
            <div class="growth-stats">
                <div class="stat-item">
                    <span class="stat-value">${stats.total_users || 0}</span>
                    <span class="stat-label">总用户数</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.active_users || 0}</span>
                    <span class="stat-label">活跃用户</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.new_users_today || 0}</span>
                    <span class="stat-label">今日新增</span>
                </div>
            </div>
        </div>
    `;
}

// 渲染标签热度图
function renderTagHeatMap(data) {
    const chartContainer = document.querySelector('#tagHeatMap');
    if (!chartContainer) return;
    
    const stats = data.statistics || {};
    const avgTags = stats.avg_tags_per_user || 0;
    const roundedAvg = Math.round(avgTags * 10) / 10;
    
    chartContainer.innerHTML = `
        <div class="chart-placeholder">
            <h4>标签使用热度</h4>
            <div class="heatmap-stats">
                <div class="stat-item">
                    <span class="stat-value">${stats.total_tags || 0}</span>
                    <span class="stat-label">总标签数</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${roundedAvg}</span>
                    <span class="stat-label">人均标签</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.most_common_dimension || '暂无数据'}</span>
                    <span class="stat-label">热门维度</span>
                </div>
            </div>
        </div>
    `;
}

// 生成用户增长数据
function generateUserGrowthData(stats) {
    // 这里可以根据实际需求生成更复杂的图表数据
    return {
        labels: ['本周', '上周', '上上周'],
        data: [stats.total_users, Math.max(0, stats.total_users - 1), Math.max(0, stats.total_users - 2)]
    };
}

// 刷新数据
function refreshData() {
    const refreshBtn = document.querySelector('.refresh-btn i');
    refreshBtn.classList.add('fa-spin');
    
    setTimeout(() => {
        refreshBtn.classList.remove('fa-spin');
    }, 1000);
    
    switch(currentSection) {
        case 'overview':
            loadOverviewData();
            break;
        case 'users':
            loadUsersData();
            break;
        case 'tags':
            loadTagsData();
            break;
        case 'analytics':
            loadAnalyticsData();
            break;
    }
}

// 退出登录
async function logout() {
    if (confirm('确定要退出登录吗？')) {
        try {
            // 清除本地存储
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
            
            // 调用后端logout接口清除session
            await fetch('/logout', {
                method: 'GET',
                credentials: 'include'
            });
        } catch (error) {
            console.error('退出登录时发生错误:', error);
        } finally {
            // 无论是否成功都跳转到登录页面
            window.location.href = '/login';
        }
    }
}

// 格式化日期
function formatDate(dateString) {
    if (!dateString) return '未知';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('userDetailModal');
    if (event.target === modal) {
        closeModal();
    }
}
