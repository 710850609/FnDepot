#!/bin/bash
# 获取名称=FnDepot 且存在 fnpack.json 的仓库列表
# FnDepot规范文档
# <a href="https://github.com/EWEDLCM/FnDepot/blob/main/README.md">FnDepot规范文档</a>
# <a href="https://ecn6sp7e44q3.feishu.cn/wiki/VSrmwqtjhigaygkWkyoceEvvnlb">FnDepot规范文档</a>
set -e

# 支持的架构列表（可通过环境变量覆盖）
SUPPORTED_ARCHES=${SUPPORTED_ARCHES:-"x86 arm"}

# 白名单和黑名单（可通过环境变量覆盖）
WHITELIST=${WHITELIST:-"RROrg/fn-apps"}
BLACKLIST=${BLACKLIST:-"\
12hgl/FnDepot \
FNOSP/FnDepot \
ByronChen7/FnDepot \
DYXIAOMA/FnDepot \
mah1618/FnDepot \
coder23j/FnDepot-arm \
hw532/FnDepot-arm \
baishicoke/FnDepot-arm \
hsliuyong/FnDepot2 \
"}

OUTPUT_FILE="repo_list.txt"
OUTPUT_FILE_TEMP="repo_list_temp.txt"

echo "支持的架构: $SUPPORTED_ARCHES"

> "$OUTPUT_FILE" # 清空旧结果

check_repo() {
  REPO=$1
  echo "检查 $REPO ..."

  # 单个 HTTP 请求获取 fnpack.json 并检查状态码和内容
  FNPACK_RESPONSE=$(curl -s -w "\n%{http_code}\n" "https://raw.githubusercontent.com/$REPO/main/fnpack.json")
  HTTP_STATUS=$(echo "$FNPACK_RESPONSE" | tail -n 1)
  FNPACK_CONTENT=$(echo "$FNPACK_RESPONSE" | head -n -1)
  
  if [[ "$HTTP_STATUS" == "200" ]]; then
    # 获取所有应用名称
    app_names=$(echo "$FNPACK_CONTENT" | jq -r 'keys[]' | tr -d '\000')
    
    # 检查是否至少有一个有效应用（有 download_url 或对应 fpk 包）
    has_valid_app=false
    
    for app_name in $app_names; do  
      # 优先检查是否有 arch_diff 中的 download_url
      has_arch_download_url=$(echo "$FNPACK_CONTENT" | jq -r ".[\"$app_name\"].arch_diff != null and (any(.[\"$app_name\"].arch_diff[]; .download_url != null and .download_url != \"\"))" | tr -d '\000')
      # 如果有下载地址或 fpk 包，标记为有效应用
      if [[ "$has_arch_download_url" == "true" ]]; then
        has_valid_app=true
        break
      fi
      # 检查是否有 download_url
      has_download_url=$(echo "$FNPACK_CONTENT" | jq -r ".[\"$app_name\"].download_url != null and .[\"$app_name\"].download_url != \"\"" | tr -d '\000')
      if [[ "$has_download_url" == "true" ]]; then
        has_valid_app=true
        break
      fi
    
      # 检查是否存在对应的 fpk 包（使用 HEAD 请求，只检查响应头）
      has_fpk_package=false
      
      # 检查 {app_name}.fpk
      fpk_url="https://raw.githubusercontent.com/$REPO/main/$app_name/$app_name.fpk"
      fpk_status=$(curl -s -o /dev/null -w "%{http_code}" "$fpk_url")
      
      if [[ "$fpk_status" == "200" ]]; then
        has_fpk_package=true
      else
        # 如果 {app_name}.fpk 不存在，检查 {app_name}_{arch}.fpk 格式
        check_arches="all ${SUPPORTED_ARCHES}"
        for arch in $check_arches; do
          arch_fpk_url="https://raw.githubusercontent.com/$REPO/main/$app_name/${app_name}_${arch}.fpk"
          arch_fpk_status=$(curl -s -o /dev/null -w "%{http_code}" "$arch_fpk_url")
          if [[ "$arch_fpk_status" == "200" ]]; then
            has_fpk_package=true
            break
          fi
        done
      fi
      
      # 如果有下载地址或 fpk 包，标记为有效应用
      if [[ "$has_fpk_package" == "true" ]]; then
        has_valid_app=true
        break
      fi
    done
    
    if [[ "$has_valid_app" == "true" ]]; then
      echo "  ✔ 存在 fnpack.json 且包含有效应用"
      return 0  # 有效
    else
      echo "  ✘ 存在 fnpack.json 但无有效应用"
      return 1  # 无效
    fi
  else
    echo "  ✘ 不存在 fnpack.json"
    return 1  # 无效
  fi
}

