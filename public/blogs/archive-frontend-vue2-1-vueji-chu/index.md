## 一、 Vue基础

### 1. 上手vue简单示例

- 想让 Vue 工作，就必须创建一个 Vue 实例，且要传入一个配置对象
- demo 容器里的代码依然符合 html 规范，只不过混入了一些特殊的 Vue 语法
- demo 容器里的代码被称为【Vue模板】
- Vue实例和容器是一一对应的，真实开发中只有一个Vue实例，并且会配合着组件一起使用
- {{xxx}}是 Vue 的语法：插值表达式，{{xxx}}可以读取到 data 中的所有属性
- 一旦 data 中的数据发生改变，那么页面中用到该数据的地方也会自动更新( Vue 实现的响应式)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- 引入Vue -->
  <script type="text/javascript" src="../js/vue.js"></script>
  <title>初始vue</title>
</head>
<body>
  <div id="root">
    <h2>hello {{ name }} !</h2>
  </div>
  <script type="text/javascript">
    Vue.config.productionTip = false //阻止vue启动时生成生产提示
    const x= new Vue({
      el:'#root', //选择挂载点，指定vue实例为哪个容器服务
      data:{ //data 用于存储数据
        name:'Vue'
      }
    })
  </script>
</body>
</html>
```

### 2. 模板语法

Vue模板语法有2大类:
插值语法：
  功能：用于解析标签体内容
  写法：{{xxx}}，xxx是 js 表达式，且可以直接读取到 data 中的所有属性
指令语法:
  功能：用于解析标签（包括：标签属性、标签体内容、绑定事件…）
  举例：v-bind:href=“xxx” 或 简写为 :href=“xxx”，xxx 同样要写 js 表达式，且可以直接读取到 data 中的所有属性

```html
<div id="root">
  <h2>指令语法与插值语法的使用</h2>
  <hr>
  <a v-bind:href="Bing_url">{{Bing_title}}</a>
  <a :href="BaiDu_url">{{BaiDu_title}}</a>
</div>
<script type="text/javascript">
  const x= new Vue({
    el:'#root',
    data:{ 
      Bing_title:'Bing',
      BaiDu_title:'BaiDu',
      Bing_url:'http://www.bing.com',
      BaiDu_url:'http://www.baidu.com'
    }
  })
</script>
```

### 3. 数据绑定

Vue中有2种数据绑定的方式：
  单向绑定(v-bind)：数据只能从data流向页面
  双向绑定(v-model)：数据不仅能从data流向页面，还可以从页面流向data
tips:

    1. 双向绑定一般都应用在表单类元素上（如：input、select等）
    2. `v-model:value=''` 可以简写为 `v-model=''`，因为 v-model 默认收集的就是 value 值

```html
<div id="root">
  <h2>数据绑定</h2>
  <hr>
  <input type="text" :value="data1">
  <!-- <input type="text" v-model:value="data2"> -->
  <input type="text" v-model="data2">
</div>
<script type="text/javascript">
  Vue.config.productionTip = false 
  const x = new Vue({
    el:'#root',
    data:{ 
      data1:'单向绑定',
      data2:'双向绑定'
    }
  })
</script>
```

### 4. el与data的数据

el 有2种写法
  new Vue 时候配置el属性
  先创建 Vue 实例，随后再通过`vm.$mount('#root')`指定 el 的挂载点
data 有2种写法
  对象式
  函数式（在组件中，data 必须使用函数式）
常规定义方式：

```html
<script type="text/javascript">
  Vue.config.productionTip = false 
  const vm = new Vue({
    el:'#root',
    data:{ 
      data1:'单向绑定',
      data2:'双向绑定'
    }
  })
</script>
```

第二种定义方式：

```html
<script type="text/javascript">
  Vue.config.productionTip = false 
  const vm = new Vue({
    // 此处函数不能写为箭头函数 ，否则 this 指向 window,如下
    // data:()=>{ 
    data() { 
      return {
        data1:'单向绑定',
        data2:'双向绑定'
      }
    }
  })
  vm.$mount('#root')
