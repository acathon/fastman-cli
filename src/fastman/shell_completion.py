"""
Shell completion generators for Fastman CLI.

Commands and per-command options are pulled from `COMMAND_REGISTRY` at
generation time, so adding a new `@register`'d Command is enough — no
edits in this file required.

Option *value* enums (e.g. `--pattern=feature|api|layer`) are still hand-
maintained below since the signature DSL has no slot for choice lists.
"""
from typing import Dict, Iterable, List, Tuple

from .commands.base import COMMAND_REGISTRY


# Per-option suggested values. Add an entry when a new enum-style option is
# introduced; commands not listed here just get plain `--name=` completion.
OPTION_VALUES: Dict[str, List[str]] = {
    "pattern": ["feature", "api", "layer"],
    "package": ["uv", "poetry", "pipenv", "pip"],
    "database": ["sqlite", "postgresql", "mysql", "oracle", "firebase"],
    "style": ["rest", "graphql"],
    "type": ["jwt", "oauth", "keycloak", "passkey"],
    "provider": ["smtp", "sendgrid", "mailgun", "ses"],
    "method": ["GET", "POST", "PUT", "PATCH", "DELETE"],
    "source": ["develop", "staging", "production"],
}


def _registry_snapshot() -> List[Tuple[str, str, List[str], List[str]]]:
    """Return [(command_name, description, options, flags), ...] sorted by name.

    Used by every shell-specific generator below — pulls everything from the
    live registry so the static lists this file used to maintain are gone.
    """
    snapshot = []
    for name, cls in sorted(COMMAND_REGISTRY.items()):
        _, _, options, flags = cls.parse_signature()
        option_names = sorted(opt["name"] for opt in options)
        flag_names = sorted(flg["name"] for flg in flags)
        snapshot.append((name, cls.description or "", option_names, flag_names))
    return snapshot


def _all_command_names() -> List[str]:
    return sorted(COMMAND_REGISTRY.keys())


class ShellCompletion:
    """Generate shell completion scripts for Fastman CLI"""

    @classmethod
    def generate_bash(cls) -> str:
        snapshot = _registry_snapshot()
        commands_str = " ".join(name for name, _, _, _ in snapshot)

        # Per-command opts case branches
        opt_branches: List[str] = []
        for name, _, options, flags in snapshot:
            tokens = [f"--{o}=" for o in options] + [f"--{f}" for f in flags] + ["--help"]
            opt_branches.append(f"        {name})\n            opts=\"{' '.join(tokens)}\"\n            ;;")

        # Per-option value cases
        value_cases: List[str] = []
        for opt_name, values in OPTION_VALUES.items():
            value_cases.append(
                f'        --{opt_name})\n'
                f'            COMPREPLY=( $(compgen -W "{" ".join(values)}" -- "${{cur}}") )\n'
                f'            return 0\n'
                f'            ;;'
            )

        script = f'''#!/bin/bash
# Fastman CLI Bash Completion (auto-generated from COMMAND_REGISTRY).
# Source this file: source /path/to/fastman-completion.bash

_fastman_completions() {{
    local cur prev opts
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    local commands="{commands_str}"

    case "${{COMP_WORDS[1]}}" in
{chr(10).join(opt_branches)}
        *)
            opts="--help"
            ;;
    esac

    case "${{prev}}" in
{chr(10).join(value_cases)}
    esac

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
        snapshot = _registry_snapshot()

        commands_block = "\n".join(
            f'        "{name}:{desc.replace(chr(34), "")}"' for name, desc, _, _ in snapshot
        )

        case_branches: List[str] = []
        for name, _, options, flags in snapshot:
            lines = []
            for opt in options:
                if opt in OPTION_VALUES:
                    choices = " ".join(OPTION_VALUES[opt])
                    lines.append(f"                '--{opt}=[{opt}]:{opt}:({choices})'")
                else:
                    lines.append(f"                '--{opt}=[{opt}]'")
            for flg in flags:
                lines.append(f"                '--{flg}[{flg}]'")
            if not lines:
                continue
            branch_body = " \\\n".join(lines)
            case_branches.append(
                f"        {name})\n            _arguments \\\n{branch_body}\n            ;;"
            )

        script = f'''#!/bin/zsh
# Fastman CLI Zsh Completion (auto-generated)
# Place in $fpath (e.g. ~/.zsh/completions/_fastman)

#compdef fastman

