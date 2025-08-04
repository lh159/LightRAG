/*
 * 前端适配新标签结构的具体代码修改示例
 * 这些代码需要替换到 web/templates/index.html 中的相应位置
 */

// ==================== 1. 更新标签维度定义 ====================

// 新的维度定义（替换所有 allDimensions 定义）
const allDimensions = [
    { 
        key: 'demographic_info', 
        name: '基本人口统计学标签',
        subcategories: {
            'age': '年龄',
            'gender': '性别',
            'location': '地域'
        }
    },
    { 
        key: 'interests_hobbies', 
        name: '兴趣爱好标签',
        subcategories: {
            'entertainment': '娱乐爱好',
            'sports': '运动爱好',
            'learning_career': '学习与职业相关爱好'
        }
    },
    { 
        key: 'emotional_state', 
        name: '情绪与情感状态标签',
        subcategories: {
            'current_mood': '当前情绪状态',
            'emotional_needs': '情感需求'
        }
    }
];

// ==================== 2. 更新用户画像显示函数 ====================

function updateProfile(profile) {
    const profileContent = document.getElementById('profileContent');
    const metricsSection = document.getElementById('metricsSection');
    const profileActions = document.getElementById('profileActions');
    
    if (!profile || Object.keys(profile).length === 0) {
        profileContent.innerHTML = '<p style="color: #666; text-align: center;">还没有生成用户画像，继续对话来建立你的个性化标签</p>';
        metricsSection.style.display = 'none';
        profileActions.style.display = 'none';
        return;
    }
    
    let html = '';
    let hasAnyTags = false;
    
    // 处理新的二级标签结构
    if (profile.tag_dimensions) {
        allDimensions.forEach(dimensionDef => {
            const dimensionData = profile.tag_dimensions[dimensionDef.key];
            
            html += `<div class="profile-dimension">`;
            html += `<h3 class="dimension-title">${dimensionDef.name}</h3>`;
            
            if (dimensionData && dimensionData.subcategories) {
                let dimensionHasAnyTags = false;
                
                // 遍历二级分类
                Object.entries(dimensionDef.subcategories).forEach(([subKey, subName]) => {
                    const subcategoryData = dimensionData.subcategories[subKey];
                    
                    if (subcategoryData && subcategoryData.active_tags && subcategoryData.active_tags.length > 0) {
                        html += `<div class="profile-subcategory">`;
                        html += `<h4 class="subcategory-title">${subName}</h4>`;
                        html += `<div class="profile-tags">`;
                        
                        hasAnyTags = true;
                        dimensionHasAnyTags = true;
                        
                        subcategoryData.active_tags.forEach(tag => {
                            const tagName = tag.tag_name || tag.name;
                            const confidence = tag.avg_confidence || tag.confidence || 0;
                            const isNew = isNewTag(tagName, dimensionDef.key, subKey);
                            const newTagClass = isNew ? ' new-tag' : '';
                            
                            html += `<span class="profile-tag clickable${newTagClass}" 
                                          onclick="showTagTrace('${tagName}')" 
                                          title="点击查看标签溯源"
                                          data-category="${dimensionDef.key}"
                                          data-subcategory="${subKey}">
                                ${tagName} (${(confidence * 100).toFixed(0)}%)
                            </span>`;
                        });
                        
                        html += `</div></div>`;
                    }
                });
                
                // 如果整个维度都没有标签，显示占位符
                if (!dimensionHasAnyTags) {
                    html += `<div class="profile-tags">`;
                    html += `<span class="tag-placeholder" style="color: #999; font-style: italic; background: #f5f5f5; border: 1px dashed #ccc;">暂无标签</span>`;
                    html += `</div>`;
                }
            } else {
                // 兼容旧格式或空数据
                html += `<div class="profile-tags">`;
                html += `<span class="tag-placeholder" style="color: #999; font-style: italic; background: #f5f5f5; border: 1px dashed #ccc;">暂无标签</span>`;
                html += `</div>`;
            }
            
            html += `</div>`;
        });
    } else {
        // 向后兼容旧格式
        html += '<p style="color: #666; text-align: center;">数据格式不兼容，请联系管理员</p>';
    }
    
    profileContent.innerHTML = html;
    
    // 显示或隐藏操作按钮
    if (hasAnyTags) {
        profileActions.style.display = 'block';
        metricsSection.style.display = 'block';
    } else {
        profileActions.style.display = 'none';
        metricsSection.style.display = 'block'; // 仍显示指标，即使是默认值
    }
    
    // 处理综合指标
    if (profile.computed_metrics) {
        const metricsGrid = document.getElementById('metricsGrid');
        metricsGrid.innerHTML = `
            <div class="metric-item">
                <div class="metric-label">情感健康指数</div>
                <div class="metric-value">${(profile.computed_metrics.emotional_health_index * 100).toFixed(0)}%</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">兴趣集中度</div>
                <div class="metric-value">${(profile.computed_metrics.interest_concentration * 100).toFixed(0)}%</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">互动依赖性</div>
                <div class="metric-value">${(profile.computed_metrics.interaction_dependency * 100).toFixed(0)}%</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">画像成熟度</div>
                <div class="metric-value">${(profile.computed_metrics.overall_profile_maturity * 100).toFixed(0)}%</div>
            </div>
        `;
    }
}