</script>
```

### 5. MVVM 模型

M：模型(Model) ：data中的数据
V：视图(View) ：模板代码
VM：视图模型(ViewModel)：Vue实例
![Vue中的MVVM模型视图](/blogs/_archive-2024-assets/156d66c3d685de218ffd.webp)
总结：

    1. Vue构造函数 所管理的 data 函数中所有的属性，最终都会出现在 vm 实例身上
    2. vm 身上的所有属性 以及 Vue 原型上的所有属性，在 Vue 模板语法中均可以直接使用


### 6. 数据代理

#### 1） 数据代理原理 |  Object.defineProperty(obj, prop, descriptor)

```js
/* 
  Object.defineProperty(obj, prop, descriptor)
    obj：要定义属性的对象。
    prop：要定义或修改的属性的名称
    descriptor：要定义或修改的属性描述符
*/ 
let Persion = {
  name:'lisi',
  sex:'男'
}
let number = 0
Object.defineProperty(Persion,'age',{ 
  // value:18,
  // writable: true, // 如果为 true，则值可以被修改，否则它是只可读的
  // enumerable: true,// 如果为 true，则表示是可以遍历的，可以在for… .in Object.keys()中枚举出来
  // configurable: true // 如果为 true，则此属性可以被删除，这些特性也可以被修改，否则不可以

  // gte()函数（getter）会在 Persion 对象指定属性被访问时调用，且返回值为指定属性（此处为 age 属性）的值
  get:function() {
    console.log('Persion.age 被访问了');
    return number
  },
  // set()函数（setter）会在 Persion 对象指定属性被修改时调用，且会收到具体的修改值
  set:function(value) {
    console.log('Persion.age 将被修改，值为',value);
    number = value
    console.log('Persion.age --- ',Persion.age);
  }
})
console.log(Persion);
console.log(Object.keys(Persion)); // Object.keys() 以数组形式返回参数对象的属性名
```

#### 2) 实现简单数据代理 | 单向绑定

```js
let obj1 = { x:1 }
let obj2 = { y:2 }
Object.defineProperty(obj2,'x',{
  set(value) {
    obj1.x = value
  },
  get() {
    return obj1.x
  }
})
```

### 7. 事件处理

#### 1) 事件的基本使用：

1. 使用`v-on:xxx` 或 语法糖形式：`@xxx` 绑定事件，其中xxx是事件名,如：`<button @click="show(value)">点击输出信息</button>`
2. 事件的回调需要配置在 methods 对象中，最终会在 vm 上
3. methods 中配置的函数，都是被 Vue 所管理的函数，事件处理函数中的 this 的指向 vm 或 组件实例对象
4. `@click="show(value)"`和`@click="show"`效果一致，事件处理函数会默认收到事件信息，如果同时需要事件信息和传递形参，需借助`$event`,例如：`<button @click="show($event,value)">点击输出信息</button>`

```html
<div id="root">
  <h2>事件处理</h2>
  <hr>
  <!-- <button v-on:click="show">点击输出信息</button> -->
  <!-- 语法糖 -->
  <button @click="show">点击输出信息</button>
  <!-- 传参 -->
  <button @click="show1(66)">点击输出信息2</button>
  <!-- 传参 并且需要 event 对象 -->
  <button @click="show2($event,44)">点击输出信息3</button>
</div>
<script type="text/javascript">
  Vue.config.productionTip = false 
  const vm = new Vue({
    el: '#root',
    data: {
      name:'Hello'
    },
    methods: {
      show(event) {//默认接收到事件信息
        console.log(event.target);
        console.log(this.name); // Hello
      },
      show1(value) {
        console.log(value); // 66
      },
      show2(event,value) {
        console.log(event,value); // 'event' , 44
      }
    }
  })
</script>
```

#### 2) 事件修饰符

Vue中的事件修饰符

1. .prevent：阻止默认事件（常用）   原生 ------ event.preventDefault()
2. .stop：阻止事件冒泡（常用）    原生 ------ event.stopPropagation()
3. .once：事件只触发一次（常用）
4. .capture: 使用事件捕获模式(即内部元素触发的事件先在此处理，然后才交由内部元素进行处理)
5. .self: 只当在 event.target 是当前元素自身时触发处理函数
6. .passive: 事件默认行为立即执行，无需等待事件回调执行完毕

```html
<!-- 修饰符可以串联 -->
<a @click.stop.prevent="doThat"></a>
```

#### 3) 键盘事件

键盘事件语法糖：`@keydown`，`@keyup`

1. Vue中常用的按键别名：

  - 回车 => enter
  - 删除 => delete
  - 退出 => esc
  - 空格 => space
  - 换行 => tab (特殊，必须配合keydown去使用)
  - 上  => up 
  - 下  => down 
  - 左  => left 
  - 右  => right 

2. Vue未提供别名的按键，可以使用按键原始的key值去绑定，但注意要转为kebab-case（短横线命名）
3. 系统修饰键（用法特殊）：ctrl、alt、shift、meta
   (1). 配合keyup使用：按下修饰键的同时，再按下其他键，随后释放其他键，事件才被触发。
    (2). 配合keydown使用：正常触发事件。
4. 也可以使用keyCode去指定具体的按键（不推荐）
5. Vue.config.keyCodes.自定义键名 = 键码，可以去定制按键别名（不推荐）

```html
<div id="root">
  <h2>键盘事件</h2>
  <hr>
  <input type="text" @keyup.enter="showInfo" placeholder="回车确认">
  <input type="text" @keyup.enter="showInfo" placeholder="回车确认">
  <input type="text" @keyup.ctrl.y="showInfo" placeholder="ctrl+y确认">
</div>
<script type="text/javascript">
  Vue.config.productionTip = false 
  const vm = new Vue({
    el: '#root',
    methods: {
      showInfo(event) {
        console.log(event.target.value);
      }
    }
  })
</script>
```

### 8. computed | 计算属性

1. 在 computed 属性对象中定义计算属性的方法
2. 在页面中使用{{ 方法名 }}来显示计算的结果
3. 定义：要用的属性不存在，要通过已有属性计算得来。
4. 原理：底层借助了 `Objcet.defineproperty` 方法提供的 getter 和 setter。
5. 计算属性的 get 函数什么时候执行？
   (1). 初次读取时会执行一次。
     (2). 当依赖的数据发生改变时会被再次调用。
6. 优势：与 methods 实现相比，内部有缓存机制（复用），效率更高，调试方便。
7. 备注：
   (1). 计算属性最终会出现在vm上，直接读取使用即可。
     (2). 如果计算属性要被修改，那必须写set 函数去响应修改，且 set 中要引起计算时依赖的数据发生改变。

```html
<div id="root">
  <h2>计算属性案例</h2>
  <hr>
  <input type="text" v-model="firstname">
  <input type="text" v-model="lastname">
  <h4>{{fullName}}</h4>
</div>
<script type="text/javascript">
  Vue.config.productionTip = false 
  const vm = new Vue({
    el: '#root',
    data:{
      firstname:'张',
      lastname:'三'
    },
    computed: {
      fullName: {
        get() {
          return this.firstname + `-`+ this.lastname
        },
        set(value) {
          const arr = value.split('-')
          this.firstname = arr[0]
           this.lastname = arr[1]
        }
      }
    }
  })
</script>
```

计算属性的简写方式：（前提：此计算属性不需要被修改）

```js
computed: {
  // 可以将计算属性写为一个函数形式，此函数当作计算属性的 getter 使用
  fullName() {
    return this.firstname + `-`+ this.lastname
  }
}
```

### 9. watch | 监视属性

通过 vm 对象的 $watch() 或 watch 配置来监视指定的属性
当被监视的属性变化时, 回调函数自动调用, 进行相关操作
监视的属性必须存在，才能进行监视！！!
监视的两种写法：
  (1). new Vue时传入watch配置
  (2). 通过vm.$watch监视

```js
<script type="text/javascript">
  const vm = new Vue({
    el: '#root',
    data:{
      isHost:true
    }
    watch:{
      isHost:{
        immediate:true,//初始化时让 handler 调用一下
		    //handler什么时候调用？当 isHot 发生改变时。
        handler(newValue,oldVlaue){console.log(newValue,oldVlaue);
        }
      }
    }
  })
</script>
```

```js
<script type="text/javascript">
  const vm = new Vue({
    el: '#root',
    data:{
      isHost:true
    }
  })

  vm.$watch('isHost',{
    immediate:true, 
	  handler(newValue,oldValue){
	  	console.log('isHot被修改了',newValue,oldValue)
	  }
  })
</script>
```

#### 深度监视 | 适用与监视引用数据类型

1. Vue 中的 watch 默认不监测对象内部值的改变（一层）。
2. 配置 `deep:true` 可以监测对象内部值改变（多层），个人理解为监视引用数据类型
   备注：
3. Vue 自身可以监测对象内部值的改变，但 Vue 提供的 watch 默认不可以！
4. 使用 watch 时根据数据的具体结构，决定是否采用深度监视。

```js
data:{
  obj:{
    a:0,
    b:1
  }
},
watch:{
  // 监视多级结构中的某个属性
  'obj.a':{
    handler(newValue,oldVlaue){console.log(newValue,oldVlaue);
    }
  },
  // 监视多级结构
  obj:{
    deep:true,//开启深度监视
    handler(newValue,oldVlaue){console.log(newValue,oldVlaue);
    }
  }
}
```

#### watch | 监视属性的简写形式

```js
watch:{
  // 当某个监视属性不需要配置项时，只需要响应者时触发语法糖，vm.$watch 也可以使用语法糖
  isHost(newValue,oldVlaue){
    console.log(newValue,oldVlaue);
  } 
}
```

### 10. computed 和 watch 之间的区别：

1. computed 能完成的功能，watch 都可以完成。
2. watch 能完成的功能，computed 不一定能完成，例如：watch 可以进行异步操作，computed 中不能开启异步任务。
3. 两个重要的小原则：

- 所有被 Vue管理的函数，最好写成普通函数，这样 this 的指向才是 vm 或 组件实例对象。
- 所有不被 Vue所管理的函数（定时器的回调函数、ajax 的回调函数等、Promise 的回调函数），最好写成箭头函数，这样this 的指向才是 vm 或 组件实例对象。

```js
// 错误示例
const vm = new Vue({
  el: '#root',
  data:{
    a:1,
    b:2
  },
  computed: {
    sum() {
      setTimeout(()=>{
        reuturn a + b 
        // return的值交给箭头函数执行 ，箭头函数由浏览器定时器对象调用，非 Vue 示例调用
      },1000)
    }
  }
})
/*
计算属性必须要返回值，侦听属性是依靠给已有属性重新赋值。
异步任务不能使用 return 给外部同步函数返回值，因为是异步的，所以也不能用同步定义的变量接
*/ 
```

### 11. 动态指定class & style 样式

在应用界面中, 某个(些)元素的样式是变化的，class/style 绑定就是专门用来实现动态样式效果的技术

1. class绑定：
   `:class='xxx' // xxx可以是字符串、对象、数组。`
     字符串  表达式是字符串: `'classA'`  适用于：类名不确定，要动态获取
     对象  表达式是对象: `{classA:isA, classB: isB}` 适用于：要绑定多个样式，个数不确定，名字也不确定
     数组  表达式是数组: `['classA', 'classB']`  适用于：要绑定多个样式，个数确定，名字也确定，但不确定用不用
