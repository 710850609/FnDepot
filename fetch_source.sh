#!/bin/bash
# 获取名称=FnDepot 且存在 fnpack.json 的仓库列表
set -e

PAGE=1          # 从第 1 页开始
PER_PAGE=100    # 每页条数，最大 100
> repo_list.txt # 清空旧结果

while :; do
  echo "==== 拉取第 $PAGE 页 ===="
  # 拉取一页
  curl -s "https://api.github.com/search/repositories?q=FnDepot+in:name&per_page=$PER_PAGE&page=$PAGE" \
    > page.json

  # 如果本页已经没有仓库就退出
  COUNT=$(jq '.items | length' page.json)
  [ "$COUNT" -eq 0 ] && break

  # 遍历本页每个仓库
  for ((i=0;i<COUNT;i++)); do
    REPO=$(jq -r ".items[$i].full_name" page.json)
    URL=$(jq  -r ".items[$i].html_url"  page.json)
    echo "检查 $REPO ..."

    # HEAD 请求 fnpack.json （只取 header，比 GET 轻量）
    if curl -sI "https://raw.githubusercontent.com/$REPO/main/fnpack.json" \
       | grep -q "^HTTP.*200"; then
      echo "$URL" >> repo_list.txt
      echo "  ✔ 存在 fnpack.json"
    else
      echo "  ✘ 不存在 fnpack.json"
    fi
  done

  ((PAGE++))
done

rm -f page.json
echo "===== 带 fnpack.json 的 FnDepot 仓库 ====="
cat repo_list.txt