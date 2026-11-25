# .bashrc

# 用户别名和函数
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# 彩色输出
export LS_OPTIONS='--color=auto'
eval "$(dircolors)"
alias ls='ls $LS_OPTIONS'
alias ll='ls $LS_OPTIONS -l'

# 加载全局配置
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi
