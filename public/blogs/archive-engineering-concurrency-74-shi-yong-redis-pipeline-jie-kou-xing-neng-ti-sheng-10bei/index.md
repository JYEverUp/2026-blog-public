# 第74节 使用Redis Pipeline，接口性能提升10倍
本文是接口性能优化一个非常好的一个方案，好好掌握，先收藏点赞，慢慢看。
# 1、使用redis执行N个命令
假如我们有 N 个命令，需要让redis去执行
常见的做法，如下图，先发送第1个命令给redis，拿到响应后，再发送下一个命令，来来回回，需和redis交互N次
![image-20240818223251982](/blogs/_archive-2024-assets/a429acbca8160e9a1541.webp)
如果有1000个命令，每个命令耗时10毫秒，那么需要和redis来回交互1000次，差不多耗时10秒左右，效率非常低，有没有更好的办法呢？
Redis Pipeline 可以解决这个问题。
# 2、使用redis Pipeline 执行N个命令
如下图，Redis中的Pipeline技术，可以将多个命令一次性打包发给redis，然后redis按顺序执行每个命令，然后将所有命令的执行结果打包一次性返回给客户端。
N个命令来回只需交互一次就可以了，性能大幅提升。
![image-20240818224625548](/blogs/_archive-2024-assets/3a9e33eb558994378974.webp)
# 3、带大家看下效果
3个案例，重点看案例1和案例2，案例1使用循环执行100个redis命令，案例2使用pipeline执行同样的100个命令，然后对比下性能，会让大家惊讶
## 案例1：使用循环执行100个命令，看性能
```java
com.itsoku.lesson074.Lesson074ApplicationTest#test1
```
大概耗时60毫秒左右。
## 案例2：使用pipeline执行100个命令，看性能
```java
com.itsoku.lesson074.Lesson074ApplicationTest#test2
```
大概耗时6秒左右，相对于案例1，性能提升了10倍。
这里演示了100个命令，性能提升了10倍，如果命令更多，性能提升更明显，大家可以自己试试。
## 案例3：pipeline中可以批量执行任何命令
```java
com.itsoku.lesson074.Lesson074ApplicationTest#test3
```
# 4、总结
当需要用redis执行多个命令，且多个命令之间没有相互依赖的时，可采用pipeline，大幅提升性能，可以用来优化接口性能。
