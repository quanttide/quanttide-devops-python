"""
Migrate repository from Coding DevOps to GitHub.
"""
import os

from coding_devops_sdk.openapi import coding_openapi_client
from coding_devops_sdk.config import settings as coding_settings
from github import Github
import semantic_version
from git import Repo
import tempfile
import subprocess

from quanttide_devops.config import settings


g = Github(settings.GITHUB_ACCESS_TOKEN)


def sync_releases():
    """
    Sync releases from Coding DevOps to GitHub
    :return:
    """
    # Coding
    coding_releases = coding_openapi_client.describe_git_releases(
        depot_id=coding_openapi_client.get_depot_id_by_name(depot_name=coding_settings.DEFAULT_DEPOT_NAME,
                                                            project_name=coding_settings.DEFAULT_PROJECT_NAME),
        PageSize=100,
    )
    coding_releases = sorted(coding_releases, key=lambda x: semantic_version.Version(x['TagName']))
    # GitHub
    # Note: suppose the repo name is same.
    repo = g.get_repo(f"{settings.GITHUB_ORGANIZATION}/{coding_settings.DEFAULT_DEPOT_NAME}")
    for release in coding_releases:
        repo.create_git_release(release['TagName'], release['Title'], release['Body'],
                                prerelease=release['Pre'])
    return coding_releases


def publish_to_pypi():
    """

    :return:
    """
    coding_releases = coding_openapi_client.describe_git_releases(
        depot_id=coding_openapi_client.get_depot_id_by_name(depot_name=coding_settings.DEFAULT_DEPOT_NAME,
                                                            project_name=coding_settings.DEFAULT_PROJECT_NAME),
        PageSize=100,
    )
    coding_releases = sorted(coding_releases, key=lambda x: semantic_version.Version(x['TagName']))

    # 发布
    for release in coding_releases:
        # 检出版本
        version = release['TagName']
        if semantic_version.Version(version) < semantic_version.Version(settings.MIN_VERSION):
            continue
        print(f"开始发布v{version}")
        # 本地仓库
        tmp_dir = tempfile.TemporaryDirectory()
        os.chdir(tmp_dir.name)
        local_repo = Repo(settings.REPO_LOCAL_PATH).clone(path=tmp_dir.name)
        local_repo.git.checkout(version)
        # 上传
        status = subprocess.run(['python3', '-m', 'build'])
        if status.returncode:
            continue
        status2 = subprocess.run(['python3', '-m', 'pip', 'install', '--upgrade', 'twine'])
        if status2.returncode:
            continue
        status3 = subprocess.run(['python3', '-m', 'twine', 'upload', 'dist/*'])
        if status3.returncode:
            continue


def main():
    # sync_releases()
    publish_to_pypi()


if __name__ == "__main__":
    main()
