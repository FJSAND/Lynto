// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有功能
    initNavbar();
    initSmoothScroll();
    initAnimations();
    initPhoneMockup();
    initPricingCards();
    loadDynamicMCPServices();
});

// 导航栏功能
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    let lastScrollY = window.scrollY;

    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        
        // 滚动时添加/移除样式
        if (currentScrollY > 50) {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
        } else {
            navbar.style.background = 'rgba(255, 255, 255, 0.9)';
            navbar.style.boxShadow = 'none';
        }

        lastScrollY = currentScrollY;
    });

    // 添加移动端导航菜单
    addMobileMenu();
}

// 添加移动端导航菜单
function addMobileMenu() {
    const navContainer = document.querySelector('.nav-container');
    const navLinks = document.querySelector('.nav-links');
    
    // 创建汉堡菜单按钮
    const menuToggle = document.createElement('button');
    menuToggle.className = 'menu-toggle';
    menuToggle.innerHTML = '☰';
    menuToggle.style.cssText = `
        display: none;
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: var(--text-primary);
    `;

    // 在移动端显示汉堡菜单
    const mediaQuery = window.matchMedia('(max-width: 768px)');
    function handleMobileMenu(e) {
        if (e.matches) {
            menuToggle.style.display = 'block';
            navContainer.appendChild(menuToggle);
            
            // 修改导航链接样式
            navLinks.style.cssText = `
                position: fixed;
                top: 70px;
                left: -100%;
                width: 100%;
                height: calc(100vh - 70px);
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                flex-direction: column;
                justify-content: flex-start;
                padding-top: 50px;
                transition: left 0.3s ease;
                z-index: 1000;
            `;
        } else {
            menuToggle.style.display = 'none';
            navLinks.style.cssText = '';
        }
    }
    
    mediaQuery.addListener(handleMobileMenu);
    handleMobileMenu(mediaQuery);

    // 菜单切换功能
    menuToggle.addEventListener('click', () => {
        const isOpen = navLinks.style.left === '0px';
        navLinks.style.left = isOpen ? '-100%' : '0px';
        menuToggle.innerHTML = isOpen ? '☰' : '✕';
    });

    // 点击链接关闭菜单
    navLinks.addEventListener('click', (e) => {
        if (e.target.tagName === 'A') {
            navLinks.style.left = '-100%';
            menuToggle.innerHTML = '☰';
        }
    });
}

// 平滑滚动
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const offsetTop = targetElement.offsetTop - 80; // 考虑导航栏高度
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// 滚动动画
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // 为需要动画的元素添加初始样式和观察
    const animatedElements = document.querySelectorAll('.feature-card, .service-category, .pricing-card, .highlight-card');
    
    animatedElements.forEach((el, index) => {
        // 设置初始状态
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        
        // 开始观察
        observer.observe(el);
    });

    // 数字计数动画
    initCountAnimation();
}

// 数字计数动画
function initCountAnimation() {
    const countElements = document.querySelectorAll('.amount');
    
    const countObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const target = parseInt(element.textContent);
                
                if (!isNaN(target)) {
                    animateCount(element, 0, target, 1500);
                }
                
                countObserver.unobserve(element);
            }
        });
    });

    countElements.forEach(el => {
        countObserver.observe(el);
    });
}

// 数字计数动画函数
function animateCount(element, start, end, duration) {
    const startTime = Date.now();
    const originalText = element.textContent;
    
    function updateCount() {
        const now = Date.now();
        const progress = Math.min((now - startTime) / duration, 1);
        
        if (isNaN(end)) {
            return;
        }
        
        const current = Math.floor(progress * (end - start) + start);
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(updateCount);
        } else {
            element.textContent = originalText; // 恢复原始文本
        }
    }
    
    updateCount();
}

// 手机样机交互
function initPhoneMockup() {
    const phoneMockup = document.querySelector('.phone-mockup');
    const messages = document.querySelectorAll('.message');
    
    if (phoneMockup) {
        // 鼠标跟随效果
        phoneMockup.addEventListener('mousemove', (e) => {
            const rect = phoneMockup.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            
            const deltaX = (e.clientX - centerX) / 20;
            const deltaY = (e.clientY - centerY) / 20;
            
            phoneMockup.style.transform = `rotate(5deg) translate(${deltaX}px, ${deltaY}px)`;
        });

        phoneMockup.addEventListener('mouseleave', () => {
            phoneMockup.style.transform = 'rotate(5deg)';
        });

        // 点击时的动画效果
        phoneMockup.addEventListener('click', () => {
            phoneMockup.style.transform = 'rotate(0deg) scale(1.1)';
            setTimeout(() => {
                phoneMockup.style.transform = 'rotate(5deg)';
            }, 300);
        });
    }

    // 消息气泡动画
    if (messages.length > 0) {
        messages.forEach((message, index) => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                message.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                message.style.opacity = '1';
                message.style.transform = 'translateY(0)';
            }, index * 800 + 1000);
        });
    }
}

