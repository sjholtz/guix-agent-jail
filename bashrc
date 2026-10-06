# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# This file gets copied into /tmp/guix-agent-home/.bashrc when the
# '~/bin/guix-agent-jail' file is executed. Here it serves as the
# .bashrc for the Guix container that is spawned. Most of the contents
# mirror my personal .bashrc so that bash in the Guix container
# behaves as I am used to. Note that the prompt here is augmented with
# '[guix-agent]' so that it is clear what shell environment is
# executing.

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# don't put duplicate lines or lines starting with space in the history.
# See bash(1) for more options
export HISTCONTROL=ignoreboth:erasedups

# Don't wait for job termination notification:
set -o notify

# Don't use ^D to exit:
set -o ignoreeof

# Don't clobber files:
set -o noclobber

# append to the history file, don't overwrite it
shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=-1
HISTFILESIZE=-1

# Spell check the command line:
shopt -s cdspell

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# Set up use of backward and forward searching of history using up
# and down arrow keys, respectively:
bind '"\e[A":history-search-backward'
bind '"\e[B":history-search-forward'

# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
shopt -s globstar

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
#force_color_prompt=yes

# if [ -n "$force_color_prompt" ]; then
#     if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
# 	# We have color support; assume it's compliant with Ecma-48
# 	# (ISO/IEC-6429). (Lack of such support is extremely rare, and such
# 	# a case would tend to support setf rather than setaf.)
# 	color_prompt=yes
#     else
# 	color_prompt=
#     fi
# fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ [guix-agent]'
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ [guix-agent] '
fi
unset color_prompt force_color_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1 "
    ;;
*)
    ;;
esac

# enable color support of ls and also add handy aliases
if [ -x /bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
#     #alias dir='dir --color=auto'
#     #alias vdir='vdir --color=auto'

#     alias grep='grep --color=auto'
#     alias fgrep='fgrep --color=auto'
#     alias egrep='egrep --color=auto'
fi

# some more ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -Al'

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

export TERM=xterm-256color
# export FCEDIT="emacsclient -c"

# export EDITOR="emacsclient"
# export GIT_EDITOR="emacsclient"
# export VISUAL="emacsclient"
# export ALTERNATE_EDITOR="emacs -Q"

# # For dcraw_emu (and prehaps others...):
# export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"

# # For pa11y to run a development version of chrome to test for webpage accessibility issues:
# export CHROME_DEVEL_SANDBOX=/home/sholtz/.cache/puppeteer/chrome/linux-145.0.7632.77/chrome-linux64/chrome_sandbox

# Set default pager:
if [ "$TERM" == "dumb" ]
then
    export PAGER=""
else
    export PAGER=less
fi

umask 0022

# Bind ctrl-left to backward-word and ctrl-right to forward-word:
bind '"\e[1;5D" backward-word'
bind '"\e[1;5C" forward-word'

# Set environment for mitmdump
export http_proxy="http://127.0.0.1:#PORT#"
export https_proxy="http://127.0.0.1:#PORT#"
export HTTP_PROXY="http://127.0.0.1:#PORT#"
export HTTPS_PROXY="http://127.0.0.1:#PORT#"

MITM_CA="$HOME/.mitmproxy/mitmproxy-ca-cert.pem"
GUIX_CA="$GUIX_ENVIRONMENT/etc/ssl/certs/ca-certificates.crt"
cat "$GUIX_CA" "$MITM_CA" > /tmp/guix-agent-ca-bundle.pem
export SSL_CERT_FILE=/tmp/guix-agent-ca-bundle.pem
export REQUESTS_CA_BUNDLE=/tmp/guix-agent-ca-bundle.pem

# Set environment for API keys
export OPENAI_API_KEY="dummy_key"
export ANTHROPIC_API_KEY="dummy_key"
export OLLAMA_API_KEY="dummy-key"
export LANGSMITH_API_KEY="dummy-key"
export LANGSMITH_TRACING="true"
export LANGSMITH_PROJECT="lca-deepagents"
