# .bashrc

# 用户自定义别名和函数
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# 如果需要 ls 命令显示彩色输出，可以启用以下配置
export LS_OPTIONS='--color=auto'
eval "$(dircolors)"
alias ls='ls $LS_OPTIONS'
alias ll='ls $LS_OPTIONS -l'

# 加载系统全局 Bash 配置
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi
