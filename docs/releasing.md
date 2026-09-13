# 發版流程

版本只有一個來源：PR 的來源分支名稱 `vX.Y.Z`。不用維護 VERSION、不用手動建立 tag。

## 每次發版

1. 建立版本分支，例如 `git switch -c v0.1.1`，在該分支完成開發。
2. 開 PR 到 main，等待 CI 通過。版本分支必須符合 `vX.Y.Z`，且同名 tag 不得存在。
3. 合併 PR。Release workflow 在該 PR 合併後的 commit 打 tag，測試並發布 GitHub Release，附套件、SHA256SUMS 與自動 release notes。
4. 到 **homebrew-tap → Actions → Update toolbox → Run workflow**，保留 main 並按執行。無需填版本。
5. tap 取得最新正式 Release、驗證 checksum、安裝並執行 brew test，成功後直接 commit 到 main。使用者即可 `brew update && brew upgrade tbx`。

一般開發分支合併 main 不發版；直接 push main 也不發版。以 v 開頭的來源分支會進行嚴格版本格式檢查。Release 僅接受同 repo 的版本分支。

支援 merge commit、squash 與 rebase merge，使用 GitHub PR 事件的 merge_commit_sha 定位合併結果，不以 workflow 執行時最新 main 取代它。請依版本順序合併發版 PR，等待上一版 Release 完成再合併下一版。

## 一次性啟用

把兩個 repo 的 workflow 和 scripts 提交並合併 main。兩邊都使用 GitHub 自動提供的 GITHUB_TOKEN，workflow 已宣告必要權限，不需 PAT、GitHub App 或額外 secret。

若 repo 或組織政策禁止 Actions 寫入，或 main 保護規則禁止 bot 直接提交，需由管理者允許相應操作；workflow 不繞過保護規則。tap 的更新按鈕需要 workflow 存在 main 後才會出現。

## 本機驗證

在版本分支上執行 `bash scripts/package.sh`，或明確指定 `bash scripts/package.sh v0.1.1`。它會檢查命令、產生套件並測試解壓後的 symlink 啟動。

VERSION 只產生在發布套件內。開發 checkout 的 `tbx --version` 顯示 `tbx dev`，安裝版顯示正式版本。

## 失敗與重跑

- 測試失敗：不發布 Release；修正後使用新版本分支重新合併。
- 發布過程失敗：在原 Release run 選 Re-run failed jobs。同名 tag 必須仍指向原合併 commit；公開 Release 的附件不覆蓋，draft 可補傳後發布。
- tap 更新失敗：修正原因後再按 Run workflow。下載、checksum 或安裝測試失敗都不提交；已是相同或更新版本就不修改。
- tap 推送時 main 已有別人提交：push 會安全失敗，不強制覆寫；再按一次即可在最新 main 重試。
- 已發布版本有 bug：發下一個 patch，不移動既有 tag 或替換公開附件。

目前保留 `tbx@0.1.0` 固定配方，只讓 `tbx.rb` 跟隨正式 Release。更新 workflow 本身執行安裝測試，不依賴 bot commit 再觸發其他 CI。

## GitHub 行為參考

- [PR 合併 commit 的定義](https://docs.github.com/en/rest/pulls/pulls#get-a-pull-request)
- [workflow_dispatch 與 workflow 權限](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