_fastman() {{
    local curcontext="$curcontext" state line
    typeset -A opt_args

    local -a commands
    commands=(
{commands_block}
    )

    _arguments -C \\
        '(-h --help)'{{-h,--help}}'[Show help message]' \\
        '(-v --version)'{{-v,--version}}'[Show version]' \\
        '*: :->command' && return 0

    case "$line[1]" in
{chr(10).join(case_branches)}
    esac
}}

_fastman "$@"
'''
        return script

    @classmethod
    def generate_fish(cls) -> str:
        snapshot = _registry_snapshot()

        command_lines = [
            f'complete -c fastman -n "__fish_use_subcommand" -a "{name}" -d "{desc}"'
            for name, desc, _, _ in snapshot
        ]

        option_lines: List[str] = []
        for name, _, options, flags in snapshot:
            for opt in options:
                base = f'complete -c fastman -n "__fish_seen_subcommand_from {name}" -l {opt} -d "{opt}"'
                if opt in OPTION_VALUES:
                    base += f' -a "{" ".join(OPTION_VALUES[opt])}"'
                option_lines.append(base)
            for flg in flags:
                option_lines.append(
                    f'complete -c fastman -n "__fish_seen_subcommand_from {name}" -l {flg} -d "{flg}"'
                )

        script = f'''# Fastman CLI Fish Completion (auto-generated)
# Place in ~/.config/fish/completions/fastman.fish

# Disable file completions for fastman
complete -c fastman -f

# Global options
complete -c fastman -s h -l help -d "Show help message"
complete -c fastman -s v -l version -d "Show version"

# Commands
{chr(10).join(command_lines)}

# Command-specific options
{chr(10).join(option_lines)}
'''
        return script

    @classmethod
    def generate_powershell(cls) -> str:
        snapshot = _registry_snapshot()
        commands_list = "', '".join(name for name, _, _, _ in snapshot)

        # Build the per-command hashtable entries
        completion_lines: List[str] = []
        for name, _, options, flags in snapshot:
            tokens = [f"--{o}=" for o in options] + [f"--{f}" for f in flags] + ["--help"]
            quoted = ", ".join(f"'{t}'" for t in tokens)
            completion_lines.append(f"    '{name}' = @({quoted})")

        # Option-value hashtable
        value_lines: List[str] = []
        for opt, values in OPTION_VALUES.items():
            quoted = ", ".join(f"'{v}'" for v in values)
            value_lines.append(f"    '--{opt}=' = @({quoted})")

        script = f'''
# Fastman CLI PowerShell Completion (auto-generated)
# Add to your PowerShell profile: notepad $PROFILE
# Or run: . /path/to/fastman-completion.ps1

$fastmanCommands = @('{commands_list}')

$fastmanCompletions = @{{
{chr(10).join(completion_lines)}
}}

$fastmanOptionValues = @{{
{chr(10).join(value_lines)}
}}

Register-ArgumentCompleter -Native -CommandName fastman -ScriptBlock {{
    param($wordToComplete, $commandAst, $cursorPosition)

    $line = $commandAst.ToString()
    $parts = $line -split '\\s+'
    $command = $parts[1]
    $currentWord = $parts[-1]

    if ($parts.Length -le 2 -and -not $currentWord.StartsWith('-')) {{
        $fastmanCommands | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }}
        return
    }}

    if ($fastmanCompletions.ContainsKey($command)) {{
        $fastmanCompletions[$command] | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }}
    }}

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


def get_completion_install_instructions() -> str:
    """Get installation instructions for shell completions"""
    return '''
╔════════════════════════════════════════════════════════════════════╗
║              Shell Completion Installation Guide                   ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  BASH:                                                             ║
║  ───────────────────────────────────────────────────────────────── ║
║  1. fastman completion bash > ~/.fastman-completion.bash           ║
║  2. echo 'source ~/.fastman-completion.bash' >> ~/.bashrc          ║
║  3. source ~/.bashrc                                               ║
║                                                                    ║
║  ZSH:                                                              ║
║  ───────────────────────────────────────────────────────────────── ║
║  1. mkdir -p ~/.zsh/completions                                    ║
║  2. fastman completion zsh > ~/.zsh/completions/_fastman           ║
║  3. Ensure fpath includes ~/.zsh/completions                       ║
║                                                                    ║
║  FISH:                                                             ║
║  ───────────────────────────────────────────────────────────────── ║
║  1. fastman completion fish > ~/.config/fish/completions/fastman.fish
║  2. Restart fish or source the file                                ║
║                                                                    ║
║  POWERSHELL:                                                       ║
║  ───────────────────────────────────────────────────────────────── ║
║  1. fastman completion powershell > ~/fastman-completion.ps1       ║
║  2. Add `. ~/fastman-completion.ps1` to your $PROFILE              ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
'''
