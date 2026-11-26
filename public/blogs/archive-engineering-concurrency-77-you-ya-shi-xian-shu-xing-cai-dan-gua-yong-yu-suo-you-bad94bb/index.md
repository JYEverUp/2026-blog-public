# 第77节 优雅实现树形菜单，适用于所有树，太好用了

# 1、背景
树形菜单，经常会用到，通常后端需要给前端提供接口，返回树形json数据，前端将其渲染成树结构。
hutool中给我们提供了一个通用的树工具类：TreeUtil，里面提供了很多好的用法，比如用来构建树的方法，非常好用。
## 2、先带大家看下效果
启动SpringBoot应用`com.itsoku.lesson077.Lesson077Application`
浏览器中访问：http://localhost:8080/menuTree
返回下面json数据，是树形结构的，前端拿到后，便可轻松处理
```json
[
  {
    "id": "1",
    "name": "菜单1",
    "parentId": null,
    "weight": 1,
    "url": "url1",
    "children": [
      {
        "id": "101",
        "name": "菜单101",
        "parentId": "1",
        "weight": 1,
        "url": "url101"
      },
      {
        "id": "102",
        "name": "菜单102",
        "parentId": "1",
        "weight": 1,
        "url": "url102"
      }
    ]
  },
  {
    "id": "2",
    "name": "菜单2",
    "parentId": null,
    "weight": 1,
    "url": "url2",
    "children": [
      {
        "id": "201",
        "name": "菜单201",
        "parentId": "2",
        "weight": 1,
        "url": "url201"
      },
      {
        "id": "202",
        "name": "菜单202",
        "parentId": "2",
        "weight": 2,
        "url": "url202"
      }
    ]
  }
]
```
上面json数据，对应下面这2棵树
![image-20240823132250754](/blogs/_archive-2024-assets/34aeff5be9ae39d5fc47.webp)
# 3、代码解析
## 引入hutool maven配置
```xml
<dependency>
    <groupId>cn.hutool</groupId>
    <artifactId>hutool-all</artifactId>
    <version>5.8.2</version>
</dependency>
```
## 案例代码
```java
package com.itsoku.lesson077;
import cn.hutool.core.lang.tree.Tree;
import cn.hutool.core.lang.tree.TreeUtil;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.ArrayList;
import java.util.List;
/**
 * <b>description</b>实战
 * <b>time</b>：2024/8/22 21:01 <br>
 * <b>author</b>：gjy
 */
@RestController
public class MenuController {
    /**
     * 获取树形菜单
     *
     * @return
     */
    @GetMapping("/menuTree")
    public List<Tree<String>> menuTree() {
        //菜单列表，放在一个menuPOList中，我们用的时候这个数据可以从 db 中去获取
        List<MenuPO> menuPOList = new ArrayList<>();
        menuPOList.add(MenuPO.builder().id("1").name("菜单1").pid(null).theSort(1).url("url1").build());
        menuPOList.add(MenuPO.builder().id("101").name("菜单101").pid("1").theSort(1).url("url101").build());
        menuPOList.add(MenuPO.builder().id("102").name("菜单102").pid("1").theSort(1).url("url102").build());
        menuPOList.add(MenuPO.builder().id("2").name("菜单2").pid(null).theSort(1).url("url2").build());
        menuPOList.add(MenuPO.builder().id("201").name("菜单201").pid("2").theSort(1).url("url201").build());
        menuPOList.add(MenuPO.builder().id("202").name("菜单202").pid("2").theSort(2).url("url202").build());
        /**
         * 下面通过 hutool 提供的工具类 TreeUtil.build，将上面的菜单列表转换为树
         * 3个参数
         * 参数1：数据源，即要被转换为树的原始数据，本案例中就是上面的 menuPOList
         * 参数2：根节点id
         * 参数3：转换器，数据源的数据可以是各种类型的，但是hutool不能识别，所以这里需要一个转换器，
         *   将第一个参数中的元素转换为 hutool可以识别的类型：Tree类（hutool对树节点的一个抽象），
         *   Tree表示树的一个节点，里面包含了这个节点所有的信息
         */
        List<Tree<String>> treeList = TreeUtil.build(menuPOList, null, (MenuPO menuPo, Tree<String> treeNode) -> {
            //树节点id
            treeNode.setId(menuPo.getId());
            //树节点名称
            treeNode.setName(menuPo.getName());
            //父节点id
            treeNode.setParentId(menuPo.getPid());
            //权重，相当于同级节点的顺序，同级会按升序排序
            treeNode.setWeight(menuPo.getTheSort());
            //节点扩展数据，可以通过put方法，放入任意个扩展数据
            treeNode.put("url", menuPo.getUrl());
        });
        return treeList;
    }
}
```