// 定价卡片交互
function initPricingCards() {
    const pricingCards = document.querySelectorAll('.pricing-card');
    
    pricingCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            pricingCards.forEach(otherCard => {
                if (otherCard !== card && !otherCard.classList.contains('featured')) {
                    otherCard.style.opacity = '0.7';
                    otherCard.style.transform = 'translateY(0px) scale(0.95)';
                }
            });
        });

        card.addEventListener('mouseleave', () => {
            pricingCards.forEach(otherCard => {
                otherCard.style.opacity = '1';
                if (otherCard.classList.contains('featured')) {
                    otherCard.style.transform = 'translateY(0px) scale(1.05)';
                } else {
                    otherCard.style.transform = 'translateY(0px) scale(1)';
                }
            });
        });
    });
}

// 页面加载动画
window.addEventListener('load', () => {
    // 英雄区域文字动画
    const heroTitle = document.querySelector('.hero-title');
    const heroSubtitle = document.querySelector('.hero-subtitle');
    const heroButtons = document.querySelector('.hero-buttons');
    
    if (heroTitle) {
        heroTitle.style.opacity = '0';
        heroTitle.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            heroTitle.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
            heroTitle.style.opacity = '1';
            heroTitle.style.transform = 'translateY(0)';
        }, 200);
    }
    
    if (heroSubtitle) {
        heroSubtitle.style.opacity = '0';
        heroSubtitle.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            heroSubtitle.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
            heroSubtitle.style.opacity = '1';
            heroSubtitle.style.transform = 'translateY(0)';
        }, 400);
    }
    
    if (heroButtons) {
        heroButtons.style.opacity = '0';
        heroButtons.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            heroButtons.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
            heroButtons.style.opacity = '1';
            heroButtons.style.transform = 'translateY(0)';
        }, 600);
    }
});

// 工具提示功能
function initTooltips() {
    const buttons = document.querySelectorAll('.btn, .download-btn');
    
    buttons.forEach(button => {
        button.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = button.getAttribute('data-tooltip') || '点击了解更多';
            tooltip.style.cssText = `
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                white-space: nowrap;
                z-index: 1000;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s ease;
            `;
            
            button.style.position = 'relative';
            button.appendChild(tooltip);
            
            setTimeout(() => {
                tooltip.style.opacity = '1';
            }, 100);
        });

        button.addEventListener('mouseleave', () => {
            const tooltip = button.querySelector('.tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
    });
}

// 性能优化：节流函数
function throttle(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 应用节流到滚动事件
window.addEventListener('scroll', throttle(() => {
    // 这里可以添加需要在滚动时执行的代码
}, 16)); // 大约60fps

// 添加键盘导航支持
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        // 关闭移动端菜单
        const navLinks = document.querySelector('.nav-links');
        const menuToggle = document.querySelector('.menu-toggle');
        if (navLinks && menuToggle) {
            navLinks.style.left = '-100%';
            menuToggle.innerHTML = '☰';
        }
    }
});

// 错误处理
window.addEventListener('error', (e) => {
    console.warn('网站脚本出现错误:', e.error);
});

// 动态MCP服务加载
function loadDynamicMCPServices() {
    try {
        console.log('开始加载静态MCP服务...');
        const config = getStaticMCPConfig();
        
        console.log('获取到的配置:', config);
        
        if (config && config.data) {
            console.log('配置数据有效，开始渲染服务...');
            
            // 渲染免费服务
            if (config.data.freeMCP && config.data.freeMCP.length > 0) {
                console.log(`找到 ${config.data.freeMCP.length} 个免费服务`);
                renderFreeServices(config.data.freeMCP);
            } else {
                console.log('没有找到免费服务或freeMCP为空');
                const freeContainer = document.getElementById('free-mcp-grid');
                if (freeContainer) {
                    freeContainer.innerHTML = '<div class="loading-placeholder"><p>暂无免费服务</p></div>';
                }
            }
            
            // 渲染推荐服务
            if (config.data.recMCP && config.data.recMCP.length > 0) {
                console.log(`找到 ${config.data.recMCP.length} 个推荐服务`);
                renderRecommendedServices(config.data.recMCP);
            } else {
                console.log('没有找到推荐服务或recMCP为空');
                const recContainer = document.getElementById('recommended-mcp-grid');
                if (recContainer) {
                    recContainer.innerHTML = '<div class="loading-placeholder"><p>暂无推荐服务</p></div>';
                }
            }
        } else {
            console.log('配置数据无效:', config);
            showError('配置数据格式错误');
        }
    } catch (error) {
        console.error('加载MCP服务失败:', error);
        showError(`加载MCP服务失败: ${error.message}`);
    }
}

