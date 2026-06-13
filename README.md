# 🎮 Maimai DX Profile Card

在 GitHub README 中展示你的 maimai DX 玩家信息卡片！

![maimai-card](maimai-card.svg)

## 🚀 快速开始

### 方式一：Fork 本仓库（推荐）

1. **Fork 本仓库**

2. **设置 GitHub Secrets**
   - 进入你 Fork 的仓库 → Settings → Secrets and variables → Actions
   - 添加以下 Secret：
     - `LXNS_TOKEN`: 你的落雪咖啡屋查分器个人 API 密钥（获取路径：落雪查分器官网 → 账号详情 → 生成个人 API 密钥）

3. **启用 GitHub Actions**
   - 进入 Actions 标签页
   - 点击 "I understand my workflows, go ahead and enable them"

4. **手动运行或等待自动更新**
   - Actions → Update Maimai Card → Run workflow

5. **在你的 README 中添加图片**
   ```markdown
   ![maimai-card](https://raw.githubusercontent.com/你的用户名/maimai-profile-card/main/maimai-card.svg)
   ```

### 方式二：本地运行

```bash
# 安装依赖
pip install requests

# 使用用户名生成
python generate_card.py --username 你的用户名 --output maimai-card.svg

# 或使用 QQ 号生成
python generate_card.py --qq 你的QQ号 --output maimai-card.svg
```

## 📝 在 README 中使用

```markdown
<!-- 基础用法 -->
![Maimai Profile](https://raw.githubusercontent.com/你的用户名/maimai-profile-card/main/maimai-card.svg)

<!-- 居中显示 -->
<p align="center">
  <img src="https://raw.githubusercontent.com/你的用户名/maimai-profile-card/main/maimai-card.svg" alt="Maimai Profile Card"/>
</p>

<!-- 带链接 -->
[![Maimai Profile](https://raw.githubusercontent.com/你的用户名/maimai-profile-card/main/maimai-card.svg)](https://www.diving-fish.com/maimaidx/prober/)
```

## ⚙️ 配置说明

### GitHub Secrets

| Secret | 说明 | 必填 |
|--------|------|------|
| `LXNS_TOKEN` | 落雪咖啡屋个人 API 密钥 | 是 (推荐) |
| `LXNS_DEV_TOKEN` | 落雪咖啡屋开发者 API 密钥 | 否 |
| `MAIMAI_QQ` | 绑定的 QQ 号（使用开发者 Token 时必填） | 否 |
| `MAIMAI_FRIEND_CODE` | 游戏好友码（使用开发者 Token 时必填） | 否 |

### 更新频率

默认每 6 小时自动更新一次。你可以在 `.github/workflows/maimai-card.yml` 中修改：

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # 每6小时
    # - cron: '0 0 * * *'  # 每天一次
    # - cron: '0 */12 * * *'  # 每12小时
```

## 🎨 卡片展示内容

- 🏷️ 玩家昵称
- 📊 Rating（带颜色区分）
- 🎖️ 段位信息
- 🏅 称号/牌子
- 📈 DX Score / SD Score
- 🏆 最高达成率

## ⚠️ 注意事项

1. **隐私设置**: 确保你的查分器账号没有设置隐私，否则无法获取数据
2. **用户协议**: 需要同意查分器用户协议才能被查询
3. **API 限制**: diving-fish API 有请求频率限制，请勿过于频繁更新

## 📜 致谢

- [diving-fish 查分器](https://www.diving-fish.com/maimaidx/prober/) - 数据来源
- 受 [GitHub Stats Card](https://github.com/anuraghazra/github-readme-stats) 启发

## 📄 License

MIT License
