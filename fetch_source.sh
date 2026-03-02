#!/bin/bash
# 获取名称=FnDepot 且存在 fnpack.json 的仓库列表
# FnDepot规范文档
# <a href="https://github.com/EWEDLCM/FnDepot/blob/main/README.md">FnDepot规范文档</a>
# <a href="https://ecn6sp7e44q3.feishu.cn/wiki/VSrmwqtjhigaygkWkyoceEvvnlb">FnDepot规范文档</a>
set -e

# 支持的架构列表（可通过环境变量覆盖）
SUPPORTED_ARCHES=${SUPPORTED_ARCHES:-"x86 arm"}
OUTPUT_FILE="repo_list.txt"
> "$OUTPUT_FILE" # 清空旧结果
PAGE=1          # 从第 1 页开始
PER_PAGE=100    # 每页条数，最大 100

echo "支持的架构: $SUPPORTED_ARCHES"

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
        echo "$URL" >> "$OUTPUT_FILE"
        echo "  ✔ 存在 fnpack.json 且包含有效应用"
      else
        echo "  ✘ 存在 fnpack.json 但无有效应用"
      fi
    else
      echo "  ✘ 不存在 fnpack.json"
    fi
  done

  ((PAGE++))
done

rm -f page.json
echo "===== 带 fnpack.json 的 FnDepot 仓库 ====="
cat "$OUTPUT_FILE"
