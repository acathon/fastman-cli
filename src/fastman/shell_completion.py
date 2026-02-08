"""
Shell completion generators for Fastman CLI.
Supports Bash, Zsh, Fish, and PowerShell.
"""
from pathlib import Path
from typing import Dict, List


class ShellCompletion:
    """Generate shell completion scripts for Fastman CLI"""
    
    # List of all Fastman commands
    COMMANDS = [
        # Project commands
        'new', 'init',
        # Server commands
        'serve',
        # Scaffold commands
        'make:feature', 'make:api', 'make:websocket', 'make:controller',
        'make:model', 'make:service', 'make:middleware', 'make:dependency',
        'make:test', 'make:seeder', 'make:factory', 'make:exception',
        'make:repository', 'make:command', 'make:schema',
        # Database commands
        'make:migration', 'database:migrate', 'migrate:rollback', 'migrate:reset',
        'migrate:status', 'database:seed',
        # Auth commands
        'install:auth',
        # Route commands
        'route:list',
        # Utility commands
        'tinker', 'generate:key', 'config:cache', 'config:clear',
        'cache:clear', 'package:import', 'package:list', 'package:remove',
        'list', 'version', 'docs', 'inspect', 'optimize', 'build', 'activate',
        'completion',
    ]
    
    # Options for each command
    COMMAND_OPTIONS: Dict[str, List[str]] = {
        'new': ['--minimal', '--pattern=', '--package=', '--database='],
        'make:feature': ['--crud'],
        'make:api': ['--style='],
        'make:model': ['--table='],
        'make:migration': [],
        'migrate:rollback': ['--steps='],
        'database:seed': ['--class='],
        'install:auth': ['--type='],
        'route:list': ['--path=', '--method='],
        'serve': ['--host=', '--port=', '--reload', '--no-reload'],
        'build': ['--docker'],
        'activate': ['--create-script'],
        'package:import': [],
        'package:remove': [],
    }
    
    # Global options available for all commands
    GLOBAL_OPTIONS = ['--help', '-h', '--version', '-v']
    
    @classmethod
    def generate_bash(cls) -> str:
        """Generate Bash completion script"""
        commands_str = ' '.join(cls.COMMANDS)
        
        script = f'''#!/bin/bash
# Fastman CLI Bash Completion
# Source this file: source /path/to/fastman-completion.bash

_fastman_completions() {{
    local cur prev opts
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    
    # Main commands
    local commands="{commands_str}"
    
    # Options for specific commands
    case "${{COMP_WORDS[1]}}" in
        new)
            opts="--minimal --pattern= --package= --database= --help"
            ;;
        make:feature)
            opts="--crud --help"
            ;;
        make:api)
            opts="--style= --help"
            ;;
        make:model)
            opts="--table= --help"
            ;;
        migrate:rollback)
            opts="--steps= --help"
            ;;
        database:seed)
            opts="--class= --help"
            ;;
        install:auth)
            opts="--type= --help"
            ;;
        route:list)
            opts="--path= --method= --help"
            ;;
        serve)
            opts="--host= --port= --reload --no-reload --help"
            ;;
        build)
            opts="--docker --help"
            ;;
        activate)
            opts="--create-script --help"
            ;;
        *)
            opts="--help"
            ;;
    esac
    
    # Handle option values
    case "${{prev}}" in
        --pattern)
            COMPREPLY=( $(compgen -W "feature api layer" -- "${{cur}}") )
            return 0
            ;;
        --package)
            COMPREPLY=( $(compgen -W "uv poetry pipenv pip" -- "${{cur}}") )
            return 0
            ;;
        --database)
            COMPREPLY=( $(compgen -W "sqlite postgresql mysql oracle firebase" -- "${{cur}}") )
            return 0
            ;;
        --style)
            COMPREPLY=( $(compgen -W "rest graphql" -- "${{cur}}") )
            return 0
            ;;
        --type)
            COMPREPLY=( $(compgen -W "jwt oauth keycloak" -- "${{cur}}") )
            return 0
            ;;
        --method)
            COMPREPLY=( $(compgen -W "GET POST PUT PATCH DELETE" -- "${{cur}}") )
            return 0
            ;;
    esac
    
    # Complete commands or options
    if [[ ${{cur}} == -* ]]; then
        COMPREPLY=( $(compgen -W "${{opts}}" -- "${{cur}}") )
    else
        COMPREPLY=( $(compgen -W "${{commands}}" -- "${{cur}}") )
    fi
}}

complete -F _fastman_completions fastman
'''
        return script
    
    @classmethod
    def generate_zsh(cls) -> str:
        """Generate Zsh completion script"""
        commands_str = ' '.join(cls.COMMANDS)
        
        script = f'''#!/bin/zsh
# Fastman CLI Zsh Completion
# Place in $fpath (e.g., /usr/local/share/zsh/site-functions/ or ~/.zsh/completions/)
# Name: _fastman

#compdef fastman

_fastman() {{
    local curcontext="$curcontext" state line
    typeset -A opt_args
    
    local -a commands
    commands=(
{chr(10).join([f'        "{cmd}:{cls._get_command_description(cmd)}"' for cmd in cls.COMMANDS])}
    )
    
    _arguments -C \\
        '(-h --help)'{{-h,--help}}'[Show help message]' \\
        '(-v --version)'{{-v,--version}}'[Show version]' \\
        '*: :->command' && return 0
    
    case "$line[1]" in
        new)
            _arguments \\
                '--minimal[Create minimal project]' \\
                '--pattern=[Architecture pattern]:pattern:(feature api layer)' \\
                '--package=[Package manager]:package:(uv poetry pipenv pip)' \\
                '--database=[Database type]:database:(sqlite postgresql mysql oracle firebase)'
            ;;
        make:feature)
            _arguments '--crud[Generate CRUD endpoints]'
            ;;
        make:api)
            _arguments '--style=[API style]:style:(rest graphql)'
            ;;
        make:model)
            _arguments '--table=[Custom table name]'
            ;;
        migrate:rollback)
            _arguments '--steps=[Number of migrations to rollback]'
            ;;
        database:seed)
            _arguments '--class=[Seeder class name]'
            ;;
        install:auth)
            _arguments '--type=[Auth type]:type:(jwt oauth keycloak)'
            ;;
        route:list)
            _arguments \\
                '--path=[Filter by path]' \\
                '--method=[Filter by HTTP method]:method:(GET POST PUT PATCH DELETE)'
            ;;
        serve)
            _arguments \\
                '--host=[Host to bind to]' \\
                '--port=[Port to bind to]' \\
                '--reload[Enable auto-reload]' \\
                '--no-reload[Disable auto-reload]'
            ;;
        build)
            _arguments '--docker[Build Docker image]'
            ;;
        activate)
            _arguments '--create-script[Create activation helper script]'
            ;;
    esac
}}

_fastman "$@"
'''
        return script
    
    @classmethod
    def generate_fish(cls) -> str:
        """Generate Fish completion script"""
        commands_str = ' '.join(cls.COMMANDS)
        
        script = f'''# Fastman CLI Fish Completion
# Place in ~/.config/fish/completions/fastman.fish

# Disable file completions for fastman
complete -c fastman -f

# Global options
complete -c fastman -s h -l help -d "Show help message"
complete -c fastman -s v -l version -d "Show version"

# Commands
{chr(10).join([f'complete -c fastman -n "__fish_use_subcommand" -a "{cmd}" -d "{cls._get_command_description(cmd)}"' for cmd in cls.COMMANDS])}

# Command-specific completions
complete -c fastman -n "__fish_seen_subcommand_from new" -l minimal -d "Create minimal project"
complete -c fastman -n "__fish_seen_subcommand_from new" -l pattern -d "Architecture pattern" -a "feature api layer"
complete -c fastman -n "__fish_seen_subcommand_from new" -l package -d "Package manager" -a "uv poetry pipenv pip"
complete -c fastman -n "__fish_seen_subcommand_from new" -l database -d "Database type" -a "sqlite postgresql mysql oracle firebase"

complete -c fastman -n "__fish_seen_subcommand_from make:feature" -l crud -d "Generate CRUD endpoints"

complete -c fastman -n "__fish_seen_subcommand_from make:api" -l style -d "API style" -a "rest graphql"

complete -c fastman -n "__fish_seen_subcommand_from make:model" -l table -d "Custom table name"

complete -c fastman -n "__fish_seen_subcommand_from migrate:rollback" -l steps -d "Number of migrations"

complete -c fastman -n "__fish_seen_subcommand_from database:seed" -l class -d "Seeder class name"

complete -c fastman -n "__fish_seen_subcommand_from install:auth" -l type -d "Auth type" -a "jwt oauth keycloak"

complete -c fastman -n "__fish_seen_subcommand_from route:list" -l path -d "Filter by path"
complete -c fastman -n "__fish_seen_subcommand_from route:list" -l method -d "Filter by method" -a "GET POST PUT PATCH DELETE"

complete -c fastman -n "__fish_seen_subcommand_from serve" -l host -d "Host to bind"
complete -c fastman -n "__fish_seen_subcommand_from serve" -l port -d "Port to bind"
complete -c fastman -n "__fish_seen_subcommand_from serve" -l reload -d "Enable auto-reload"
complete -c fastman -n "__fish_seen_subcommand_from serve" -l no-reload -d "Disable auto-reload"

complete -c fastman -n "__fish_seen_subcommand_from build" -l docker -d "Build Docker image"

complete -c fastman -n "__fish_seen_subcommand_from activate" -l create-script -d "Create activation script"
'''
        return script
    
    @classmethod
    def generate_powershell(cls) -> str:
        """Generate PowerShell completion script"""
        commands_list = "', '".join(cls.COMMANDS)
        
        script = f'''
# Fastman CLI PowerShell Completion
# Add to your PowerShell profile: notepad $PROFILE
# Or run: . /path/to/fastman-completion.ps1

$fastmanCommands = @('{commands_list}')

$fastmanCompletions = {{
    'new' = @('--minimal', '--pattern=', '--package=', '--database=', '--help')
    'make:feature' = @('--crud', '--help')
    'make:api' = @('--style=', '--help')
    'make:model' = @('--table=', '--help')
    'migrate:rollback' = @('--steps=', '--help')
    'database:seed' = @('--class=', '--help')
    'install:auth' = @('--type=', '--help')
    'route:list' = @('--path=', '--method=', '--help')
    'serve' = @('--host=', '--port=', '--reload', '--no-reload', '--help')
    'build' = @('--docker', '--help')
    'activate' = @('--create-script', '--help')
}}

$fastmanOptionValues = {{
    '--pattern=' = @('feature', 'api', 'layer')
    '--package=' = @('uv', 'poetry', 'pipenv', 'pip')
    '--database=' = @('sqlite', 'postgresql', 'mysql', 'oracle', 'firebase')
    '--style=' = @('rest', 'graphql')
    '--type=' = @('jwt', 'oauth', 'keycloak')
    '--method=' = @('GET', 'POST', 'PUT', 'PATCH', 'DELETE')
}}

Register-ArgumentCompleter -Native -CommandName fastman -ScriptBlock {{
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $line = $commandAst.ToString()
    $parts = $line -split '\\s+'
    $command = $parts[1]
    $currentWord = $parts[-1]
    
    # Complete commands
    if ($parts.Length -le 2 -and -not $currentWord.StartsWith('-')) {{
        $fastmanCommands | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }}
        return
    }}
    
    # Complete options for known commands
    if ($fastmanCompletions.ContainsKey($command)) {{
        $fastmanCompletions[$command] | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }}
    }}
    
    # Complete option values
    foreach ($opt in $fastmanOptionValues.Keys) {{
        if ($line -match "$opt([^\\s]+)") {{
            $valuePrefix = $Matches[1]
            $fastmanOptionValues[$opt] | Where-Object {{ $_ -like "$valuePrefix*" }} | ForEach-Object {{
                [System.Management.Automation.CompletionResult]::new("$opt$_", $_, 'ParameterValue', $_)
            }}
        }}
    }}
}}
'''
        return script
    
    @classmethod
    def _get_command_description(cls, cmd: str) -> str:
        """Get description for a command"""
        descriptions = {
            'new': 'Create a new FastAPI project',
            'init': 'Initialize Fastman in existing project',
            'serve': 'Start development server',
            'make:feature': 'Create vertical slice feature',
            'make:api': 'Create API endpoint',
            'make:websocket': 'Create WebSocket endpoint',
            'make:controller': 'Create controller class',
            'make:model': 'Create SQLAlchemy model',
            'make:service': 'Create service class',
            'make:middleware': 'Create middleware',
            'make:dependency': 'Create dependency',
            'make:test': 'Create test file',
            'make:seeder': 'Create database seeder',
            'make:factory': 'Create model factory',
            'make:exception': 'Create custom exception',
            'make:repository': 'Create repository class',
            'make:command': 'Create custom CLI command',
            'make:schema': 'Create Pydantic schema',
            'make:migration': 'Create database migration',
            'database:migrate': 'Run database migrations',
            'migrate:rollback': 'Rollback migrations',
            'migrate:reset': 'Reset all migrations',
            'migrate:status': 'Check migration status',
            'database:seed': 'Run database seeders',
            'install:auth': 'Install authentication system',
            'route:list': 'List all API routes',
            'tinker': 'Interactive shell',
            'generate:key': 'Generate secret key',
            'config:cache': 'Cache configuration',
            'config:clear': 'Clear config cache',
            'cache:clear': 'Clear application cache',
            'package:import': 'Install Python package',
            'package:list': 'List installed packages',
            'package:remove': 'Remove Python package',
            'list': 'List all commands',
            'version': 'Show version',
            'docs': 'Open documentation',
            'inspect': 'Inspect code components',
            'optimize': 'Optimize project',
            'build': 'Build project',
            'activate': 'Show venv activation command',
            'completion': 'Generate shell completion script',
        }
        return descriptions.get(cmd, 'Fastman command')