2. style 绑定： 
   `:style="{ color: activeColor, fontSize: fontSize + 'px' }"` ，其中 activeColor/fontSize 是 data 属性
     对象  `:style="{fontSize: xxx}"` 其中xxx是动态值。
     数组  `:style="[a,b]"` 其中a、b是样式对象。

```html
  <div id="root">
    <h2>动态指定样式</h2>
    <hr>
    <!-- 绑定样式 —— 字符串写法 适用情况:样式类名不确定 需要追加-->
    <h3 class="basic red" :class="login_class">未登录/注册</h3>
    <button @click="login">登录</button>
    <button @click="demo">随机改变样式</button>

    <!-- 绑定样式 —— 数组写法 适用情况:样式类名不确定 追加个数也不确定-->
    <h3 :class="class_arr">未登录/注册</h3>

    <!-- 绑定样式 —— 对象写法 适用情况:样式类名确定 个数确定 但动态决定追加-->
    <h3 :class="class_obj">未登录/注册</h3>

    <!-- 绑定内联样式 —— 对象写法 -->
    <!-- <h3 :style="{fontSize: 10+'px'}"> 内联样式指定 </h3> -->
    <h3 :style="style_obj"> 内联样式对象指定 </h3>

    <!-- 绑定内联样式 —— 数组写法 (极少用)-->
    <h3 :style="[style_obj]"> 内联样式数组指定 </h3>
  </div>
  <script type="text/javascript">
    Vue.config.productionTip = false 
    const vm = new Vue({
      el: '#root',
      data:{
        login_class:'12',
        class_arr:['pink','green'],
        class_obj:{
          pink:true,
          green:false
        },
        style_obj:{
          fontSize: '10px'
        }
      },
      methods: {
        login() {  
          this.login_class = 'green'
        },
        demo() {  
          let arr = ['red','green','pink']
          this.login_class = arr[Math.floor(Math.random()*3)]
        },
      }
    })
  </script>
```

### 12. 渲染指令

#### 1. 条件渲染 | v-if、v-show

1. v-if
   语法：

    1) `v-if = '表达式'`
    2) `v-else-if = '表达式'`
    3) `v-else = '表达式'`
       适用于：切换频率较低的场景
       特点：不展示的DOM元素直接被移除
       注意：v-if可以和:v-else-if、v-else一起使用，但要求结构不能被“打断”

2. v-show
   语法：
     `v-show='表达式'`
   适用于：切换频率较高的场景
   特点：不展示的DOM元素未被移除，仅仅是使用样式隐藏掉(display:none)
   备注：使用 v-if 的时，元素可能无法获取到，而使用v-show一定可以获取到 v-if 是实打实地改变dom元素，v-show 是隐藏或显示dom元素

```html
<div id="root">
    <h2>条件渲染</h2>
    <hr>
    <!-- v-show 可以接受布尔值/表达式作为属性值 -->
    <div v-show="true">{{ hello_name }}</div>
    <div v-show="0.1+0.2===0.3">{{ vue_name }}</div>

    <!-- v-if 可以接受布尔值/表达式作为属性值 -->
    <div v-if="n==1">{{ hello_name }}</div>
    <div v-else-if="n==2">{{ hello_name }}!</div>
    <div v-else-if="n==3">{{ hello_name }}!!</div>
    <div v-else-if="n>=3">{{ hello_name }} good</div>
    <button @click="n++">点击变换</button>

    <!-- v-if与template的配合使用  管理多个元素渲染 -->
    <template v-if="n==1">
      <ul>
        <li>1</li>
        <li>2</li>
        <li>3</li>
      </ul>
    </template>
  </div>
  <script type="text/javascript">
    const x= new Vue({
      el:'#root', 
      data:{ 
        hello_name:'Vue',
        vue_name:'Vue',
        n:1
      }
    })
  </script>
```

