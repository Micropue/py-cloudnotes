#!/bin/bash
# ============================================================
#  云笔记系统 - 需求问答脚本
#  通过交互式问答，逐项明确项目需求
# ============================================================

set -e

RESULT_FILE="./需求问答结果.txt"
> "$RESULT_FILE"

# --------------- 颜色 ---------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --------------- 辅助函数 ---------------
print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}============================================================${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}============================================================${NC}"
    echo ""
}

ask_select() {
    # $1: 提示文字, $2: 变量名, $3+: 选项 (用 | 分隔的字符串)
    local prompt="$1"
    local varname="$2"
    shift 2
    local options=("$@")

    echo -e "${YELLOW}${BOLD}▶ ${prompt}${NC}"
    for i in "${!options[@]}"; do
        echo -e "  ${GREEN}[$((i+1))]${NC} ${options[$i]}"
    done
    echo -e "  ${GREEN}[0]${NC} 自定义输入"

    while true; do
        read -r -p "$(echo -e ${BOLD}"请输入选项编号 (0-${#options[@]}): "${NC})" choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 0 ] && [ "$choice" -le "${#options[@]}" ]; then
            if [ "$choice" -eq 0 ]; then
                read -r -p "$(echo -e ${BOLD}"请输入自定义内容: "${NC})" custom
                export "$varname"="$custom"
            else
                export "$varname"="${options[$((choice-1))]}"
            fi
            break
        else
            echo -e "${RED}无效输入，请重新选择${NC}"
        fi
    done
    echo -e "${GREEN}  ✓ 已选择: ${!varname}${NC}"
    echo "[$varname] ${!varname}" >> "$RESULT_FILE"
    echo ""
}

ask_open() {
    # $1: 提示文字, $2: 变量名
    local prompt="$1"
    local varname="$2"

    echo -e "${YELLOW}${BOLD}▶ ${prompt}${NC}"
    read -r -p "$(echo -e ${BOLD}"请输入: "${NC})" answer
    export "$varname"="$answer"
    echo -e "${GREEN}  ✓ 已输入: ${!varname}${NC}"
    echo "[$varname] ${!varname}" >> "$RESULT_FILE"
    echo ""
}

ask_yesno() {
    # $1: 提示文字, $2: 变量名
    local prompt="$1"
    local varname="$2"

    echo -e "${YELLOW}${BOLD}▶ ${prompt}${NC}"
    echo -e "  ${GREEN}[Y]${NC} 是"
    echo -e "  ${GREEN}[N]${NC} 否"

    while true; do
        read -r -p "$(echo -e ${BOLD}"请输入 (Y/N): "${NC})" choice
        case "$choice" in
            [Yy]|[Yy][Ee][Ss]|是)
                export "$varname"="是"
                break
                ;;
            [Nn]|[Nn][Oo]|否)
                export "$varname"="否"
                break
                ;;
            *)
                echo -e "${RED}请输入 Y 或 N${NC}"
                ;;
        esac
    done
    echo -e "${GREEN}  ✓ 已选择: ${!varname}${NC}"
    echo "[$varname] ${!varname}" >> "$RESULT_FILE"
    echo ""
}

# ============================================================
#  开场
# ============================================================
clear
echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║          ☁️  云笔记系统 - 需求问答向导  ☁️                ║"
echo "║                                                          ║"
echo "║   本向导将帮助你逐项明确项目需求                          ║"
echo "║   所有答案将保存到: 需求问答结果.txt                      ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

read -r -p "按 Enter 开始..."

# ============================================================
#  第一轮：项目背景与业务目标
# ============================================================
print_header "📋 第一轮：项目背景与业务目标"

echo -e "${GREEN}${BOLD}1.1 项目定位与目标${NC}"
echo ""

ask_select "为什么要做这个云笔记系统？" \
    PROJECT_PURPOSE \
    "个人学习/练手项目" \
    "创业 MVP（最小可行产品）" \
    "公司内部工具" \
    "开源项目" \
    "学术研究项目" \
    "接单/外包项目"

