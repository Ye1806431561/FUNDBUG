/**
 * FUNDBUG Frontend Application
 * 
 * 负责与后端 API 交互，管理关注列表，实时更新净值估算。
 */

const API_BASE = '/api';
const REFRESH_INTERVAL = 60 * 1000; // 60秒刷新
let autoRefreshTimer = null;
let isConfirming = false; // 标记是否正在显示确认框

// DOM Elements
const addFundForm = document.getElementById('add-fund-form');
const fundCodeInput = document.getElementById('fund-code-input');
const watchlistContainer = document.getElementById('watchlist-container');
const errorMessageDiv = document.getElementById('error-message');
const lastUpdateSpan = document.getElementById('last-update');

/**
 * 初始化应用
 */
async function init() {
    setupEventListeners();
    setupGlobalDelegation();
    setupModalListeners();
    await loadWatchlist();
    startAutoRefresh();
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    addFundForm.addEventListener('submit', handleAddFund);
}

/**
 * 启动自动刷新
 */
function startAutoRefresh() {
    // 立即执行一次估算获取
    refreshEstimates();

    if (autoRefreshTimer) clearInterval(autoRefreshTimer);
    autoRefreshTimer = setInterval(() => {
        refreshEstimates();
    }, REFRESH_INTERVAL);
}

/**
 * 加载关注列表（全量刷新）
 * 1. 获取关注列表
 * 2. 渲染基础卡片结构
 * 3. 获取估算数据填充
 */
async function loadWatchlist() {
    console.log(`Fetching watchlist from: ${API_BASE}/watchlist`);
    try {
        const response = await fetch(`${API_BASE}/watchlist`);
        if (!response.ok) {
            throw new Error(`无法加载关注列表 (Status: ${response.status})`);
        }

        const watchlist = await response.json();
        renderWatchlist(watchlist);

        // 列表加载完后，立即获取一次估算数据
        await refreshEstimates();

    } catch (error) {
        console.error("Load watchlist failed:", error);
        showError(error.message);
        watchlistContainer.innerHTML = `<div class="status-bar" style="text-align:center; color: #ef4444;">加载失败: ${error.message}<br>请检查后端服务是否运行</div>`;
    }
}

/**
 * 刷新估算数据（不重绘整个列表）
 */
async function refreshEstimates() {
    if (isConfirming) return; // 如果正在弹窗，暂停刷新以免干扰 UI

    try {
        updateStatusTime('更新中...');
        const response = await fetch(`${API_BASE}/estimates`);
        if (!response.ok) throw new Error('无法获取估算数据');

        const estimates = await response.json();
        updateFundCards(estimates);
        updateStatusTime(new Date().toLocaleTimeString());

    } catch (error) {
        console.error('刷新估算失败:', error);
        // 不打断用户体验，仅在控制台报错，或在状态栏显示
        updateStatusTime('更新失败');
    }
}

/**
 * 渲染关注列表卡片
 */
function renderWatchlist(watchlist) {
    if (!watchlist || watchlist.length === 0) {
        watchlistContainer.innerHTML = `
            <div class="empty-state">
                <p>暂无关注基金，请在上方添加。</p>
            </div>
        `;
        return;
    }

    watchlistContainer.innerHTML = watchlist.map(item => createFundCardHTML(item)).join('');
}

/**
 * 设置全局事件委托
 */
function setupGlobalDelegation() {
    watchlistContainer.addEventListener('click', (e) => {
        const deleteBtn = e.target.closest('.delete-btn');
        if (deleteBtn) {
            e.preventDefault();
            e.stopPropagation();
            const fundCode = deleteBtn.dataset.code;
            handleRemoveFund(fundCode);
        }
    });
}

/**
 * 生成单个基金卡片的 HTML
 */
function createFundCardHTML(item) {
    return `
        <div class="fund-card" id="card-${item.fund_code}">
            <div class="fund-header">
                <div>
                    <div class="fund-name" id="name-${item.fund_code}">${item.fund_name || '加载中...'}</div>
                    <div class="fund-code">${item.fund_code}</div>
                </div>
                <button class="delete-btn" data-code="${item.fund_code}" title="移除关注">×</button>
            </div>
            
            <div class="fund-body">
                <div class="metric-row">
                    <div class="metric">
                        <div class="label">预估净值</div>
                        <div class="value" id="nav-${item.fund_code}">--</div>
                    </div>
                    <div class="metric">
                        <div class="label">预估涨跌</div>
                        <div class="value" id="return-${item.fund_code}">--</div>
                    </div>
                </div>
                
                <div class="correction-info" id="correction-${item.fund_code}" style="display: none;">
                    <span class="badge">EWA修正</span> 偏差: <span id="bias-${item.fund_code}">0.00%</span>
                </div>
                
                <div class="meta-row">
                    <span>持仓: <span id="holdings-${item.fund_code}">-</span>只</span>
                    <span>现金: <span id="cash-${item.fund_code}">-%</span></span>
                    <span>更新: <span id="time-${item.fund_code}">--:--</span></span>
                </div>
            </div>
        </div>
    `;
}

/**
 * 更新基金卡片数据
 */