#### 2. 列表渲染 | v-for

v-for指令，用于展示列表数据
语法：`v-for="(item, index) in xxx" :key="yyy"`
可遍历元素：数组、对象、字符串（用的很少）、指定次数（用的很少）

  - 组: (item, index)
  - 象: (value, key)
  - 符串：(char, index)
  - 字：(number, index)

```html
<div id="root">
    <h2>列表渲染</h2>
    <hr>
    <div>
      <!-- 遍历数组 -->
      <!-- <ul v-for="p in persion" :key="p.id"> -->
      <ul v-for="p of persion" :key="p.id">
        <li>{{p.name}} ，年龄：{{p.age}}</li>
      </ul>

      <!-- 遍历对象 -->
      <ul v-for="(value,key) of persion[0]" :key="key">
        <li>{{ value }}</li>
      </ul>

      <!-- 遍历字符串 -->
      <ul v-for="(char,index) of 'hello'" :key="index">
        <li>第{{index}}字母为：{{ char }}</li>
      </ul>

      <!-- 遍历指定次数 -->
      <ul v-for="(char,index) of 4" :key="char+index+Math.random()">
        <li>{{ char }} ，索引为 {{index}}</li>
      </ul>
    </div>
  </div>
  <script type="text/javascript">
    const x= new Vue({
      el:'#root', 
      data:{ 
        persion: [
          {id:'sk9G2O01avD',name:'张三',age:'12'},
          {id:'k8F4Dl7m',name:'李四',age:'34'},
          {id:'oB5vA0Qmm1p',name:'杰克',age:'22'}
        ]
      }
    })
  </script>
```

##### key 的作用与原理

虚拟DOM中key的作用：
key是虚拟DOM对象的标识，当数据发生变化时，Vue会根据【新数据】生成【新的虚拟DOM】, 随后Vue进行【新虚拟DOM】与【旧虚拟DOM】的差异比较，比较规则如下：
对比规则：

1. 旧虚拟DOM中找到了与新虚拟DOM相同的key：
   ①若虚拟DOM中内容没变, 直接使用之前的真实DOM
   ②若虚拟DOM中内容变了, 则生成新的真实DOM，随后替换掉页面中之前的真实DOM
2. 旧虚拟DOM中未找到与新虚拟DOM相同的key创建新的真实DOM，随后渲染到到页面。
   用index作为key可能会引发的问题：

    1) 若对数据进行：**逆序添加、逆序删除**等破坏顺序操作: 会产生没有必要的真实DOM更新 ==> 界面效果没问题, 但效率低
    2) 如果结构中还包含输入类的DOM： 会产生错误DOM更新 ==>界面有问题
       开发中如何选择key:

1. 最好使用每条数据的唯一标识作为key, 比如id、手机号、身份证号、学号等唯一值。
2. 如果不存在对数据的逆序添加、逆序删除等破坏顺序操作，仅用于渲染列表用于展示，使用index作为key是没有问题的。

#### 3. 实现列表排序 

```html
  <div id="root">
    <h2>列表排序</h2>
    <hr>
    <input type="text" v-model="inputKey" placeholder="检索姓名">
    <button @click="sortType = 1">年龄升序</button>
    <button @click="sortType = 2">年龄降序</button>
    <button @click="sortType = 0">原顺序</button>
    {{sortType}}
    <div>
      <ul v-for="p of filePersion" :key="p.id">
        <li>{{p.name}} ，年龄：{{p.age}}</li>
      </ul>
    </div>
  </div>
  <script type="text/javascript">
     new Vue({
      el: '#root', 
      data: { 
        sortType: 0, //0 原顺序 ，1 升序，2 降序
        inputKey: '',
        persion: [
          {id:'sk9G2O01avD',name:'张三',age:'12'},
          {id:'k8F4Dl7m',name:'李四',age:'34'},
          {id:'1Ff3lm0G',name:'李六',age:'54'},
          {id:'sf3Pd94pf7za',name:'张九',age:'32'},
          {id:'oB5vA0Qmm1p',name:'杰克',age:'22'}
        ],
      },
      computed: {
        filePersion() {
          const arr =  this.persion.filter((p)=>{
            return p.name.indexOf(this.inputKey) >= 0
          })
          // 判断是否需要排序
          if (this.sortType) {
            arr.sort((p1,p2)=>{
              return this.sortType === 1 ?  p1.age-p2.age : p2.age-p1.age
            })
          }
          return arr
        }
      }
    })
  </script>
```

#### 4. 数据监测原理_对象