# 追加有效仓库地址
add_repo() {
  local url="$1"
  echo "$url" >> "$OUTPUT_FILE"
}

fetch_repo() {
  > "$OUTPUT_FILE_TEMP"

  PER_PAGE=100    # 每页条数，最大 100
  PAGE=1          # 从第 1 页开始
  > page.json
  echo "开始拉取所有普通仓库..."
  while :; do
    echo "==== 拉取第 $PAGE 页 ===="
    curl -s "https://api.github.com/search/repositories?q=FnDepot+in:name&per_page=$PER_PAGE&page=$PAGE" \
    > page.json
    # 如果本页已经没有仓库就退出
    COUNT=$(jq '.items | length' page.json)
    [ "$COUNT" -eq 0 ] && break
    for ((i=0;i<COUNT;i++)); do
      repo=$(jq -r ".items[$i].full_name" page.json)
      if ! grep -q "$repo" "$OUTPUT_FILE_TEMP"; then
        echo "$repo" >> "$OUTPUT_FILE_TEMP"
        # echo "追加仓库：$repo"
      # else 
        # echo "跳过追加${repo}仓库： 已存在"
      fi
    done
    ((PAGE++))
  done 

  PAGE=1
  > page.json
  echo "开始拉取所有从https://github.com/EWEDLCM/FnDepot仓库fork出来的仓库..."
  while :; do
    echo "==== 拉取第 $PAGE 页 ===="
    curl -s "https://api.github.com/search/repositories?q=FnDepot+in:name+fork:true&per_page=$PER_PAGE&page=$PAGE" \
    > page.json
    # 如果本页已经没有仓库就退出
    COUNT=$(jq '.items | length' page.json)
    [ "$COUNT" -eq 0 ] && break
    for ((i=0;i<COUNT;i++)); do
      repo=$(jq -r ".items[$i].full_name" page.json)
      if ! grep -q "$repo" "$OUTPUT_FILE_TEMP"; then
        echo "$repo" >> "$OUTPUT_FILE_TEMP"
        # echo "追加仓库：$repo"
      # else 
        # echo "跳过追加${repo}仓库： 已存在"
      fi
    done
    ((PAGE++))
  done

  

  rm -f page.json
}

check_and_add_repo() {
  echo "开始检查并添加有效仓库..."
  repo_list=$(cat "$OUTPUT_FILE_TEMP")
  # 处理黑名单和白名单
  if [[ -n "$BLACKLIST" ]]; then
    echo "应用黑名单过滤..."
    # 去除黑名单中的仓库
    for blacklist_item in $BLACKLIST; do
      if grep -q "$blacklist_item" "$OUTPUT_FILE_TEMP"; then
        repo_list=$(echo "$repo_list" | grep -v "$blacklist_item")
        echo "  ✔ 移除黑名单仓库 $blacklist_item"
      fi
    done
    # 写回文件
    echo "$repo_list" > "$OUTPUT_FILE_TEMP"
  fi
  if [[ -n "$WHITELIST" ]]; then
    echo "添加白名单仓库..."
    # 追加白名单中的仓库
    for whitelist_item in $WHITELIST; do
      # 检查白名单仓库是否已经存在
      if ! grep -q "$whitelist_item" "$OUTPUT_FILE_TEMP"; then
        echo "$whitelist_item" >> "$OUTPUT_FILE_TEMP"
        echo "  ✔ 添加白名单仓库 $whitelist_item"
      fi
    done
  fi
  repo_list=$(cat "$OUTPUT_FILE_TEMP")
  for repo in $repo_list; do
    if check_repo "$repo" ; then
      # 构建仓库 URL
      add_repo "https://github.com/$repo"
    else
      echo "  ✘ 仓库 $repo 无效"
    fi
  done
}

# 拉取仓库列表
fetch_repo
check_and_add_repo
echo "===== 带 fnpack.json 的 FnDepot 仓库 ====="
cat "$OUTPUT_FILE"
