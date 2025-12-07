#!/bin/bash

# Disabilita in .bashrc (se esiste)
if [ -f ~/.bashrc ]; then
    sed -i 's/^\(export PYENV_ROOT\)/# \1/' ~/.bashrc
    sed -i 's/^\(.*PYENV_ROOT.*PATH\)/# \1/' ~/.bashrc
    sed -i 's/^\(eval.*pyenv init\)/# \1/' ~/.bashrc
    sed -i 's/^\(eval.*pyenv virtualenv-init\)/# \1/' ~/.bashrc
fi

# Disabilita in .zshrc (se esiste)
if [ -f ~/.zshrc ]; then
    sed -i 's/^#*eval.*pyenv init -/# eval "$(pyenv init -)"/' ~/.zshrc
    sed -i 's/^#*eval.*pyenv virtualenv-init -/# eval "$(pyenv virtualenv-init -)"/' ~/.zshrc
fi

# Ricarica entrambi
source ~/.bashrc 2>/dev/null || true
source ~/.zshrc 2>/dev/null || true

echo "Pyenv disabilitato in tutti i file di configurazione"