简单模拟vue更新数据原理

```js
let data = {
    name:'尚硅谷',
    address:'北京',
}

function Observer(obj){
    //汇总 data 对象中所有的属性形成一个数组
    const keys = Object.keys(obj)
    //遍历 keys 数组，分别添加 getter 、 setter
    keys.forEach((k) => {
        Object.defineProperty(this, k, {
            get() {
                return obj[k]
            },
            set(val) {
                console.log(`${k}被改了，我要去解析模板，生成虚拟DOM.....我要开始忙了`)
                obj[k] = val
            }
        })
    })
}

//创建一个监视的实例对象，用于监视(中转) data 中属性的变化
const obs = new Observer(data)		
console.log(obs)	

//准备一个vm实例对象
let vm = {}
vm._data = data = obs
```

#### 5. Vue.set | 为 data 中的对象追加属性

Vue.set 的使用（两种方式）
  方式1：`Vue.set(target，propertyName/index，value)` 
  方式2：`vm.$set(target，propertyName/index，value)`
注意：Vue.set方法也可以对数组（数组是特殊的对象）进行操作，但是不能对data中的根数据进行改变

```html
<div id="root">
  <div>
    <!-- 追加属性data对象 -->
    <button @click = "updataPersion">更新数据</button>
    <ul v-for="p of persion" :key="p.id">
      <li>{{ p.name }} <span v-if="p.age">，年龄：{{ p.age }}</span></li>
    </ul>
  </div>
</div>
<script type="text/javascript">
  const vm = new Vue({
    el: '#root', 
    data: { 
      persion: [
        {id:'sk9G2O01avD',name:'张三',age:''},
        {id:'k8F4Dl7m',name:'李四',age:'34'}
      ],
    },
    methods: {
     updataPersion() {
       // Vue.set(this.persion[0],'age',100)
       this.$set(this.persion[0],'age',100)
     }
    },
  })
</script>
```

#### 6. 数据监测原理_数组

vue 监测在数组中没有 getter 和 setter，所以监测不到数据的更改，也不会引起页面的更新。
vue 对数组的监测是通过 **包装数组上常用的用于修改数组的方法**来实现的。

```html
  <div id="root">
    <div>
      <div>
        <span v-for="(n,index) of arr" :key="index">{{ n }} ,</span>
      </div>
      <!-- 通过索引改变原数组是不被允许的  不奏效-->
      <button @click="arr[0]=100">通过索引改变原数组</button> <br><br>
      
      <button @click="arr.splice(0,1,100)">通过数组方法改变原数组</button><br><br>
      <button @click="age">通过set()改变原数组</button>
    </div>
  </div>
  <script type="text/javascript">
    new Vue({
     el: '#root', 
     data: { 
       arr: [1,4,8,9,10],
     },
     methods: {
       age(){
         this.$set(this.arr,0,200)
       }
     },
   })
 </script>
```

#### 总结：

Vue监视数据的原理：

1. vue会监视data中所有层次的数据

2. 如何监测对象中的数据？
   通过 setter 实现监视，且要在 new Vue 时就传入要监测的数据。
     对象中后追加的属性，Vue 默认不做响应式处理，如需给后添加的属性做响应式，请使用如下API：

   ```
     Vue.set(target，propertyName/index，value) 
     vm.$set(target，propertyName/index，value)
   ```

3. 如何监测数组中的数据？
   通过包裹数组更新元素的方法实现，本质就是做了两件事：

   1) 调用原生对应的方法对数组进行更新
   2) 重新解析模板，进而更新页面

4. 在Vue修改数组中的某个元素一定要用如下方法：
   使用这些API:push()、pop()、shift()、unshift()、splice()、sort()、reverse()
     `Vue.set()` 或 `vm.$set()`
     直接替换原数组 如：`arr = arr.filter((n)=>{return n!==1})`

5. 特别注意：`Vue.set()` 和 `vm.$set()` 不能给 vm 或 vm 的根数据对象 添加属性！！！

6. 数据劫持：每个数据经过数据代理的过程就叫数据劫持

### 13. 收集表单数据

1. v-model 默认收集的是被收集元素的 value 值，用户输入即收集 value 值。如 text/password/email等属性input表单元素 `<input type="text" v-model="userInfo.account">`
2. 表单元素默认无 value 值的，如 checkbox/redio/select等属性表单元素，可以手动配置value属性，v-model收集配置属性 `<input type="radio" name="sex" v-model="userInfo.sex" value="male">`
3. 没有配置 value 属性的表单元素，那么默认收集的就是 checked（勾选 or 未勾选，是布尔值）`<input type="checkbox" v-model="userInfo.agree">`
4. v-model 的指定收集元素的初始值会影响 收集的属性配置了 input 的 value 属性
   v-model 的初始值是非数组，那么收集的就是 checked（勾选 or 未勾选，是布尔值）
     v-model 的初始值是数组，那么收集的的就是 手动配置的 value 组成的数组