// ==================== 3. 更新辅助函数 ====================

// 更新标签新旧判断函数
function isNewTag(tagName, category, subcategory) {
    if (!previousTags[category] || !previousTags[category][subcategory]) {
        return true;
    }
    
    return !previousTags[category][subcategory].some(tag => 
        (tag.name || tag.tag_name) === tagName
    );
}

// 更新历史标签记录函数
function updatePreviousTags(profile) {
    const newPreviousTags = {};
    
    if (profile.tag_dimensions) {
        allDimensions.forEach(dimensionDef => {
            const dimensionData = profile.tag_dimensions[dimensionDef.key];
            
            if (dimensionData && dimensionData.subcategories) {
                newPreviousTags[dimensionDef.key] = {};
                
                Object.entries(dimensionDef.subcategories).forEach(([subKey, subName]) => {
                    const subcategoryData = dimensionData.subcategories[subKey];
                    
                    if (subcategoryData && subcategoryData.active_tags) {
                        newPreviousTags[dimensionDef.key][subKey] = subcategoryData.active_tags.map(tag => ({
                            name: tag.tag_name || tag.name,
                            confidence: tag.avg_confidence || tag.confidence || 0
                        }));
                    } else {
                        newPreviousTags[dimensionDef.key][subKey] = [];
                    }
                });
            }
        });
    }
    
    // 延迟更新previousTags，让新标签显示一段时间后变成历史标签
    setTimeout(() => {
        previousTags = newPreviousTags;
        document.querySelectorAll('.profile-tag.new-tag').forEach(tag => {
            tag.classList.remove('new-tag');
        });
    }, 5000); // 5秒后将新标签变为历史标签
}

// ==================== 4. 更新页面加载逻辑 ====================

// 更新页面加载时的数据处理
window.onload = async function() {
    try {
        // 获取用户画像
        const profileResponse = await fetch('/api/profile');
        const profileData = await profileResponse.json();
        
        // 获取历史对话记录
        const chatResponse = await fetch('/api/chat_history');
        const chatData = await chatResponse.json();
        
        if (profileData.success) {
            // 处理新的二级标签结构
            const dimensions = profileData.user_tags.tag_dimensions;
            const activeDimensions = [];
            
            // 处理新格式的标签数据
            Object.entries(dimensions).forEach(([key, dimension]) => {
                const tags = [];
                
                // 处理二级标签结构
                if (dimension.subcategories) {
                    Object.entries(dimension.subcategories).forEach(([subKey, subcategoryData]) => {
                        if (subcategoryData.active_tags && Array.isArray(subcategoryData.active_tags)) {
                            tags.push(...subcategoryData.active_tags.map(tag => ({
                                name: tag.tag_name || tag.name,
                                tag_name: tag.tag_name || tag.name,
                                confidence: tag.avg_confidence || tag.confidence || 0,
                                weight: tag.current_weight || tag.weight || 0,
                                avg_confidence: tag.avg_confidence || 0,
                                category: tag.category || key,
                                subcategory: tag.subcategory || subKey
                            })));
                        }
                    });
                } else if (dimension.active_tags && Array.isArray(dimension.active_tags)) {
                    // 兼容旧格式
                    tags.push(...dimension.active_tags.map(tag => ({
                        name: tag.tag_name || tag.name,
                        tag_name: tag.tag_name || tag.name,
                        confidence: tag.avg_confidence || tag.confidence || 0,
                        weight: tag.current_weight || tag.weight || 0,
                        avg_confidence: tag.avg_confidence || 0
                    })));
                }
                
                // 添加维度数据
                activeDimensions.push({
                    name: dimension.dimension_name || dimension.name || key,
                    dimension: key,
                    tags: tags
                });
            });
            
            // 构建用户画像对象
            const userProfile = {
                tag_dimensions: dimensions,
                active_dimensions: activeDimensions, // 保持向后兼容
                computed_metrics: profileData.user_tags.computed_metrics || {}
            };
            
            // 更新显示
            updateProfile(userProfile);
            updatePreviousTags(userProfile);
        }
        
        // 处理历史对话
        if (chatData.success && chatData.chat_history) {
            chatData.chat_history.forEach(message => {
                if (message.role === 'user') {
                    addMessage(message.content, 'user');
                } else {
                    addMessage(message.content, 'assistant');
                }
            });
        }
        
    } catch (error) {
        console.error('页面加载错误:', error);
        alert('页面加载失败，请刷新重试');
    }
};

