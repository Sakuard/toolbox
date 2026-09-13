# toolbox (`tbx`)

以 Bash 與 fzf 提供常用開發工具的命令列入口。

## 安裝與更新

```sh
brew install Sakuard/tap/tbx
brew update
brew upgrade tbx
```

`tbx --version` 自 v0.1.1 起提供。子命令需要的工具（例如 kubectl）需另行安裝。

## 使用

```sh
tbx             # 互動選單
tbx kube        # Kubernetes 選單
tbx kube logs   # 直接執行子命令
```

## 本機開發

在 repo 根目錄執行：

```sh
mkdir -p ~/.local/bin
ln -sf "$PWD/bin/tbx" ~/.local/bin/tbx
export PATH="$HOME/.local/bin:$PATH"
bash scripts/package.sh
# 非版本分支可用 bash scripts/package.sh v0.1.1 驗證打包
```

將 PATH 設定加入 `~/.zshrc` 可永久生效。

## 發版

vX.Y.Z 分支 PR 合併 main → 自動建立 tag 與 GitHub Release → 在 homebrew-tap 按 Run workflow → 測試通過後自動更新配方。

首次設定、逐步指令與重跑方式見[發版指南](docs/releasing.md)。

## cat 檔案瀏覽

```sh
tbx cat                      # 從目前目錄選檔案
tbx cat ./config             # 從指定目錄選檔案
```

也可以在 `tbx` 選單選 **cat**。搜尋檔名，Enter 後直接在 tbx 顯示內容。

JSON／YAML 會自動啟用**上方搜尋框**，下方有限高度區域顯示內容。不用按管線鍵或另外選 jq／yq；搜尋只比對當前層 key，命中字元標紅，預覽只留下符合 key 的完整子樹。

- Enter：進入所選 key，清空 query，繼續查下一層；單值也留在畫面內。
- ↑ / ↓：選 key 並捲動；Alt-↑ / Alt-↓、PgUp / PgDn：單獨捲動內容。
- Ctrl-B 或 Alt-←：返回上一層。
- Esc：回檔案選單，再按 Esc 離開。
- Ctrl-O：輸出目前層並回檔案選單。

一般文字檔直接顯示、↑↓ 捲動。無效或多文件 JSON／YAML 顯示原文並提示；缺少查詢工具時仍可讀原文。

需要 python3、fzf；JSON 查詢使用 jq，YAML 另需 Mike Farah yq v4。YAML 查詢不保留註解、anchor 或原始排版。陣列按原始 index 逐層瀏覽。

```sh
python3 -m unittest discover -s tests -v
```
