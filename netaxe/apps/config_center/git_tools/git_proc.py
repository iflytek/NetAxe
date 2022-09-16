import os
from datetime import datetime

from git import Actor
from git.repo import Repo
from pydriller import Repository
from netboost.settings import BASE_DIR
repo_path = os.path.join(BASE_DIR, 'media/device_config')
repo = Repo(path=repo_path)


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
        print(commit)
        repo.remote('origin').push()
        o = repo.remotes.origin
        o.pull()
        return commit, changedFiles, untracked_files
    return '', '', ''


# 查看单个提交中包含的文件
def diff_config():
    # for commit in Repository(repo_path, single='8b4ecd6090068003a3832c4c8a41217a7d3f1445').traverse_commits():
    for commit in Repository(repo_path, single='e2bf3906d1847a26a755333c5abc207d2a09b1ae').traverse_commits():
        for m in commit.modified_files:
            print(m.new_path)
            print(m.filename)
            print(m.change_type.name)


def get_all_commit():
    # commits_list = list(repo.iter_commits('master'))
    # return commits_list
    for commit in repo.iter_commits('master'):
        print(commit.author)
        print(commit.committer)
        print(commit.committed_date)
        print(commit.hexsha)
        print(commit.committed_datetime)


# 比较两个文件的差异
def diff_file():
    commits_list = list(repo.iter_commits())
    # print(commits_list)
    a_commit = commits_list[1]
    b_commit = commits_list[0]
    print(a_commit.message, b_commit.message)
    print(a_commit.committed_datetime)
    print(b_commit.committed_datetime)
    # res = repo.git.diff(a_commit, b_commit, 'git_proc.py')
    # print(res)
    for commit in Repository(repo_path, from_commit=a_commit, to_commit=b_commit,
                             filepath='current-configuration/10.254.8.45/hp_comware-10.254.8.45.txt').traverse_commits():
        for m in commit.modified_files:
            # print(m.filename)
            if m.filename == 'hp_comware-10.254.8.45.txt':
                print(m.diff_parsed)
                print(m.diff_parsed.keys())
                # print(m.source_code)
                print(m.source_code_before)


if __name__ == '__main__':

    diff_config()