// 静态MCP配置数据
function getStaticMCPConfig() {
    return {
        "header": {
            "vs": "20250711"
        },
        "data": {
            "active": {
                "showFree": 1
            },
            "freeMCP": [
                {
                    "id": "12306mcp",
                    "name": "12306",
                    "description": "基于 Model Context Protocol (MCP) 的12306购票搜索服务器。提供了简单的API接口，允许大模型利用接口搜索12306购票信息。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-0jhxupcs/sse"
                },
                {
                    "id": "edgeonemcp",
                    "name": "网页生成",
                    "description": "一个用于将 HTML 内容部署到 EdgeOne Pages 并获取公开可访问 URL的MCP服务。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-gei7ht3o/sse"
                },
                {
                    "id": "bazimcp",
                    "name": "八字",
                    "description": "根据给定的公历或农历时间计算八字信息。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-lg33cw5y/sse"
                },
                {
                    "id": "hotnewsmcp",
                    "name": "新闻热点",
                    "description": "一个提供来自中国主要社交平台和新闻网站实时热点话题的模型上下文协议（MCP）服务器。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-fuqm3orc/sse"
                },
                {
                    "id": "trendsmcp",
                    "name": "趋势热点",
                    "description": "全网热点趋势一站式聚合服务。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-dcs4m502/sse"
                },
                {
                    "id": "playwrightmcp",
                    "name": "PlayWright",
                    "description": "一个使用 Playwright 提供浏览器自动化功能的 Model Context Protocol (MCP) 服务器。该服务器使 LLM 能够通过结构化的无障碍快照与网页进行交互，从而绕过了对屏幕截图或视觉调优模型的需求。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-9lat94ae/sse"
                },
                {
                    "id": "variflightmcp",
                    "name": "飞常准",
                    "description": "飞常准MCP服务系统是基于模型上下文协议（MCP）的航空信息服务端实现，为航班信息查询、气象数据获取及飞行舒适度分析提供多维度数据聚合与语义化查询接口。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-7c92iw0g/sse"
                },
                {
                    "id": "chartmcp",
                    "name": "可视化图表",
                    "description": "这是一个基于 TypeScript 的 MCP 服务器，提供了图表生成功能。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-gej8y2qc/sse"
                },
                {
                    "id": "bingcn",
                    "name": "必应搜索",
                    "description": "一个基于 MCP (Model Context Protocol) 的中文必应搜索工具，可以直接通过AI来搜索必应并获取网页内容。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-ch623k4y/sse"
                },
                {
                    "id": "juhefree",
                    "name": "聚合数据",
                    "description": "包括今日新闻、足球赛事、NBA赛事等。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-5v6tocgo/sse"
                },
                {
                    "id": "sequentialthinking",
                    "name": "序列思考",
                    "description": "一种MCP服务器，它提供了一种工具，可以通过结构化的思维过程动态地、反思性地解决问题。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-pes6ba60/sse"
                },
                {
                    "id": "amapfree",
                    "name": "高德地图",
                    "description": "地图搜索、路线规划、地理编码等服务。",
                    "category": "限时免费",
                    "endpoint": "http://lynto.com.cn/lhms-7qteh0d0/sse"
                }
            ],
            "recMCP": [
                {
                    "id": "gezhe",
                    "name": "歌者PPT",
                    "description": "专业PPT制作与文档处理，智能演示文稿生成服务",
                    "category": "办公服务",
                    "endpoint": "https://mcp.gezhe.com/mcp?API_KEY="
                },
                {
                    "id": "amap",
                    "name": "高德地图",
                    "description": "地图搜索、路线规划、地理编码等服务",
                    "category": "位置服务",
                    "endpoint": "https://mcp.amap.com/sse?key="
                },
                {
                    "id": "tencentmap",
                    "name": "腾讯位置",
                    "description": "地理编码、地点搜索、路线规划等服务",
                    "category": "位置服务",
                    "endpoint": "https://mcp.map.qq.com/mcp?key="
                },
                {
                    "id": "juhe",
                    "name": "聚合数据",
                    "description": "天气查询、足篮球、手机号归属地等服务",
                    "category": "生活服务",
                    "endpoint": "https://mcp.juhe.cn/sse?token="
                },
                {
                    "id": "stockmcp",
                    "name": "证券服务",
                    "description": "专业证券股票分析、市场行情等金融服务",
                    "category": "金融服务",
                    "endpoint": "http://175.24.203.120:9035/v1/mcp/stream?token="
                },
                {
                    "id": "yingmi",
                    "name": "盈米且慢",
                    "description": "提供基金、内容、投研、投顾等专业领域能力",
                    "category": "金融服务",
                    "endpoint": "https://stargate.yingmi.com/mcp/sse?apiKey="
                },
                {
                    "id": "custom",
                    "name": "自定义远程",
                    "description": "添加您自己的远程 MCP 服务",
                    "category": "自定义",
                    "endpoint": ""
                }
            ]
        }
    };
}

