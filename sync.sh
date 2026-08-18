#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Uso: $0 \"mensagem de commit\""
  exit 1
fi

commit_msg="$1"
req_file="requirements.txt"

# Lista recomendada de pacotes para busca web e ciência de dados
packages=(
  beautifulsoup4
  playwright
  selenium
  numpy
  scipy
  scikit-learn
  pandas
  openpyxl
  xlrd
  tavily-python
  requests
  google-genai
  google-generativeai
)

added=false

# Cria requirements.txt se não existir
if [ ! -f "$req_file" ]; then
  touch "$req_file"
fi

for pkg in "${packages[@]}"; do
  if ! grep -Fxq "$pkg" "$req_file"; then
    echo "$pkg" >> "$req_file"
    echo "Added $pkg to $req_file"
    added=true
  fi
done

if [ "$added" = true ]; then
  git add "$req_file"
  # Inclui trailer Co-authored-by conforme política do projeto
  full_msg="$commit_msg\n\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
  git commit -m "$full_msg" || { echo "git commit falhou ou sem mudanças"; exit 1; }
  echo "requirements.txt atualizado e commitado"
else
  echo "Nenhuma alteração necessária em $req_file"
fi