// ==================== 5. 更新标签统计显示 ====================

// 更新标签统计模态窗口显示
function displayTagStatsModal(data) {
    const modal = document.getElementById('tagStatsModal');
    const content = document.getElementById('tagStatsContent');
    
    let html = `
        <div class="stats-overview">
            <h4>📊 总览</h4>
            <p>总标签数: ${data.total_tags} | 类别数: ${data.total_categories}</p>
        </div>
    `;
    
    // 按新的分类显示标签统计
    allDimensions.forEach(dimensionDef => {
        const categoryStats = data.tag_statistics[dimensionDef.key];
        
        if (categoryStats && Object.keys(categoryStats).length > 0) {
            html += `
                <div class="category-stats">
                    <h4>${dimensionDef.name}</h4>
            `;
            
            // 按二级分类显示
            Object.entries(dimensionDef.subcategories).forEach(([subKey, subName]) => {
                const subcategoryStats = categoryStats[subKey];
                
                if (subcategoryStats && subcategoryStats.length > 0) {
                    html += `
                        <div class="subcategory-stats">
                            <h5>${subName}</h5>
                            <div class="tags-stats-grid">
                    `;
                    
                    subcategoryStats.forEach(tag => {
                        html += `
                            <div class="tag-stat-item" onclick="showTagTrace('${tag.tag_name}')">
                                <div class="tag-stat-name">${tag.tag_name}</div>
                                <div class="tag-stat-confidence">${(tag.current_confidence * 100).toFixed(1)}%</div>
                                <div class="tag-stat-triggers">触发: ${tag.total_triggers}次</div>
                            </div>
                        `;
                    });
                    
                    html += `
                            </div>
                        </div>
                    `;
                }
            });
            
            html += `</div>`;
        }
    });
    
    // 显示最近触发
    if (data.recent_triggers && data.recent_triggers.length > 0) {
        html += `
            <div class="recent-triggers">
                <h4>🕒 最近触发</h4>
                <div class="triggers-list">
        `;
        
        data.recent_triggers.forEach(trigger => {
            const date = new Date(trigger.trigger_time).toLocaleString();
            html += `
                <div class="trigger-item">
                    <span class="trigger-tag">${trigger.tag_name}</span>
                    <span class="trigger-time">${date}</span>
                    <span class="trigger-confidence">${(trigger.confidence_after * 100).toFixed(0)}%</span>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    content.innerHTML = html;
    modal.style.display = 'block';
}

// ==================== 6. 获取分类显示名称的辅助函数 ====================

function getCategoryDisplayName(categoryKey) {
    const dimension = allDimensions.find(d => d.key === categoryKey);
    return dimension ? dimension.name : categoryKey;
}

function getSubcategoryDisplayName(categoryKey, subcategoryKey) {
    const dimension = allDimensions.find(d => d.key === categoryKey);
    if (dimension && dimension.subcategories[subcategoryKey]) {
        return dimension.subcategories[subcategoryKey];
    }
    return subcategoryKey;
}