5. v-model 收集表单元素可以添加修饰符，如`v-model.number = 'userInfo.age'`
   lazy：失去焦点再收集数据
   number：输入字符串转为有效的数字
   trim：输入首尾空格过滤

```html
  <div id="root">
    <form action="">
      账号：<input type="text" v-model="userInfo.account"><br><br>
      密码：<input type="text" v-model="userInfo.password"><br><br>
      性别：
      男 <input type="radio" name="sex" v-model="userInfo.sex" value="male"> 
      女 <input type="radio" name="sex" v-model="userInfo.sex" value="female"><br><br>
      爱好：
      LOL     <input type="checkbox" v-model="userInfo.hobby" value="lol"> &nbsp;
      原神    <input type="checkbox" v-model="userInfo.hobby" value="mihoyo"><br><br>
      所在服务器：
      <select name="" id="" v-model="userInfo.server">
        <option value="">请选择你的服务器地址</option>
        <option value=" asia ">亚洲</option>
        <option value=" america ">美洲</option>
        <option value=" europe ">欧洲</option>
      </select><br><br>
      其它信息：
      <textarea name="" id="" v-model="userInfo.other"></textarea><br><br>
      <input type="checkbox" v-model="userInfo.agree"> 阅读并接收<a href="#">用户协议</a><br><br>
      <button type="button" @click="login">登录</button>
    </form>
  </div>
  <script type="text/javascript">
    const x= new Vue({
      el:'#root', 
      data:{
        userInfo:{
          account:'',
          password:'',
          sex:'',
          hobby:[],
          server:'',
          other:'',
          agree:'',
        }
      },
      methods: {
        login() {
          console.log(JSON.stringify(this.userInfo));
        }
      },
    })
  </script>
```

### 14. 过滤器（了解）

定义：对要显示的数据进行特定格式化后再显示（适用于一些简单逻辑的处理）。
语法：

    1. 注册过滤器：

    全局注册 `Vue.filter(name,callback)` 
    局部注册 `new Vue{filters:{}}`

    2. 使用过滤器：`{{ xxx | 过滤器名}}` 或 `v-bind:属性 = 'xxx | 过滤器名'`
       备注：

- 过滤器也可以接收额外参数、多个过滤器也可以串联
- 过滤器并没有改变原本的数据, 是产生新的对应的数据

```html
  <div id="root">
    <h2>过滤器</h2>
    <hr>
    <h3 v-if="timeStr">当前时间为： {{ time | timeFormater }}</h3>
  </div>
  <script type="text/javascript">
    let time = new Date()
    const vm = new Vue({
      el:'#root', 
      data:{
        time
      },
      filters:{
        timeFormater(value) {
          return value.toLocaleString()
        }
      }
    })
  </script>
```

### 15. vue指令

#### 1. 内置指令

目前vue中的常见内置指令：

- v-bind  : 单项绑定解析表达式 ，语法糖： :xxx
- v-model  : 双向数据绑定
- v-on  : 绑定事件监听 语法糖： @
- v-if  : 条件渲染（动态控制节点是否存在）
- v-else  : 条件渲染（动态控制节点是否存在）
- v-show  : 条件渲染（动态控制节点是否展示）
- v-for  : 遍历数组/对象/字符串 
- v-text  : 向所在节点渲染指定文本内容
- v-html  : 向所在节点渲染指定标签内容
- v-cloak  : 向所在节点渲染指定文本内容
- v-once  : 向所在节点渲染指定文本内容
- v-pre  : 向所在节点渲染指定文本内容

```html
    <div id="root">
    <!-- v-text 解析文本-->
    <div v-text="name">你好，</div>

    <!-- v-html 解析标签-->
    <div v-html="aStr"></div>

    <!-- v-cloak 添加爹play：none属性，vue实例接管容器之后会删除此属性-->
    <h3 v-cloak> hello {{name}} </h3>

    <!-- v-once 添加此属性的标签只会在初始动态渲染后，转为为静态属性-->
    <div v-once> number初始值为 {{ number }} </div>
    <div>number值为 {{ number }} </div>
    <button @click="number++">number++</button>

    <!-- v-pre 添加此属性，vue实例解析模板时会跳过解析阶段 一般用于优化-->
    <div v-pre> number值为 {{ number }} </div>
  </div>
  <script type="text/javascript">
    const vm = new Vue({
      el:'#root', 
      data:{
        name: 'Vue',
        number:1,
        aStr: `<a href="javascript:alert('XSS攻击成功');">链接标签</a>`
      }
    })
  </script>
```

#### 2. 自定义指令

局部指令语法

