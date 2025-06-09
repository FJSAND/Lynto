// 网站交互功能
document.addEventListener('DOMContentLoaded', function() {
    // 导航栏滚动效果
    const header = document.querySelector('.header');
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    // 监听滚动事件
    window.addEventListener('scroll', function() {
        if (window.scrollY > 100) {
            header.style.background = 'rgba(255, 255, 255, 0.98)';
            header.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)';
        } else {
            header.style.background = 'rgba(255, 255, 255, 0.95)';
            header.style.boxShadow = 'none';
        }
    });
    
    // 移动端菜单切换
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
            
            // 动画效果
            const spans = navToggle.querySelectorAll('span');
            spans.forEach((span, index) => {
                if (navToggle.classList.contains('active')) {
                    if (index === 0) span.style.transform = 'rotate(45deg) translate(5px, 5px)';
                    if (index === 1) span.style.opacity = '0';
                    if (index === 2) span.style.transform = 'rotate(-45deg) translate(7px, -6px)';
                } else {
                    span.style.transform = 'none';
                    span.style.opacity = '1';
                }
            });
        });
    }
    
    // 平滑滚动到锚点
    const smoothScrollLinks = document.querySelectorAll('a[href^="#"]');
    smoothScrollLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const headerHeight = header.offsetHeight;
                const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
                
                // 关闭移动端菜单
                if (navMenu.classList.contains('active')) {
                    navMenu.classList.remove('active');
                    navToggle.classList.remove('active');
                }
            }
        });
    });
    
    // 滚动显示动画
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease-out forwards';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // 观察需要动画的元素
    const animateElements = document.querySelectorAll('.feature-card, .tech-item, .doc-card, .stat');
    animateElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        observer.observe(el);
    });
    
    // 打字机效果（可选）
    function typeWriter(element, text, speed = 100) {
        if (!element) return;
        
        let i = 0;
        element.innerHTML = '';
        
        function type() {
            if (i < text.length) {
                element.innerHTML += text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        }
        
        type();
    }
    
    // 聊天预览动画
    const chatMessages = document.querySelectorAll('.chat-message');
    if (chatMessages.length > 0) {
        chatMessages.forEach((message, index) => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(10px)';
            
            setTimeout(() => {
                message.style.transition = 'all 0.3s ease-out';
                message.style.opacity = '1';
                message.style.transform = 'translateY(0)';
            }, index * 800 + 1000);
        });
    }
    
    // 统计数字动画
    function animateCounter(element, target, duration = 2000) {
        if (!element) return;
        
        let start = 0;
        const increment = target / (duration / 16);
        
        function updateCounter() {
            start += increment;
            if (start < target) {
                element.textContent = Math.ceil(start);
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = target;
            }
        }
        
        updateCounter();
    }
    
    // 复制到剪贴板功能
    function copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('已复制到剪贴板');
            });
        } else {
            // 兼容性处理
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showToast('已复制到剪贴板');
        }
    }
    
    // 显示提示消息
    function showToast(message, duration = 3000) {
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--gray-800);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            font-size: 14px;
            font-weight: 500;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease-out;
        `;
        
        document.body.appendChild(toast);
        
        // 显示动画
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // 隐藏动画
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, duration);
    }
    
    // 复制代码功能
    const codeBlocks = document.querySelectorAll('.code-content pre');
    codeBlocks.forEach(block => {
        const copyButton = document.createElement('button');
        copyButton.textContent = '复制';
        copyButton.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s;
        `;
        
        const container = block.closest('.code-preview');
        if (container) {
            container.style.position = 'relative';
            container.appendChild(copyButton);
            
            container.addEventListener('mouseenter', () => {
                copyButton.style.opacity = '1';
            });
            
            container.addEventListener('mouseleave', () => {
                copyButton.style.opacity = '0';
            });
            
            copyButton.addEventListener('click', () => {
                copyToClipboard(block.textContent);
                copyButton.textContent = '已复制!';
                setTimeout(() => {
                    copyButton.textContent = '复制';
                }, 2000);
            });
        }
    });
    
    // 表单验证（如果有的话）
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            
            // 这里可以添加表单提交逻辑
            console.log('表单数据:', data);
            showToast('表单提交成功！');
        });
    });
    
    // 键盘导航支持
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // 关闭移动端菜单
            if (navMenu && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            }
        }
    });
    
    // 外部链接处理
    const externalLinks = document.querySelectorAll('a[href^="http"]');
    externalLinks.forEach(link => {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    });
    
    // 图片懒加载
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
    
    // 性能监控（开发环境）
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('页面加载时间:', performance.now(), 'ms');
        
        window.addEventListener('load', () => {
            console.log('页面完全加载时间:', performance.now(), 'ms');
        });
    }
    
    // 主题切换（预留功能）
    function toggleTheme() {
        const body = document.body;
        const isDark = body.classList.contains('dark-theme');
        
        if (isDark) {
            body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
        } else {
            body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        }
    }
    
    // 应用保存的主题
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
    
    // 搜索功能（预留）
    function initSearch() {
        const searchInput = document.querySelector('.search-input');
        const searchResults = document.querySelector('.search-results');
        
        if (searchInput && searchResults) {
            let searchTimeout;
            
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                const query = this.value.trim();
                
                if (query.length < 2) {
                    searchResults.style.display = 'none';
                    return;
                }
                
                searchTimeout = setTimeout(() => {
                    performSearch(query);
                }, 300);
            });
        }
    }
    
    function performSearch(query) {
        // 搜索逻辑
        console.log('搜索:', query);
    }
    
    // 初始化搜索
    initSearch();
    
    // 页面可见性变化处理
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            document.title = '👋 回来看看吧 - 灵拓 Lynto';
        } else {
            document.title = '灵拓 Lynto - 智能聊天应用';
        }
    });
    
    console.log('灵拓 Lynto 网站已加载完成 🚀');
});

// 工具函数
const utils = {
    // 节流函数
    throttle(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // 防抖函数
    debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    },
    
    // 格式化数字
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },
    
    // 获取设备类型
    getDeviceType() {
        const width = window.innerWidth;
        if (width < 768) return 'mobile';
        if (width < 1024) return 'tablet';
        return 'desktop';
    },
    
    // 检测浏览器
    getBrowser() {
        const userAgent = navigator.userAgent;
        if (userAgent.includes('Chrome')) return 'Chrome';
        if (userAgent.includes('Firefox')) return 'Firefox';
        if (userAgent.includes('Safari')) return 'Safari';
        if (userAgent.includes('Edge')) return 'Edge';
        return 'Unknown';
    }
};

// 导出工具函数（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = utils;
} 