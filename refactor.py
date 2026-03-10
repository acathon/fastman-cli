import re

with open(r'c:\laragon\www\wip\fastman-cli\src\fastman\commands\project.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add context manager
handle_start = """        Output.banner(__version__)
        Output.section("Creating Project", f"{name} ({pattern} pattern with {database}{' + GraphQL' if graphql else ''})")
        
        with Output.run_progress(f"Scaffolding {name}...") as (progress, task_id):
            if progress: progress.update(task_id, description="Setting up project directories...", advance=10)"""

content = re.sub(
    r'        Output\.banner\(__version__\)\n        Output\.section\("Creating Project".*?\n        \n        Output\.task\("Setting up project structure".*?\n',
    handle_start + '\n',
    content,
    flags=re.DOTALL
)

# 2. Remove directory logging
content = content.replace('            Output.directory_created(dir_path)', '')

# 3. Add progress update for templates
template_start = """        if progress: progress.update(task_id, description="Generating core templates...", advance=20)
        for file_path, template in files.items():"""

content = re.sub(
    r'        Output\.line\(\)\n        for file_path, template in files\.items\(\):',
    template_start,
    content
)

# 4. Remove file logging
content = content.replace('            Output.file_created(file_path)', '')

# 5. Fix _initialize_package_manager call
pkg_call_start = """        dependencies = self._get_database_dependencies(database, graphql, minimal)
        self._initialize_package_manager(package_manager, dependencies, name, project_path, progress, task_id)

        Output.line()"""

content = re.sub(
    r'        dependencies = self\._get_database_dependencies.*?\n        self\._initialize_package_manager.*?\n\n        Output\.line\(\)',
    pkg_call_start,
    content,
    flags=re.DOTALL
)

# 6. Refactor _initialize_package_manager signature
content = content.replace(
    'def _initialize_package_manager(self, package_manager: str, dependencies: list, project_name: str, cwd: Path = None):',
    'def _initialize_package_manager(self, package_manager: str, dependencies: list, project_name: str, cwd: Path = None, progress=None, task_id=None):'
)

# 7. Add progress updates into package manager
content = re.sub(
    r'        Output\.section\("Initializing Package Manager", f"Using \{package_manager\}"\)',
    '        if progress: progress.update(task_id, description=f"Initializing {package_manager}...", advance=10)',
    content
)

# 8. Hide Output.task logs
content = re.sub(r' +Output\.task.*?status="in progress".*?\n', '', content)
content = re.sub(
    r' +Output\.task.*?status="done".*?\n', 
    '                if progress: progress.update(task_id, description="Virtual environment created", advance=50)\n', 
    content
)

# Remove manual pipenv output task
content = re.sub(r' +Output\.task\("Installing pipenv".*?\n', '', content)

with open(r'c:\laragon\www\wip\fastman-cli\src\fastman\commands\project.py', 'w', encoding='utf-8') as f:
    f.write(content)