// 渲染免费服务
function renderFreeServices(freeServices) {
    console.log('开始渲染免费服务:', freeServices);
    const container = document.getElementById('free-mcp-grid');
    if (!container) {
        console.error('找不到免费服务容器 #free-mcp-grid');
        return;
    }
    
    console.log('找到免费服务容器，开始渲染...');
    
    // 清空加载占位符
    container.innerHTML = '';
    
    freeServices.forEach((service, index) => {
        console.log(`渲染第 ${index + 1} 个免费服务:`, service.name);
        const serviceCard = createServiceCard(service, 'free');
        container.appendChild(serviceCard);
    });
    
    console.log(`成功渲染了 ${freeServices.length} 个免费服务`);
}

// 渲染推荐服务
function renderRecommendedServices(recommendedServices) {
    console.log('开始渲染推荐服务:', recommendedServices);
    const container = document.getElementById('recommended-mcp-grid');
    if (!container) {
        console.error('找不到推荐服务容器 #recommended-mcp-grid');
        return;
    }
    
    console.log('找到推荐服务容器，开始渲染...');
    
    // 清空加载占位符
    container.innerHTML = '';
    
    recommendedServices.forEach((service, index) => {
        console.log(`渲染第 ${index + 1} 个推荐服务:`, service.name);
        const serviceCard = createServiceCard(service, 'recommended');
        container.appendChild(serviceCard);
    });
    
    console.log(`成功渲染了 ${recommendedServices.length} 个推荐服务`);
}

// 创建服务卡片
function createServiceCard(service, type) {
    const card = document.createElement('div');
    card.className = 'mcp-service-card';
    
    // 根据服务类型确定样式
    const badgeClass = type === 'free' ? 'free-service-badge' : 'recommended-service-badge';
    
    card.innerHTML = `
        <div class="mcp-service-header">
            <h4 class="mcp-service-name">${service.name}</h4>
            <span class="mcp-service-category ${badgeClass}">${service.category}</span>
        </div>
        <p class="mcp-service-description">${service.description}</p>
    `;
    
    // 添加点击效果
    card.addEventListener('click', () => {
        // 可以在这里添加点击服务卡片的处理逻辑
        console.log('点击了服务:', service.name);
        
        // 简单的视觉反馈
        card.style.transform = 'translateY(-12px) scale(1.02)';
        setTimeout(() => {
            card.style.transform = 'translateY(-8px)';
        }, 150);
    });
    
    return card;
}

// 显示错误信息
function showError(message) {
    const freeContainer = document.getElementById('free-mcp-grid');
    const recommendedContainer = document.getElementById('recommended-mcp-grid');
    
    const errorHTML = `
        <div class="error-message">
            <h4>❌ 加载失败</h4>
            <p>${message}</p>
            <button onclick="loadDynamicMCPServices()" style="
                margin-top: 10px;
                padding: 8px 16px;
                background: var(--gradient-primary);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 500;
            ">重新尝试</button>
        </div>
    `;
    
    if (freeContainer) {
        freeContainer.innerHTML = errorHTML;
    }
    if (recommendedContainer) {
        recommendedContainer.innerHTML = errorHTML;
    }
}

// 导出函数供其他脚本使用
window.MCPWebsite = {
    initNavbar,
    initSmoothScroll,
    initAnimations,
    throttle,
    loadDynamicMCPServices
}; 