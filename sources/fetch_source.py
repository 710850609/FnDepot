#!/usr/bin/env python3
"""
获取名称=FnDepot 且存在 fnpack.json 的仓库列表
FnDepot规范文档:
https://github.com/EWEDLCM/FnDepot/blob/main/README.md
https://ecn6sp7e44q3.feishu.cn/wiki/VSrmwqtjhigaygkWkyoceEvvnlb
"""

import os
import re
import sys
import time

try:
    import requests
except ImportError:
    print("请先安装 requests 库: pip install requests")
    sys.exit(1)


def parse_args():
    """解析 key=value 格式的参数"""
    params = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            params[key] = value
    return params


def main():
    params = parse_args()

    github_api_sleep = float(params.get("github_api_sleep", 0))
    print(f"github api请求时，睡眠时间: {github_api_sleep} s")

    proxy_url = ""

    SUPPORTED_ARCHES = os.environ.get("SUPPORTED_ARCHES", "x86 arm").split()

    WHITELIST = os.environ.get("WHITELIST", " ".join([
        # "EWEDLCM/FnDepot",
        "RROrg/fn-apps",
        "shuangji66/FnDepot",
        "jianzhichu/FnDepot",
        "yuexps/FnDepot",
        "hbestm/FnDepot",
    ])).split()

    BLACKLIST = os.environ.get("BLACKLIST", " ".join([
        "12hgl/FnDepot",
        "FNOSP/FnDepot",
        "ByronChen7/FnDepot",
        "DYXIAOMA/FnDepot",
        "AKAAKUNLEE/*",
        "Stranger10086/*",
        "xuanxiaofeng/*",
        "p125141/*",
        "YingHaoIT/*",
        "wootor/*",
        "xubillde/*",
        "maliang99/*",
        "wtugwyitx/*",
        "zhang12345eer/*",
        "qq1416567661/*",
        "zsferking/*",
        "nbcoming/*",
        "miaomi9/*",
        "hsliuyong/*",
        "15064187978/*",
        "jankxia/*",
        "henry-hub/*",
        "xiaoliang2012/*",
        "16xiaoji/*",
        "ryxiang/FnDepot",
    ])).split()

    OUTPUT_FILE = "repo_list.txt"
    OUTPUT_FILE_TEMP = "repo_list_temp.txt"

    print(f"支持的架构: {' '.join(SUPPORTED_ARCHES)}")

    with open(OUTPUT_FILE, "w") as f:
        pass

    # 获取原创仓库的应用列表
    ori_repo_apps = {}
    for ori_repo in WHITELIST:
        try:
            resp = requests.get(
                f"{proxy_url}https://raw.githubusercontent.com/{ori_repo}/refs/heads/main/fnpack.json",
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            ori_repo_apps[ori_repo] = list(data.keys())
        except Exception:
            ori_repo_apps[ori_repo] = []

    def is_ori_repo(app_name, repo):
        """判断仓库是否为原创仓库"""
        if repo in WHITELIST:
            return True
        for ori_repo in WHITELIST:
            if app_name in ori_repo_apps.get(ori_repo, []) and repo != ori_repo:
                return False
        return True

    def check_repo(repo):
        """检查仓库是否有效"""
        print(f"检查 {repo} ...")

        if github_api_sleep > 0:
            time.sleep(github_api_sleep)

        try:
            resp = requests.get(
                f"{proxy_url}https://raw.githubusercontent.com/{repo}/main/fnpack.json",
                timeout=30,
            )
            if resp.status_code != 200:
                print(f"  ✘ 不存在 fnpack.json：{resp.text}")
                return False
            fnpack_content = resp.json()
        except Exception as e:
            print(f"  ✘ 检查 fnpack.json 时出错: {e}")
            return False

        if fnpack_content.get("schema_version") == "2" and fnpack_content.get("source_info") and fnpack_content.get("apps"):
            return check_repo_v2(repo, fnpack_content)
        else:
            return check_repo_v1(repo, fnpack_content)


    def check_repo_v1(repo, fnpack_content) -> bool:
        app_names = list(fnpack_content.keys())
        has_valid_app = False
        is_original = True
        check_repo_v1(repo, fnpack_content)
        for app_name in app_names:
            print(f"  检查应用 {app_name} ...")

            if app_name == "test":
                is_original = False
                print(f"  ✘ 排除测试仓库：{repo}")
                break

            if is_ori_repo(app_name, repo):
                is_original = True
            else:
                is_original = False
                print(f"  ✘ 排除非原创仓库：{repo}")
                break

            app_info = fnpack_content.get(app_name, {})

            # 检查 arch_diff 中的 download_url
            has_arch_download_url = False
            arch_diff = app_info.get("arch_diff")
            if isinstance(arch_diff, list):
                for item in arch_diff:
                    if isinstance(item, dict) and item.get("download_url"):
                        has_arch_download_url = True
                        break

            if has_arch_download_url:
                has_valid_app = True

            # 检查 download_url
            if app_info.get("download_url"):
                has_valid_app = True

            # 检查 fpk 包
            has_fpk_package = False

            if github_api_sleep > 0:
                time.sleep(github_api_sleep)

            fpk_url = f"{proxy_url}https://raw.githubusercontent.com/{repo}/main/{app_name}/{app_name}.fpk"
            try:
                fpk_resp = requests.head(fpk_url, timeout=30)
                if fpk_resp.status_code == 200:
                    has_fpk_package = True
            except Exception:
                pass

            if not has_fpk_package:
                check_arches = ["all"] + SUPPORTED_ARCHES
                for arch in check_arches:
                    if github_api_sleep > 0:
                        time.sleep(github_api_sleep)
                    arch_fpk_url = f"{proxy_url}https://raw.githubusercontent.com/{repo}/main/{app_name}/{app_name}_{arch}.fpk"
                    try:
                        arch_fpk_resp = requests.head(arch_fpk_url, timeout=30)
                        if arch_fpk_resp.status_code == 200:
                            has_fpk_package = True
                    except Exception:
                        pass

            if has_fpk_package:
                has_valid_app = True

        if has_valid_app and is_original:
            print("  ✔ 存在 fnpack.json 且包含有效应用")
            return True
        else:
            print("  ✘ 存在 fnpack.json 但无有效应用或非原创仓库")
            return False

    def check_repo_v2(repo, fnpack_content) -> bool:
        print(f"跳过第二版本处理 {repo} ...")
        return False

    def add_repo(url):
        """追加有效仓库地址"""
        with open(OUTPUT_FILE, "a") as f:
            f.write(url + "\n")

    def fetch_repo():
        """拉取仓库列表"""
        with open(OUTPUT_FILE_TEMP, "w") as f:
            pass

        PER_PAGE = 100
        session = requests.Session()

        # 搜索普通仓库
        print("开始拉取所有普通仓库...")
        page = 1
        while True:
            print(f"==== 拉取第 {page} 页 ====")
            if github_api_sleep > 0:
                time.sleep(github_api_sleep)

            resp = session.get(
                f"{proxy_url}https://api.github.com/search/repositories",
                params={"q": "FnDepot in:name", "per_page": PER_PAGE, "page": page},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            if not items:
                break

            existing_repos = set()
            try:
                with open(OUTPUT_FILE_TEMP, "r") as f:
                    existing_repos = set(line.strip() for line in f if line.strip())
            except FileNotFoundError:
                pass

            for item in items:
                repo = item["full_name"]
                if repo not in existing_repos:
                    existing_repos.add(repo)
                    with open(OUTPUT_FILE_TEMP, "a") as f:
                        f.write(repo + "\n")

            page += 1

        # 搜索 fork 仓库
        print("开始拉取所有从https://github.com/EWEDLCM/FnDepot 仓库fork出来的仓库...")
        page = 1
        while True:
            print(f"==== 拉取第 {page} 页 ====")
            if github_api_sleep > 0:
                time.sleep(github_api_sleep)

            resp = session.get(
                f"{proxy_url}https://api.github.com/search/repositories",
                params={"q": "FnDepot in:name fork:true", "per_page": PER_PAGE, "page": page},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            if not items:
                break

            existing_repos = set()
            try:
                with open(OUTPUT_FILE_TEMP, "r") as f:
                    existing_repos = set(line.strip() for line in f if line.strip())
            except FileNotFoundError:
                pass

            for item in items:
                repo = item["full_name"]
                if repo not in existing_repos:
                    existing_repos.add(repo)
                    with open(OUTPUT_FILE_TEMP, "a") as f:
                        f.write(repo + "\n")

            page += 1

    def check_and_add_repo():
        """检查并添加有效仓库"""
        print("开始检查并添加有效仓库...")

        with open(OUTPUT_FILE_TEMP, "r") as f:
            repo_list = [line.strip() for line in f if line.strip()]

        # 黑名单过滤
        if BLACKLIST:
            print("应用黑名单过滤...")
            filtered_list = []
            for repo in repo_list:
                excluded = False
                for blacklist_item in BLACKLIST:
                    regex_pattern = re.escape(blacklist_item).replace(r"\*", ".*")
                    if re.fullmatch(regex_pattern, repo):
                        print(f"  ✔ 移除黑名单仓库 {blacklist_item}")
                        excluded = True
                        break
                if not excluded:
                    filtered_list.append(repo)
            repo_list = filtered_list

            with open(OUTPUT_FILE_TEMP, "w") as f:
                for repo in repo_list:
                    f.write(repo + "\n")

        # 白名单添加
        if WHITELIST:
            print("添加白名单仓库...")
            existing = set(repo_list)
            for whitelist_item in WHITELIST:
                if whitelist_item not in existing:
                    repo_list.append(whitelist_item)
                    with open(OUTPUT_FILE_TEMP, "a") as f:
                        f.write(whitelist_item + "\n")
                    print(f"  ✔ 添加白名单仓库 {whitelist_item}")

        for repo in repo_list:
            if check_repo(repo):
                add_repo(f"https://github.com/{repo}")
            else:
                print(f"  ✘ 仓库 {repo} 无效")

    # 主流程
    fetch_repo()
    check_and_add_repo()

    print("===== 带 fnpack.json 的 FnDepot 仓库 =====")
    try:
        with open(OUTPUT_FILE, "r") as f:
            sys.stdout.write(f.read())
    except FileNotFoundError:
        print("(无有效仓库)")


if __name__ == "__main__":
    main()
