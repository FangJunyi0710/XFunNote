cd "$(dirname "$0")"
cd ..

scripts/project_info.py tree | 
scripts/replace.py ./README.md -b $'<!-- begin project tree -->\n```\n' -e $'```\n<!-- end project tree -->'

scripts/project_info.py mermaid | 
scripts/replace.py ./README.md -b $'<!-- begin dependence graph -->\n```mermaid\n' -e $'```\n<!-- end dependence graph -->'