function updateFundCards(estimates) {
    estimates.forEach(est => {
        const card = document.getElementById(`card-${est.fund_code}`);
        if (!card) return; // 列表可能已变动

        // 更新名称（如果之前是加载中）
        if (est.fund_name) {
            const nameEl = document.getElementById(`name-${est.fund_code}`);
            if (nameEl) nameEl.textContent = est.fund_name;
        }

        // 决定显示原始值还是修正值
        const displayNav = est.is_corrected ? est.corrected_nav : est.estimated_nav;
        const displayReturn = est.is_corrected ? est.corrected_return : est.estimated_return;

        // 更新净值和涨跌幅
        updateValueWithColor(`nav-${est.fund_code}`, displayNav.toFixed(4), displayReturn);
        updateValueWithColor(`return-${est.fund_code}`, formatPercentage(displayReturn), displayReturn);

        // 更新 EWA 修正提示
        const correctionEl = document.getElementById(`correction-${est.fund_code}`);
        if (est.is_corrected && correctionEl) {
            correctionEl.style.display = 'block';
            document.getElementById(`bias-${est.fund_code}`).textContent = est.ewa_bias.toFixed(2) + '%';
            // 根据偏差正负给予颜色提示？暂不需要，保持简约
        } else if (correctionEl) {
            correctionEl.style.display = 'none';
        }

        // 更新元数据
        setText(`holdings-${est.fund_code}`, est.holdings_count);
        setText(`cash-${est.fund_code}`, est.cash_ratio.toFixed(1) + '%');

        // 格式化时间 (仅显示 HH:MM:SS)
        const timeStr = est.estimate_time ? est.estimate_time.split(' ')[1] : '--:--';
        setText(`time-${est.fund_code}`, timeStr);
    });
}

/**
 * 处理添加基金
 */
async function handleAddFund(e) {
    e.preventDefault();
    const fundCode = fundCodeInput.value.trim();
    if (!fundCode) return;

    // UI Loading State
    const submitBtn = addFundForm.querySelector('button');
    const originalBtnText = submitBtn.textContent;
    submitBtn.textContent = '添加中...';
    submitBtn.disabled = true;
    hideError();

    try {
        console.log(`Adding fund ${fundCode} to: ${API_BASE}/watchlist`);
        const response = await fetch(`${API_BASE}/watchlist`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fund_code: fundCode })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.detail || `Server Error: ${response.status}`;
            throw new Error(errorMsg);
        }

        // 成功后的处理
        fundCodeInput.value = '';
        await loadWatchlist(); // 重新加载列表（包含新基金）

    } catch (error) {
        console.error("Add fund failed:", error);
        let msg = error.message;
        if (msg.includes("Failed to fetch")) {
            msg = "无法连接到服务器，请确认后台服务已启动 (python main.py)";
        }
        showError(msg);
    } finally {
        submitBtn.textContent = originalBtnText;
        submitBtn.disabled = false;
    }
}

/**
 * 处理移除基金
 */
// Modal Elements
const confirmModal = document.getElementById('confirm-modal');
const modalFundCodeSpan = document.getElementById('modal-fund-code');
const modalCancelBtn = document.getElementById('modal-cancel');
const modalConfirmBtn = document.getElementById('modal-confirm');

let fundToDelete = null;

function setupModalListeners() {
    modalCancelBtn.addEventListener('click', hideModal);
    modalConfirmBtn.addEventListener('click', executeDelete);

    // 点击遮罩层关闭
    confirmModal.addEventListener('click', (e) => {
        if (e.target === confirmModal) hideModal();
    });
}

function showModal(fundCode) {
    fundToDelete = fundCode;
    modalFundCodeSpan.textContent = fundCode;
    confirmModal.style.display = 'flex';
    isConfirming = true; // 暂停自动刷新
}

function hideModal() {
    confirmModal.style.display = 'none';
    fundToDelete = null;
    isConfirming = false; // 恢复自动刷新
}

async function executeDelete() {
    if (!fundToDelete) return;

    const fundCode = fundToDelete;
    const btn = modalConfirmBtn;

    try {
        btn.textContent = "删除中...";
        btn.disabled = true;

        // 乐观更新 UI：先移除 DOM
        const card = document.getElementById(`card-${fundCode}`);
        if (card) {
            card.style.opacity = '0.5';
            card.style.pointerEvents = 'none';
        }

        const response = await fetch(`${API_BASE}/watchlist/${fundCode}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('移除失败');

        // 彻底移除 DOM
        if (card) card.remove();

        // 如果列表空了，显示空状态
        if (watchlistContainer.children.length === 0) {
            loadWatchlist();
        }

        hideModal();

    } catch (error) {
        showError(`移除失败: ${error.message}`);
        // 恢复 UI
        const card = document.getElementById(`card-${fundCode}`);
        if (card) {
            card.style.opacity = '1';
            card.style.pointerEvents = 'auto';
        }
        hideModal();
    } finally {
        btn.textContent = "删除";
        btn.disabled = false;
    }
}

/**
 * 处理移除基金 (Trigger Modal)
 */
function handleRemoveFund(fundCode) {
    showModal(fundCode);
}

// --- Helpers ---

function updateValueWithColor(elementId, text, valueForColor) {
    const el = document.getElementById(elementId);
    if (!el) return;

    el.textContent = text;

    // 移除旧的一类
    el.classList.remove('up', 'down', 'flat');

    if (valueForColor > 0) {
        el.classList.add('up');
    } else if (valueForColor < 0) {
        el.classList.add('down');
    } else {
        el.classList.add('flat');
    }
}

function formatPercentage(val) {
    const sign = val > 0 ? '+' : '';
    return `${sign}${val.toFixed(2)}%`;
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function showError(msg) {
    errorMessageDiv.textContent = msg;
    errorMessageDiv.style.display = 'block';
    setTimeout(() => {
        errorMessageDiv.style.display = 'none';
    }, 5000);
}

function hideError() {
    errorMessageDiv.style.display = 'none';
}

function updateStatusTime(text) {
    if (lastUpdateSpan) lastUpdateSpan.textContent = text;
}

// Start
init();