ask_select "你期望的成功标准是什么？" \
    SUCCESS_CRITERIA \
    "完成所有核心功能即可，不关注并发量" \
    "能稳定支持 10-50 人同时使用" \
    "能稳定支持 50-200 人同时使用" \
    "能稳定支持 200-1000 人同时使用" \
    "能支持 1000+ 人同时使用，具备水平扩展能力"

echo -e "${GREEN}${BOLD}1.2 目标用户${NC}"
echo ""

ask_select "主要目标用户群体是？" \
    TARGET_USERS \
    "仅个人使用" \
    "小团队（2-20人）" \
    "中型团队（20-100人）" \
    "大型组织（100-1000人）" \
    "开放给所有互联网用户（SaaS）"

ask_select "用户的技术水平如何？" \
    USER_TECH_LEVEL \
    "全部是开发者（懂 Markdown、Git 等）" \
    "主要是开发者，也有少量非技术人员" \
    "开发者和非技术人员各半" \
    "主要是非技术人员（产品、运营、写作等）"

ask_open "预计同时在线用户数（并发）大概是多少？" \
    EXPECTED_CONCURRENT_USERS

echo -e "${GREEN}${BOLD}1.3 实时协作场景（核心功能）${NC}"
echo ""

ask_select "\"实时协作\"具体指什么级别？" \
    REALTIME_COLLAB_LEVEL \
    "A) 完全实时（类似 Google Docs）：看到对方光标、实时同步每个字符变更" \
    "B) 准实时（类似 Notion）：多人同时编辑，自动同步，但不一定看到光标" \
    "C) 轻协作（类似 GitHub 文件编辑）：多人可编辑，自动合并/提示冲突" \
    "D) 仅共享：多人可查看，但同一时间只有一人可编辑"

ask_open "同一篇文档，预计最多几个人同时编辑？" \
    MAX_SIMULTANEOUS_EDITORS

ask_yesno "协作时是否需要显示「谁正在编辑」（用户头像/光标位置/在线状态）？" \
    SHOW_COLLABORATORS

ask_yesno "是否需要文档评论区/行内批注功能？" \
    NEED_COMMENTS

echo -e "${GREEN}${BOLD}1.4 权限与安全${NC}"
echo ""

ask_yesno "是否需要用户注册/登录系统？" \
    NEED_AUTH

if [ "$NEED_AUTH" = "是" ]; then
    ask_select "文档的权限模型是？" \
        DOC_PERMISSION_MODEL \
        "个人私有 + 可分享链接（类似 Google Drive）" \
        "团队/工作空间模式（成员共享）" \
        "两者都需要（私有 + 团队空间）"

    ask_select "权限粒度需要多细？" \
        PERMISSION_GRANULARITY \
        "简单两级：可读 / 可写" \
        "三级：只读 / 可评论 / 可编辑" \
        "四级：只读 / 可评论 / 可编辑 / 管理员"
else
    echo -e "${YELLOW}  → 无需登录，后续问题自动跳过${NC}"
    echo ""
fi

# ============================================================
#  第二轮：笔记核心功能
# ============================================================
print_header "📝 第二轮：笔记核心功能"

echo -e "${GREEN}${BOLD}2.1 笔记管理${NC}"
echo ""

ask_select "笔记的组织方式？" \
    NOTE_ORGANIZATION \
    "平铺列表（类似备忘录）" \
    "文件夹/目录树结构" \
    "标签系统" \
    "文件夹 + 标签混合"

ask_yesno "是否需要 Markdown 实时预览（分屏/即时渲染）？" \
    NEED_MD_PREVIEW

ask_yesno "是否需要支持图片/附件上传？" \
    NEED_FILE_UPLOAD

if [ "$NEED_FILE_UPLOAD" = "是" ]; then
    ask_open "单个文件大小限制建议（MB）？" \
        MAX_FILE_SIZE_MB
fi

ask_yesno "是否需要笔记版本历史/修订记录？" \
    NEED_VERSION_HISTORY

if [ "$NEED_VERSION_HISTORY" = "是" ]; then
    ask_open "版本历史需要保留多少天/多少个版本？" \
        VERSION_RETENTION
fi

ask_yesno "是否需要全文搜索功能？" \
    NEED_FULLTEXT_SEARCH

ask_yesno "是否需要笔记导出功能（PDF/HTML/Markdown 文件）？" \
    NEED_EXPORT

