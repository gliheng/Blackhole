+++
date = 2014-09-18T15:19:38Z
draft = false
title = "详细配置"
weight = 3

+++

# 配置文件详解 #

1. 配置文件是ini格式的，支持设置变量
2. rules定义了一组url匹配响应规则，每行规则之间通过tab分隔
3. 每行rules分为两组或三组，第三组可选
	- 匹配url正则
	- 数据来源（包括单文件、文件夹、ip、伪造请求、合并规则）
	- 中间件（可以修改请求和返回）

## 转发规则

示例一组规则定义如下：

- 转发到文件夹

	http://%(host)s/css/	%(root)s/css/

- 转发到单个文件

	http://res.html5.qq.com/topicshare/js/common1	%(build)s\js\common1.js


- 默认转发，免得被其他规则匹配上

	http://favtest.cs0309.html5.qq.com/login	DEFAULT


- 伪造一个404请求

	http://comic.html5.qq.com/cache.manifest	*404:sorry

- 转发到一个concat配置文件

	http://3gimg.qq.com/reader/v\d+/js/reader.min.js	%(root)s/meteor.cfg


- 转发到单个文件，再对文件跑个py文件处理下

	http://comic.html5.qq.com/	E:\ComicWebServer\wsp\index.wsp	comic_index.py

- 默认转发，但是使用两个中间件修改请求。加入清除缓存header, 然后修改返回加入weinre调试脚本

	http://comic.html5.qq.com/	DEFAULT	bustCache|weinre


## Tunnel规则

- Tunnel使用一个域名将请求转发到你的PC，方便移动调试。
- 每行tunnel定义也是两个或三个部分，第三部分可选。定义可以有很多行。
	- tunnel域名
	- 转向域名
	- 中间件

示例如下：

	tunnels = 
		test.mttweb.html5.qq.com	www.example.com	bustCache|weinre|fixcookie

这个配置通过test.mttweb.html5.qq.com域名把请求转发到你的pc上变成www.example.com的请求。


tunnel的server是可以配置的，鹅厂员工请使用

	tunnel_server = mttweb.html5.qq.com:8080
