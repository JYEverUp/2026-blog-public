## 代码缩略图：CodeGlance Pro

当代码很长的时候，为了快速下翻是不是很羡慕Sublime和VS Code右侧的缩略图，通过点击大概位置就可以快速的定位代码。

在IDEA中只需要安装插件：CodeGlance Pro，马上也能拥有它

![image-20240924202535101](/blogs/_archive-2024-assets/9c23760699071cfd2d5f.webp)

## 调试Stream操作  Java Stream Debugger

![image-20240924202710861](/blogs/_archive-2024-assets/5954e8619da623e227f5.webp)

```
public class StreamTest {

    @Test
    void test() {
        List<String> list = List.of("blog.didispace.com", "spring4all.com", "openwrite.cn", "www.didispace.com");

        List<String> result = list.stream()
                .filter(e -> e.contains("didispace.com"))
                .filter(e -> e.length() > 17)
                .toList();

        System.out.println(result);
    }

}

```

这段代码的逻辑是通过stream去过滤list集合中的元素，由于有两个filter，所以当出现问题的时候，可能不知道具体是哪个filter中出了问题。

借助强大的IDEA，我们在遇到stream的时候，只需要点击下图中的按钮：

![image-20240924202621441](/blogs/_archive-2024-assets/bc936b64267c2be53077.webp)

此时会弹出一个Stream操作的跟踪窗口：

![image-20240924202629120](/blogs/_archive-2024-assets/4e4a6f6e538f03d25ddf.webp)

## 接口管理工具：apifox

Apifox客户端安装成功后，我们来IDEA中设置Apifox插件，以便同步项目接口。

![image-20240924203338295](/blogs/_archive-2024-assets/7950150e2058024ac9b7.webp)

下载客户端，拿私钥过来配置。

![image-20240924203411092](/blogs/_archive-2024-assets/c3c62414c79ad14dfdda.webp)

![image-20240924203428833](/blogs/_archive-2024-assets/2d044645ab3b6725cd27.webp)

![image-20240924203447611](/blogs/_archive-2024-assets/a8a1e9fc175bd1d81762.webp)

![image-20240924203456732](/blogs/_archive-2024-assets/0e854e0bc6108368d3ea.webp)

##  进度条：**Mario Progress Bar**

安装该插件后，进度条的样式就会变成马里奥里面的角色。如下图：

![image-20240924203725934](/blogs/_archive-2024-assets/f0acf347e75f2b45f0ac.png)

![image-20240924203733377](/blogs/_archive-2024-assets/9f672b45624b3fb6206c.webp)

## json转对象：**GsonFormat**

给你一段`Json`格式数据，除了手写之外，如何快速生成一个和该`Json`数据对应的`Java`对象？

比如一段`Json`格式数据如下：

```
{
    "status": 0,
    "msg": "操作成功",
    "data": 1
}
```

**GsonFormat**则是一个**JSON格式数据 → 对象**的快速**代码自动生成**插件。

![图片](/blogs/_archive-2024-assets/b913d4b6d385f3cf26cd.webp)

![图片](/blogs/_archive-2024-assets/bc36f76edf528b3bb8ea.webp)

![图片](/blogs/_archive-2024-assets/2465959b235495f60a14.webp)

## 接口管理工具：**RestfulToolkit**

- 你知道你项目里到底写了多少个URL接口吗？
- 如何快速定位某个`URL`接口对应的`Controller`代码？
- 如何快速测试你的`Controller`接口？

**RestfulToolkit**则是一个可以解决上述问题的，非常方便的IDEA集成插件，从此`Postman`怕是要下岗了：

![图片](/blogs/_archive-2024-assets/fa38dfab243a1f6948fd.webp)

## 常用快捷键操作

### 重命名

有时候手误会把边变量名拼写错误，等到自己发现时，这个变量已经被引用了多次，这时再修改，需要把所有引用的地方都修改一遍，这就很麻烦。

IDEA 重构功能-重命名（**Rename**）,可以修改命名，并且一键替换所有的引用的地方。

另外函数名，类名修改都可以使用这个快捷键。

快捷键如下：

- **Windows：shift + F6**
- **Mac： ⇧  + F6**

### **快速抽取变量**

有时候新建了一个对象，忘记了创建了变量，就很麻烦，需要移动光标到前面，然后声明。

![图片](/blogs/_archive-2024-assets/45b714823cbdbae9478a.webp)

这种情况下，我们可以使用 IDEA 的重构功能-**Introduce Variable**。

快捷键如下：

- **Windows：ctrl + alt + V**
- **Mac： ⌥ + ⌘  + V**

### 快速抽取单独的方法

ctrl + alt + M

![image-20241207150250914](/blogs/_archive-2024-assets/51e6e8dfb8622bb00262.webp)

### 自动补全代码

使用这个快捷键，可以自动补全代码末尾的分号，括号对等等，可以让我们少打很多字符。另外这个快捷键还会自动格式化完成的代码。

快捷键：

- **Windows：ctrl + shift + Enter（回车键）**
- **Mac： ⌘ + ⇧  +⏎** 

**自动补全分号**

![图片](/blogs/_archive-2024-assets/c2bbfd1a4b4c51e2aab0.gif)

**自动补全括号对**

![图片](/blogs/_archive-2024-assets/c2bbfd1a4b4c51e2aab0.gif)

### 文件夹重命名快捷键

shift+F6

### 指定多个位置同时填相同内容

 ctrl + alt + shirt, 然后左键点击 选中 多行。

### 快速加入if代码块

 ctrl + alt + T，可以快速加if。

![image-20241207150045997](/blogs/_archive-2024-assets/12cab144dfbd0c99ca97.webp)
