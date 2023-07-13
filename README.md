# ClaudeWeb
一个基于 Python 用于和 Claude Web API 进行交互的程序



## 注意

目前这个项目仍处于初级阶段，可能存在一些问题。实现非常基础的功能，还没有进行细化。



## 使用方法

首先，你需要安装 `aiohttp` 和 `loguru` 这两个库：

```
pip install aiohttp loguru
```

接着，你需要获取`session_token`

它由两部分组成，你可以在浏览器打开`F12`后选择网络并开启记录网络日记，然后创建一个会话即可。

它应该类似这个样子

```
sessionKey=(a lot of things); __cf_bm=(a lot of things)
```

然后，你可以创建一个 `ClaudeWeb` 的实例，并使用它的方法来和 Claude Web API 进行交互

根据地区的不同，可能需要设置相应的代理

例如：

```
proxy = "http://127.0.0.1:7890"  # 您的代理
```



