#!/bin/bash

BUILD_VER="0.0.1"
APP_NAME="fndepot.source"

declare -A PARAMS
# 默认值
PARAMS[release]="false"
PARAMS[arch]="x86_64"
# 解析 key=value 格式的参数
for arg in "$@"; do
  if [[ "$arg" == *=* ]]; then
    key="${arg%%=*}"
    value="${arg#*=}"
    PARAMS["$key"]="$value"
  else
    # 处理标志参数
    case "$arg" in
      --pre)
        PARAMS[pre]="true"
        ;;
      *)
        echo "忽略未知参数: $arg"
        ;;
    esac
  fi
done

release="${PARAMS[release]}"
arch="${PARAMS[arch]}"
echo "release: ${release}"
echo "arch: ${arch}"


# platform 取值 x86, arm, risc-v, all
platform=""
os_min_version="1.0.0"
if [ "${arch}" == "x86_64" ]; then
    platform="x86"
    os_min_version="1.1.8"
    py_platform="manylinux_2_28_x86_64"
elif [ "${arch}" == "aarch64" ]; then
    platform="aarch64"
    os_min_version="1.0.2"
    py_platform="manylinux_2_28_aarch64"
elif [ "${arch}" == "riscv64" ]; then
    platform="riscv64"
    py_platform="manylinux_2_34_riscv64"
    os_min_version="1.0.0"
else
    echo "不支持的 arch 参数"
    exit 1
fi
echo "设置 platform 为: ${platform}"
echo "---------------------------------------"

build_backend() {
    echo "下载py依赖"
#    rm -rf "${APP_NAME}/app/backend"
    rm -rf "${APP_NAME}/app/backend/wheels"
    mkdir -p "${APP_NAME}/app/backend/wheels"
    # 下载 wheel
    app_script_path="${APP_NAME}/app/backend"
    pip download \
        --only-binary=:all: \
        --platform $py_platform \
        --python-version 311 \
        -r "${APP_NAME}/app/backend/requirements.txt" \
        -d ${app_script_path}/wheels
        
#    echo "写入脚本到app"
#    rsync -a --exclude='.venv' \
#    --exclude='__pycache__' \
#    backend/ "${app_script_path}/"
}

build_fpk() {
    local fpk_version=$BUILD_VER
    if [ "${release}" != "true" ]; then
        fpk_version="${fpk_version}-$(TZ='Asia/Shanghai' date +'%Y%m%d%H%M%S')"
    fi
    sed -i "s|^[[:space:]]*version[[:space:]]*=.*|version=${fpk_version}|" "${APP_NAME}/manifest"
    echo "设置 manifest 的 version 为: ${fpk_version}"
    sed -i "s|^[[:space:]]*platform[[:space:]]*=.*|platform=${platform}|" "${APP_NAME}/manifest"
    echo "设置 manifest 的 platform 为: ${platform}"
    sed -i "s|^[[:space:]]*os_min_version[[:space:]]*=.*|os_min_version=${os_min_version}|" "${APP_NAME}/manifest"
    echo "设置 manifest 的 os_min_version 为: ${os_min_version}"

    echo "开始打包 fpk"
    if command -v fnpack >/dev/null 2>&1; then
        echo "使用系统已安装的 fnpack 进行打包"
        fnpack build --directory "${APP_NAME}/"  || { echo "打包失败"; exit 1; }
    else
        echo "使用本地 fnpack 脚本进行打包"
        ./fnpack.sh build --directory "${APP_NAME}" || { echo "打包失败"; exit 1; }
    fi 

    fpk_name="${APP_NAME}-${arch}-${fpk_version}.fpk"
    rm -f "${fpk_name}"
    mv "${APP_NAME}.fpk" "${fpk_name}"
    echo "打包完成: ${fpk_name}"
}


if [ "${release}" == "true" ]; then
    fpk_version="${fpk_version}-$(TZ='Asia/Shanghai' date +'%Y%m%d%H%M%S')"
fi

build_backend

build_fpk

exit 0