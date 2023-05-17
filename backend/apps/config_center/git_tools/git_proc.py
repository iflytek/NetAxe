import os
from datetime import datetime

from git import Actor
from git import Repo
from pydriller import Repository
from netaxe.settings import BASE_DIR
repo_path = os.path.join(BASE_DIR, 'media/device_config')

if not os.path.exists(os.path.join(BASE_DIR, 'media/device_config')):
    os.makedirs(os.path.join(BASE_DIR, 'media/device_config'))
    repo = Repo.init(os.path.join(repo_path))

try:
    repo = Repo(path=repo_path)
except:
    repo = Repo.init(os.path.join(repo_path))


class ConfigGit:
    def __init__(self):
        self.repo = Repo(path=repo_path)

    # 获取所有的提交
    def get_commit(self, commit=None):
        """
        {
          label: "Everybody's Got Something to Hide Except Me and My Monkey",
          value: 'song0',
          disabled: true
        },
        :param commit:
        :return:
        """
        result = []
        if commit is None:
            for m in repo.iter_commits():
                _data = {
                    # 'author': m.author,
                    'label': m.committed_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    # 'message': m.message,
                    'value': m.hexsha,
                }
                result.append(_data)
        return result

    # 获取单个文件在commit范围中的变化
    def get_commit_by_file(self, **kwargs):
        file = kwargs['file']
        from_commit = kwargs['from_commit']
        to_commit = kwargs['to_commit']
        # commits_list = list(repo.iter_commits())
        # b_commit = commits_list[1]
        # res = repo.git.diff(a_commit, b_commit, 'git_proc.py')
        # print(res)
        result = {
            'new_str': '无变更',
            'old_str': '无变更'
        }
        for commit in Repository(repo_path, from_commit=from_commit, to_commit=to_commit,
                                 filepath=file).traverse_commits():
            for m in commit.modified_files:
                if m.filename == file.split('/')[-1]:
                    result['new_str'] = m.source_code if m.source_code is not None else ''
                    result['old_str'] = m.source_code_before if m.source_code_before is not None else ''
                    result['added_lines'] = m.added_lines
                    result['deleted_lines'] = m.deleted_lines
                    return result
        return result

    # 获取单个commit包含的变更文件
    def get_commit_detail(self, commit):
        result = []
        for commit in Repository(repo_path, single=commit).traverse_commits():
            for m in commit.modified_files:
                tmp = {
                    'label': m.filename,
                    'value': m.new_path
                }
                result.append(tmp)
        return result

    # 获取单个commit指定文件名的变更详情
    def get_commit_by_filename(self, commit, filename):
        result = {
            'new_str': '无变更',
            'old_str': '无变更'
        }
        for commit in Repository(repo_path, single=commit).traverse_commits():
            for m in commit.modified_files:
                if m.filename == filename.split('/')[-1]:
                    result['new_str'] = m.source_code if m.source_code is not None else ''
                    result['old_str'] = m.source_code_before if m.source_code_before is not None else ''
                    result['added_lines'] = m.added_lines
                    result['deleted_lines'] = m.deleted_lines
                    # print(m.diff_parsed)
                    return result
        return result


def push_file():
    # 本地更改的文件
    log_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    files = []
    changedFiles = [item.a_path for item in repo.index.diff(None)]
    files += changedFiles
    # 未跟踪的文件
    untracked_files = repo.untracked_files
    files += untracked_files
    if files:
        for file in files:
            print(file)
            repo.index.add(os.path.join(repo.working_tree_dir, file))
        author = Actor("netaxe", "netaxe@example.com")
        committer = Actor(log_time, "netops@example.com")
        commit = repo.index.commit(f"automation commit by {log_time}", author=author, committer=committer)
        if repo.remotes:
            for _origin in repo.remotes:
                repo.remote(_origin).push()
                o = repo.remotes.origin
                o.pull()
        return commit, changedFiles, untracked_files
    return '', '', ''