def get_completion_install_instructions() -> str:
    """Get installation instructions for shell completions"""
    return '''
╔════════════════════════════════════════════════════════════════════╗
║              Shell Completion Installation Guide                   ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  BASH:                                                             ║
║  ───────────────────────────────────────────────────────────────── ║
║  1. Save completion script:                                        ║
║     fastman completion bash > ~/.fastman-completion.bash           ║
║                                                                    ║
║  2. Add to ~/.bashrc:                                              ║
║     echo 'source ~/.fastman-completion.bash' >> ~/.bashrc          ║
║                                                                    ║
║  3. Reload shell:                                                  ║
║     source ~/.bashrc                                               ║
║                                                                    ║
║  ZSH:                                                              ║
║  ───────────────────────────────────────────────────────────────── ║
║  1. Create completions directory:                                  ║
║     mkdir -p ~/.zsh/completions                                    ║
║                                                                    ║
║  2. Save completion script:                                        ║
║     fastman completion zsh > ~/.zsh/completions/_fastman          ║
║                                                                    ║
║  3. Add to ~/.zshrc (if not using compinit):                       ║
║     fpath+=(~/.zsh/completions)                                    ║
║                                                                    ║
║  FISH:                                                             ║
║  ───────────────────────────────────────────────────────────────── ║
║  1. Save completion script:                                        ║
║     fastman completion fish > ~/.config/fish/completions/fastman.fish
║                                                                    ║
║  2. Restart fish or run:                                           ║
║     source ~/.config/fish/completions/fastman.fish                 ║
║                                                                    ║
║  POWERSHELL:                                                       ║
║  ───────────────────────────────────────────────────────────────── ║
║  1. Save completion script:                                        ║
║     fastman completion powershell > ~/fastman-completion.ps1       ║
║                                                                    ║
║  2. Add to your profile:                                           ║
║     notepad $PROFILE                                               ║
║     # Add: . ~/fastman-completion.ps1                              ║
║                                                                    ║
║  3. Or run directly:                                               ║
║     . ~/fastman-completion.ps1                                     ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
'''
