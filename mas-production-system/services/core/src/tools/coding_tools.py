import subprocess

class CodingTools:
    def __init__(self):
        self.tools = {
            'git_clone': self.git_clone,
            'git_commit': self.git_commit,
            'compile_code': self.compile_code,
            'run_tests': self.run_tests,
        }
    
    def git_clone(self, repo_url):
        try:
            result = subprocess.run(['git', 'clone', repo_url], capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return str(e)
    
    def git_commit(self, message, files):
        try:
            subprocess.run(['git', 'add'] + files, check=True)
            result = subprocess.run(['git', 'commit', '-m', message], capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return str(e)
    
    def compile_code(self, code, language='python'):
        if language == 'python':
            try:
                compile(code, '<string>', 'exec')
                return "Compiled successfully"
            except SyntaxError as e:
                return str(e)
        # Add other languages
    
    def run_tests(self, test_code):
        try:
            result = subprocess.run(['python', '-c', test_code], capture_output=True, text=True, timeout=30)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return str(e)