# ============================================================
#  第三轮：技术约束
# ============================================================
print_header "⚙️ 第三轮：技术约束与偏好"

echo -e "${GREEN}${BOLD}3.1 技术栈确认${NC}"
echo ""

echo -e "${YELLOW}  根据你的初始描述，技术栈如下：${NC}"
echo -e "  - 前端: Vue (Vue 3? Vue 2?) + npm run dev"
echo -e "  - 后端: Python FastAPI"
echo -e "  - 部署: 后端使用 Docker"
echo -e "  - 文档格式: Markdown"
echo ""

ask_select "Vue 版本？" \
    VUE_VERSION \
    "Vue 3（Composition API）" \
    "Vue 2（Options API）"

ask_select "前端 UI 框架偏好？" \
    UI_FRAMEWORK \
    "Element Plus（Vue 3）" \
    "Ant Design Vue" \
    "Naive UI" \
    "Vuetify" \
    "Tailwind CSS（无组件库）" \
    "无所谓，你来推荐"

ask_select "数据库偏好？" \
    DATABASE \
    "PostgreSQL" \
    "MySQL" \
    "MongoDB" \
    "SQLite（轻量/开发阶段）" \
    "无所谓，你来推荐"

ask_yesno "是否需要使用 WebSocket 实现实时协作？" \
    USE_WEBSOCKET

ask_select "实时协作的同步算法偏好？" \
    SYNC_ALGORITHM \
    "OT（Operational Transformation，如 ShareDB）" \
    "CRDT（Conflict-free Replicated Data Types，如 Yjs）" \
    "简单锁机制（编辑时锁定文档）" \
    "不了解，你来推荐"

ask_yesno "是否需要 Redis（缓存/消息队列）？" \
    NEED_REDIS

echo -e "${GREEN}${BOLD}3.2 部署与运维${NC}"
echo ""

ask_yesno "是否已有服务器/云服务商？" \
    HAS_SERVER

if [ "$HAS_SERVER" = "是" ]; then
    ask_open "使用哪个云服务商/服务器？" \
        CLOUD_PROVIDER
fi

ask_select "期望的部署方式？" \
    DEPLOY_METHOD \
    "Docker Compose 单机部署" \
    "Kubernetes (K8s) 集群部署" \
    "云服务商托管（如阿里云 SAE / AWS ECS）" \
    "仅本地开发使用"

# ============================================================
#  第四轮：扩展与未来
# ============================================================
print_header "🔮 第四轮：未来扩展"

ask_yesno "未来是否需要移动端（App/小程序）？" \
    FUTURE_MOBILE

ask_yesno "未来是否需要支持富文本（非 Markdown）文档？" \
    FUTURE_RICH_TEXT

ask_yesno "未来是否需要开放 API 给第三方？" \
    FUTURE_OPEN_API

ask_yesno "是否需要考虑离线编辑（PWA/本地缓存）？" \
    FUTURE_OFFLINE

ask_yesno "是否需要多语言/国际化支持？" \
    NEED_I18N

# ============================================================
#  第五轮：开放问题
# ============================================================
print_header "💡 第五轮：补充信息"

ask_open "是否有参考竞品？（如 Notion、语雀、飞书文档、Obsidian 等）" \
    REFERENCE_PRODUCTS

ask_open "还有哪些我没想到但你认为重要的需求或想法？" \
    ADDITIONAL_REQUIREMENTS

ask_open "项目的预期开发周期？" \
    DEV_TIMELINE

ask_open "团队规模/人数？" \
    TEAM_SIZE

# ============================================================
#  完成
# ============================================================
echo ""
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo -e "${CYAN}${BOLD}  ✅ 问卷完成！${NC}"
echo -e "${CYAN}${BOLD}============================================================${NC}"
echo ""
echo -e "所有答案已保存到: ${GREEN}${BOLD}需求问答结果.txt${NC}"
echo ""
echo -e "请将该文件内容发送给我，我将根据你的回答："
echo -e "  1. 进行深度分析"
echo -e "  2. 指出潜在矛盾与风险"
echo -e "  3. 追问不确定的部分"
echo -e "  4. 最终生成完整的 Markdown 需求文档"
echo ""