```js
  new Vue({
  el:'#root', 
  // 配置自定义指令 对象写法
  directives: {
    '自定义指令名':{
      bind(element, binding){},// 指令与元素成功绑定时（一上来）调用
      inserted(element, binding){},// 指令所在元素被插入页面时 调用
      update(element, binding){}// 指令所在的模板被重新解析时 调用 
    }
  }
  // 配置自定义指令 语法糖（函数写法），当不需要 指定 inserted 函数 时 。此函数被当作 bind和 update 函数调用
  // directives: {
  //   '自定义指令名':(element,binding) {
  //   }
  // }
  })
```

配置对象 directives 中常用的3个回调：

- bind：指令与元素成功绑定时调用。
- inserted：指令所在元素被插入页面时调用。
- update：指令所在模板结构被重新解析时调用。

全局指令的定义方式：`Vue.directive('指令名',{})` 或者`Vue.directive('指令名',function() {})`
注意：

- 自定义指令名不要采用驼峰命名法，因采用以下的方式`big-number() {}`,调用方式`<div v-bing-number="number"></div>`
- 指令定义时不使用 v- ，使用时需要添加 ***v-***
  理解这三个的调用时机，需要进一步了解 vue 的生命周期。
  实例：

```html
  <div id="root">
    <h2>自定义指令</h2>
    <hr>
    <button @click="number++">n++</button>
    <div v-bing="number"></div>
    <div v-fbnd="number"></div>
  </div>
  <script type="text/javascript">
    const vm = new Vue({
      el:'#root', 
      data:{
        name: 'Vue',
        number:1
      },
      directives:{
        bing:{
          bind(element,binding){
            console.log(element,binding);
            element.innerText = binding.value*100 
          },// 指令所在元素 与 Vue实例绑定时 调用
          inserted(element, binding){
            element.style.background = 'skyblue'
          },// 指令所在元素被插入页面时 调用
          update(element, binding){
            element.innerText = binding.value*100 
          }// 指令所在的模板被重新解析时 调用 
        },
        fbnd(element, binding){
          element.innerText = binding.value
        }
      }
    })
  </script>
```

### 16. Vue生命周期

Vue 实例有⼀个完整的⽣命周期：new Vue()、初始化事件(.once事件)和生命周期、编译模版、挂载Dom -> 渲染、更新 -> 渲染、卸载 等⼀系列过程，称这是Vue的⽣命周期。生命周期函数中的 this 指定 vm 或者组件实例对象
![生命周期模型图](/blogs/_archive-2024-assets/95ec50905cdbaca9b7e5.webp)

1. beforeCreate（创建前）：数据监测(getter和setter)和初始化事件还未开始，此时 data 的响应式追踪、event/watcher 都还没有被设置，也就是说不能访问到data、computed、watch、methods上的方法和数据。
2. created（创建后）：实例创建完成，实例上配置的 options 包括 data、computed、watch、methods 等都配置完成，但是此时渲染得节点还未挂载到 DOM，所以不能访问到 $el属性。
3. beforeMount（挂载前）：在挂载开始之前被调用，相关的render函数首次被调用。此阶段Vue开始解析模板，生成虚拟DOM存在内存中，还没有把虚拟DOM转换成真实DOM，插入页面中。所以网页不能显示解析好的内容。
4. mounted（挂载后,***常用***）：在el被新创建的 vm.$el（就是真实DOM的拷贝）替换，并挂载到实例上去之后调用（将内存中的虚拟DOM转为真实DOM，真实DOM插入页面）。此时页面中呈现的是经过Vue编译的DOM，这时在这个钩子函数中对DOM的操作可以有效，但要尽量避免。一般在这个阶段进行: ***开启定时器，发送网络请求，订阅消息，绑定自定义事件 等***
5. beforeUpdate（更新前）：响应式数据更新时调用，此时虽然响应式数据更新了，但是对应的真实 DOM 还没有被渲染（数据是新的，但页面是旧的，页面和数据没保持同步呢）。
6. updated（更新后） ：在由于数据更改导致的虚拟DOM重新渲染和打补丁之后调用。此时 DOM 已经根据响应式数据的变化更新了。调用时，组件 DOM已经更新，所以可以执行依赖于DOM的操作。然而在大多数情况下，应该避免在此期间更改状态，因为这可能会导致更新无限循环。该钩子在服务器端渲染期间不被调用。
7. beforeDestroy（销毁前,***常用***）：实例销毁之前调用。这一步，实例仍然完全可用，this 仍能获取到实例。在这个阶段一般进行: ***关闭定时器，取消订阅消息，解绑自定义事件 等***。
8. destroyed（销毁后）：实例销毁后调用，调用后，Vue 实例指示的所有东西都会解绑定，所有的事件监听器会被移除，所有的子实例也会被销毁。该钩子在服务端渲染期间不被调用。
