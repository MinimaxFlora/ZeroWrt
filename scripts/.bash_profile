# .bash_profile

# 加载用户配置
if [ -f ~/.bashrc ]; then
	. ~/.bashrc
fi

# 添加用户程序目录到 PATH
PATH=$PATH:$HOME/bin
export PATH
