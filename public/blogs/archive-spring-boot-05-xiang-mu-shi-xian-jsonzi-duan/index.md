参考http://www.dedeyun.com/it/java/93532.html

有些很复杂的信息，我们一般会用扩展字段传一个json串，字段一般用text类型存在数据库。mysql5.7以后支持json类型的字段，还可以进行sql查询与修改json内的某个字段的能力。

### 1.表结构

```java
`ip_info` json DEFAULT NULL COMMENT 'ip信息',
```

设置的字段为json类型。

```java
select * from `user` where ip_info->'$.createIp' ='113.110.223.73'
```

如果我们想查json字段里的某个值`createIp`，可以这样去查询。

### 2.配置实体类

设置自动生成resultmap

![image-20240924200934758](/blogs/_archive-2024-assets/b26cc42067a8e34982ab.webp)

![image-20240924200945667](/blogs/_archive-2024-assets/28aadb6e56bdadf3c13d.webp)

类型改为我们期望的类型，并配置类型转换。
