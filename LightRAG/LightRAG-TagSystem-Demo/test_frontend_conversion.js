// 测试前端数据转换逻辑
console.log("🧪 测试前端数据转换逻辑...");

// 模拟后端返回的数据结构
const mockBackendData = {
  "user_tags": {
    "tag_dimensions": {
      "interests_hobbies": {
        "dimension_name": "兴趣爱好标签",
        "subcategories": {
          "knowledge_learning": {
            "subcategory_name": "知识学习类",
            "active_tags": [
              {
                "tag_name": "魔法药水制作",
                "avg_confidence": 0.8,
                "category": "interests_hobbies",
                "subcategory": "knowledge_learning"
              }
            ]
          }
        }
      },
      "emotional_state": {
        "dimension_name": "情绪与情感状态标签",
        "subcategories": {
          "current_mood": {
            "subcategory_name": "当前情绪状态",
            "active_tags": [
              {
                "tag_name": "兴奋",
                "avg_confidence": 0.7,
                "category": "emotional_state",
                "subcategory": "current_mood"
              }
            ]
          }
        }
      }
    }
  }
};

// 模拟前端的转换逻辑
function convertBackendToFrontend(profileData) {
  if (!profileData.success) {
    return {
      active_dimensions: [],
      emotional_health_index: 0.5,
      profile_maturity: 0.0
    };
  }

  const dimensions = profileData.user_tags.tag_dimensions;
  const activeDimensions = [];
  
  // 处理新的二级标签结构
  Object.entries(dimensions).forEach(([key, dimension]) => {
    const tags = [];
    
    // 处理新的二级标签结构
    if (dimension.subcategories) {
      // 遍历所有二级分类
      Object.entries(dimension.subcategories).forEach(([subKey, subcategoryData]) => {
        if (subcategoryData.active_tags && Array.isArray(subcategoryData.active_tags)) {
          tags.push(...subcategoryData.active_tags.map(tag => ({
            name: tag.tag_name || tag.name,
            tag_name: tag.tag_name || tag.name,
            confidence: tag.avg_confidence || tag.confidence || 0,
            weight: tag.current_weight || tag.weight || 0,
            avg_confidence: tag.avg_confidence || 0,
            category: tag.category || key,
            subcategory: tag.subcategory || subKey,
            subcategory_name: subcategoryData.subcategory_name || subKey
          })));
        }
      });
    }
    
    // 总是添加维度，即使没有标签
    activeDimensions.push({
      name: dimension.dimension_name || dimension.name || key,
      dimension: key,
      tags: tags,
      subcategories: dimension.subcategories || null
    });
  });
  
  return {
    active_dimensions: activeDimensions,
    emotional_health_index: profileData.user_tags.emotional_health_index || 
                           profileData.user_tags.computed_metrics?.emotional_health_index || 0.5,
    profile_maturity: profileData.user_tags.profile_maturity || 
                     profileData.user_tags.computed_metrics?.overall_profile_maturity || 0.0
  };
}

// 测试转换
console.log("\n📥 后端数据:");
console.log(JSON.stringify(mockBackendData, null, 2));

const convertedData = convertBackendToFrontend({
  success: true,
  user_tags: mockBackendData.user_tags
});

console.log("\n📤 转换后的前端数据:");
console.log(JSON.stringify(convertedData, null, 2));

// 验证转换结果
console.log("\n🔍 验证转换结果:");
convertedData.active_dimensions.forEach(dim => {
  console.log(`\n📂 维度: ${dim.name} (${dim.dimension})`);
  console.log(`   标签数量: ${dim.tags.length}`);
  if (dim.tags.length > 0) {
    dim.tags.forEach(tag => {
      console.log(`   • ${tag.name} (置信度: ${tag.confidence})`);
      console.log(`     子分类: ${tag.subcategory} (${tag.subcategory_name})`);
    });
  } else {
    console.log("   ℹ️  无标签");
  }
});

// 检查是否有魔药相关标签
const magicTags = convertedData.active_dimensions
  .flatMap(dim => dim.tags)
  .filter(tag => tag.name.includes('魔药') || tag.name.includes('魔法'));

console.log(`\n🎯 魔药相关标签: ${magicTags.length} 个`);
magicTags.forEach(tag => {
  console.log(`   • ${tag.name} (置信度: ${tag.confidence})`);
});
